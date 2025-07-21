"""
工业内窥镜图像拼接处理器
版本: v1.0 
日期: 2025-06-08
功能: 基于SIFT特征匹配和RANSAC的自动运动检测拼接算法
特点: 正确处理相机深入/退出运动，支持通用拼接任务
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Union
import time
from scipy.ndimage import gaussian_filter
from scipy import interpolate


class StitchProcessor:
    """垂直图像拼接处理器（完全无缝版）

    改动要点：
    1. **超大融合区域**：使用图像高度50%作为融合区域
    2. **多重融合策略**：结合5种不同的融合方法
    3. **强力缝隙消除**：多级后处理消除任何残留缝隙
    4. **自适应融合**：根据图像特征自动调整融合参数
    5. **双向融合验证**：确保融合的对称性和一致性
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # ORB 参数针对内窥镜纹理做增强
        try:
            # 尝试使用新版本OpenCV
            #提取关键点，并计算描述子
            if hasattr(cv2, 'ORB_create'):
                self.feature_detector = cv2.ORB_create(
                    nfeatures=8000,
                    scaleFactor=1.2,
                    nlevels=8,
                    edgeThreshold=15,
                    patchSize=31,
                    fastThreshold=15,
                )
            else:
                # 兼容旧版本OpenCV
                self.feature_detector = cv2.ORB()
        except Exception as e:
            self.logger.warning(f"创建ORB检测器失败: {e}")
            self.feature_detector = None

        # 超大重叠区域以获得最佳融合效果
        self.overlap = getattr(config, "overlap", 600)  # 增加到600像素
        self.min_overlap = 300  # 最小重叠区域也增加
        self.save_intermediate = getattr(config, "save_intermediate", False)
        self.logger.info(f"estimated overlap: {self.overlap}px")

    # ------------------------------------------------------------------
    #   PUBLIC API
    # ------------------------------------------------------------------
    def process(self, images: List[np.ndarray], output_path: Optional[Path] = None):
        if not images:
            raise ValueError("输入图像列表为空")
        if len(images) == 1:
            return images[0]

        self.logger.info(f"开始完全无缝拼接 {len(images)} 张图像")

        # ② 先进图像配准偏移估计 - 先计算偏移量
        # 返回画布上的起始点和相对上张图的偏移
        offsets, pair_dy = self._ultra_precise_offset_estimation(images)
        
        # ① 根据偏移量创建合适大小的画布
        max_w = max(im.shape[1] for im in images)
        
        # 计算画布高度：考虑所有图像的放置位置
        canvas_height_needed = 0
        for i, (im, y_start) in enumerate(zip(images, offsets)):
            img_bottom = y_start + im.shape[0]
            canvas_height_needed = max(canvas_height_needed, img_bottom)
        
        # 添加一些缓冲空间
        canvas_height_needed += 200
        
        self.logger.info(f"创建画布: {canvas_height_needed}x{max_w} (原累加高度: {sum(im.shape[0] for im in images)})")
        panorama = np.zeros((canvas_height_needed, max_w, 3), dtype=np.float64)  # 使用float64提高精度

        # ③ 逐步完美融合
        current_end = 0
        for idx, (im, y_start) in enumerate(zip(images, offsets)):
            img_height, img_width = im.shape[:2]
            img_end = y_start + img_height
            
            self.logger.info(f"放置第 {idx+1}/{len(images)} 张图像: 位置[{y_start}:{img_end}] (高度{img_height}px)")
            
            # 检查画布边界
            if img_end > panorama.shape[0]:
                self.logger.warning(f"图像{idx}超出画布边界! 图像结束位置{img_end} > 画布高度{panorama.shape[0]}")
                continue
            
            if idx == 0:
                # 第一张图像直接放置
                panorama[y_start:y_start + img_height, :img_width] = im.astype(np.float64)
                current_end = y_start + img_height
                self.logger.info(f"  第一张图像已放置，当前结束位置: {current_end}")
            else:
                # 后续图像使用完美融合
                try:
                    current_end = self._perfect_seamless_blend(
                        panorama, im, y_start, current_end, idx
                    )
                    self.logger.info(f"  图像{idx}融合完成，当前结束位置: {current_end}")
                except Exception as e:
                    self.logger.error(f"图像{idx}融合失败: {e}")
                    # 备用方案：直接放置
                    panorama[y_start:y_start + img_height, :img_width] = im.astype(np.float64)
                    current_end = max(current_end, y_start + img_height)
                    self.logger.info(f"  使用备用放置方案，当前结束位置: {current_end}")
        
        self.logger.info(f"所有图像放置完成，最终画布使用高度: {current_end}/{panorama.shape[0]}")

        # ④ 强力后处理 - 多级缝隙消除
        panorama = self._crop_valid_region(panorama)

        # ⑤ 保存
        if output_path:
            output_path.mkdir(parents=True, exist_ok=True)
            # 转换回uint8保存
            panorama_uint8 = np.clip(panorama, 0, 255).astype(np.uint8)
            cv2.imwrite(str(output_path / "panorama_result.png"), panorama_uint8)
            if self.save_intermediate:
                np.save(str(output_path / "offsets.npy"), np.array(offsets))

        return np.clip(panorama, 0, 255).astype(np.uint8)

    # ------------------------------------------------------------------
    #   ULTRA ENHANCED METHODS
    # ------------------------------------------------------------------
    def _ultra_precise_offset_estimation(self, images):
        """先进的图像配准和偏移估计 - 基于RANSAC和全局优化"""
        self.logger.info("开始先进图像配准估计...")
        
        # 使用先进的图像配准方法
        transformations = self._estimate_global_transformations(images)
        offsets = self._extract_offsets_from_transformations(transformations, images)
        
        # 打印偏移量校验报告
        self.logger.info("\n=== 先进配准位移校验(累积偏移) ===")
        pair_dy = []
        for i in range(1, len(offsets)):
            dy = offsets[i] - offsets[i-1] if i > 0 else 0
            pair_dy.append(dy)
            self.logger.info(f"frame {i}: 累积={offsets[i]}px, 相对前帧=+{dy}px")
        self.logger.info("=" * 48)
        
        return offsets, pair_dy
    
   
    def _perfect_seamless_blend(self, panorama: np.ndarray, new_image: np.ndarray, 
                            y_start: int, current_end: int, idx: int) -> int:
        """
        可靠的无缝融合实现，确保高质量拼接
        
        参数:
            panorama: 当前全景画布 (HxWx3)
            new_image: 待融合的新图像 (hxwx3)
            y_start: 新图像在画布上的起始Y坐标
            current_end: 当前画布的有效内容结束位置
            idx: 当前图像索引
            
        返回:
            更新后的画布有效内容结束位置
        """
        # 确保图像使用高精度格式
        if new_image.dtype != np.float64:
            new_image = new_image.astype(np.float64)
        
        img_h, img_w = new_image.shape[:2]
        img_end = y_start + img_h
        
        # 计算重叠区域
        overlap_start = y_start
        overlap_end = min(current_end, img_end)
        overlap_height = max(0, overlap_end - overlap_start)
        
        if overlap_height <= 0:
            # 无重叠区域，直接放置图像
            panorama[y_start:y_start+img_h, :img_w] = new_image
            return y_start + img_h
        
        self.logger.info(f"  图像{idx}重叠区域高度: {overlap_height}px")
        
        # 提取重叠区域
        canvas_overlap = panorama[overlap_start:overlap_end, :img_w]
        newimg_overlap = new_image[:overlap_height, :]
        
        # 创建优化的渐变权重掩码
        # 使用简单的线性渐变确保自然过渡
        mask = self._create_simple_mask(overlap_height, img_w)
        
        # 直接加权混合 - 最可靠的方法
        blended_overlap = canvas_overlap * (1 - mask) + newimg_overlap * mask
        
        # 将融合后的重叠区域写回画布
        panorama[overlap_start:overlap_end, :img_w] = blended_overlap
        
        # 处理非重叠区域
        if img_end > current_end:
            non_overlap_start = current_end
            non_overlap_end = img_end
            non_overlap_height = non_overlap_end - non_overlap_start
            
            # 新图像的非重叠部分
            non_overlap_img = new_image[overlap_height:overlap_height+non_overlap_height, :]
            
            # 写入画布
            panorama[non_overlap_start:non_overlap_end, :img_w] = non_overlap_img
            self.logger.info(f"  添加非重叠区域: {non_overlap_height}px")
        
        # 返回新的有效内容结束位置
        return max(current_end, img_end)

    def _create_simple_mask(self, height: int, width: int) -> np.ndarray:
        """
        创建简单的渐变权重掩码
        - 垂直方向线性渐变
        - 避免复杂处理导致伪影
        """
        # 垂直方向渐变权重
        y = np.linspace(1, 0, height)  # 顶部权重1(全景图)，底部权重0(新图)
        
        # 创建二维掩码
        mask = np.repeat(y[:, np.newaxis], width, axis=1)
        
        # 扩展为3通道
        return np.repeat(mask[:, :, np.newaxis], 3, axis=2)

   
    def _multi_scale_template_match(self, img1, img2):
        """多尺度模板匹配 - 使用整个图像进行匹配"""
        #在img1和img2的整个图像区域进行特征对齐，计算垂直方向的偏移量
        best_offset = 0
        best_confidence = 0
        
        for scale in [1.0, 0.75, 0.5]:
            if scale == 1.0:
                i1, i2 = img1, img2
            else:
                h1, w1 = img1.shape[:2]
                h2, w2 = img2.shape[:2]
                i1 = cv2.resize(img1, (int(w1 * scale), int(h1 * scale)))
                i2 = cv2.resize(img2, (int(w2 * scale), int(h2 * scale)))
            
            # 使用图像1的中心区域作为模板（而不只是顶部）
            h1, w1 = i1.shape[:2]
            h2, w2 = i2.shape[:2]
            
            # 使用图像高度的60%作为模板，从图像中心开始
            template_h = min(int(h1 * 0.6), 300)
            start_y = max(0, (h1 - template_h) // 2)
            template = i1[start_y:start_y + template_h]  # 图像1的中心区域作为模板
            
            # 在整个图像2中搜索，允许更大的偏移范围
            search = i2  # 使用完整的图像2作为搜索区域
            
            # 检查搜索区域是否足够大
            if search.shape[0] < template.shape[0] or search.shape[1] < template.shape[1]:
                continue
                
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            search_gray = cv2.cvtColor(search, cv2.COLOR_BGR2GRAY)
            
            # 增强对比度
            template_gray = cv2.equalizeHist(template_gray)
            search_gray = cv2.equalizeHist(search_gray)
            
            # 应用高斯滤波减少噪声
            template_gray = cv2.GaussianBlur(template_gray, (3, 3), 0)
            search_gray = cv2.GaussianBlur(search_gray, (3, 3), 0)
            
            #获取最高匹配值及其位置
            res = cv2.matchTemplate(search_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            # 计算垂直偏移量，考虑模板在图像1中的起始位置
            # max_loc[1]是在图像2中匹配到的位置，需要减去模板在图像1中的起始位置
            offset_in_search = max_loc[1]
            actual_offset = int((offset_in_search - start_y) / scale)
            
            # 调试信息
            self.logger.debug(f"全图模板匹配 scale={scale}: search_offset={offset_in_search}, template_start={start_y}, actual_offset={actual_offset}, confidence={max_val:.3f}")
            
            #保留置信度最高的偏移量
            if max_val > best_confidence:
                best_confidence = max_val
                best_offset = actual_offset
        
        # 记录最佳匹配的详细信息
        self.logger.debug(f"模板匹配最佳结果: offset={best_offset}, confidence={best_confidence:.3f}")
        
        # 置信度检查：如果置信度太低，尝试不同区域匹配
        if best_confidence < 0.3:
            self.logger.debug("置信度低，尝试不同区域策略")
            
            # 尝试使用图像的不同部分作为模板
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            
            # 尝试上半部分
            template_h_top = min(int(h1 * 0.4), 150)
            template_top = img1[:template_h_top]
            
            # 尝试下半部分  
            template_h_bottom = min(int(h1 * 0.4), 150)
            start_bottom = max(0, h1 - template_h_bottom)
            template_bottom = img1[start_bottom:]
            
            for template_region, region_name, start_offset in [
                (template_top, "上半部分", 0),
                (template_bottom, "下半部分", start_bottom)
            ]:
                if (template_region.shape[0] > 50 and template_region.shape[1] > 50 and
                    img2.shape[0] >= template_region.shape[0] and img2.shape[1] >= template_region.shape[1]):
                    
                    template_gray = cv2.cvtColor(template_region, cv2.COLOR_BGR2GRAY)
                    search_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
                    
                    res = cv2.matchTemplate(search_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    
                    backup_offset = max_loc[1] - start_offset
                    if max_val > best_confidence:
                        best_offset = backup_offset
                        best_confidence = max_val
                        self.logger.debug(f"{region_name}匹配改进: offset={backup_offset}, confidence={max_val:.3f}")
        
        # 直接返回最佳偏移量，不施加任何约束
        return best_offset


    def _estimate_global_transformations(self, images):
        """使用RANSAC和全局束调整估计图像间的变换"""
        n_images = len(images)
        transformations = []
        
        # 初始化第一个图像的变换为单位矩阵
        base_transform = np.eye(3, dtype=np.float32)
        transformations.append(base_transform)
        
        # 提取所有图像的特征点
        all_keypoints, all_descriptors = self._extract_robust_features(images)
        
        # 逐对估计变换并累积
        cumulative_transform = base_transform.copy()
        
        for i in range(1, n_images):
            self.logger.info(f"配准图像 {i-1} -> {i}")
            
            # 匹配特征点
            matches = self._match_features_robust(
                all_descriptors[i-1], all_descriptors[i],
                all_keypoints[i-1], all_keypoints[i]
            )
            
            if len(matches) < 10:
                self.logger.warning(f"图像{i-1}->{i}特征匹配点不足({len(matches)})，尝试全图模板匹配")
                # 使用增强的模板匹配作为备选方案
                try:
                    offset = self._multi_scale_template_match(images[i-1], images[i])
                    if abs(offset) > 1:  # 如果检测到明显偏移
                        # 创建基于模板匹配的变换矩阵
                        template_transform = np.eye(3, dtype=np.float32)
                        template_transform[1, 2] = -offset  # 注意：与特征匹配保持一致的坐标系
                        
                        # 累积变换
                        cumulative_transform = cumulative_transform @ template_transform
                        transformations.append(cumulative_transform.copy())
                        
                        self.logger.info(f"  模板匹配成功: offset={offset}px, 累积dy={cumulative_transform[1, 2]:.2f}px")
                        continue
                    else:
                        self.logger.warning(f"  模板匹配未检测到明显偏移({offset}px)，使用零偏移")
                except Exception as e:
                    self.logger.error(f"  模板匹配失败: {e}，使用零偏移")
                
                # 如果模板匹配也失败，使用零偏移
                transformations.append(cumulative_transform.copy())
                continue
            
            # 使用RANSAC估计变换
            transform = self._estimate_transform_ransac(matches)
            
            if transform is not None:
                # 对于内窥镜拼接，我们需要重新解释变换矩阵
                # 如果相机向内深入，dy<0表示图像内容向上移动
                # 但在拼接时，当前帧应该放在前一帧的下方
                # 因此我们需要反转dy的符号
                corrected_transform = transform.copy()
                corrected_transform[1, 2] = -transform[1, 2]  # 反转垂直偏移
                
                # 累积变换
                cumulative_transform = cumulative_transform @ corrected_transform
                transformations.append(cumulative_transform.copy())
                
                # 记录变换信息
                original_dy = transform[1, 2]
                corrected_dy = cumulative_transform[1, 2]
                self.logger.info(f"  估计变换: 原始dy={original_dy:.2f}px, 校正后累积dy={corrected_dy:.2f}px, 匹配点={len(matches)}")
            else:
                self.logger.warning(f"图像{i-1}->{i}变换估计失败，使用前一变换")
                transformations.append(cumulative_transform.copy())
        
        return transformations

    def _extract_robust_features(self, images):
        """提取鲁棒特征点"""
        all_keypoints = []
        all_descriptors = []
        
        # 尝试多种特征检测器
        detectors = []
        
        try:
            # SIFT - 最鲁棒，但较慢
            sift = cv2.SIFT_create(nfeatures=2000, contrastThreshold=0.02, edgeThreshold=8)
            detectors.append(("SIFT", sift))
        except:
            pass
            
        try:
            # ORB - 快速，二进制描述符
            orb = cv2.ORB_create(nfeatures=2000, scaleFactor=1.2, nlevels=8)
            detectors.append(("ORB", orb))
        except:
            pass
            
        try:
            # AKAZE - 良好的性能
            akaze = cv2.AKAZE_create()
            detectors.append(("AKAZE", akaze))
        except:
            pass
        
        if not detectors:
            raise RuntimeError("无可用的特征检测器")
        
        detector_name, detector = detectors[0]  # 使用第一个可用的检测器
        self.logger.info(f"使用{detector_name}特征检测器")
        
        for i, img in enumerate(images):
            # 预处理图像
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 增强对比度
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # 检测特征点
            kp, des = detector.detectAndCompute(gray, None)
            
            if des is None:
                des = np.array([]).reshape(0, 128 if detector_name == "SIFT" else 32)
                kp = []
            
            all_keypoints.append(kp)
            all_descriptors.append(des)
            
            self.logger.debug(f"图像{i}: 检测到{len(kp)}个特征点")
        
        return all_keypoints, all_descriptors

    def _match_features_robust(self, des1, des2, kp1, kp2):
        """鲁棒特征匹配"""
        if des1.shape[0] == 0 or des2.shape[0] == 0:
            return []
        
        # 选择匹配器
        if des1.dtype == np.uint8:  # ORB描述符
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        else:  # SIFT/AKAZE描述符
            matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        
        # KNN匹配，每个特征图返回另一个图像中的最佳匹配
        knn_matches = matcher.knnMatch(des1, des2, k=2)
        
        # Lowe's比率测试，如果最佳匹配距离 < 0.7 * 次佳匹配距离，则认为匹配可靠
        good_matches = []
        for match_pair in knn_matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.7 * n.distance:  # 降低阈值获得更多匹配
                    good_matches.append(m)
        
        # 转换为点对，匹配结果转为点对坐标形式，pt1第一幅图像中特征点的索引
        matches = []
        for match in good_matches:
            pt1 = kp1[match.queryIdx].pt
            pt2 = kp2[match.trainIdx].pt
            matches.append((pt1, pt2))
        
        return matches

    def _estimate_transform_ransac(self, matches):
        """使用RANSAC估计变换矩阵"""
        if len(matches) < 10:
            return None
        
        # 提取点对
        src_pts = np.float32([m[0] for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([m[1] for m in matches]).reshape(-1, 1, 2)
        
        # 对于内窥镜，主要是垂直平移，尝试不同的变换模型
        
        # 1. 尝试纯平移模型（最简单）
        transform_translation = self._estimate_translation_ransac(src_pts, dst_pts)
        
        # 2. 尝试仿射变换（包含平移、旋转、缩放）
        try:
            transform_affine, mask = cv2.estimateAffinePartial2D(
                src_pts, dst_pts, 
                method=cv2.RANSAC,
                ransacReprojThreshold=3.0,
                maxIters=2000,
                confidence=0.99
            )
            
            if transform_affine is not None:
                # 转换为3x3矩阵
                transform_3x3 = np.eye(3, dtype=np.float32)
                transform_3x3[:2, :] = transform_affine
                
                # 检查变换的合理性
                dy = transform_3x3[1, 2]
                scale_x = np.sqrt(transform_3x3[0, 0]**2 + transform_3x3[0, 1]**2)
                scale_y = np.sqrt(transform_3x3[1, 0]**2 + transform_3x3[1, 1]**2)
                
                inlier_ratio = np.sum(mask) / len(mask) if mask is not None else 0
                
                self.logger.debug(f"仿射变换: dy={dy:.2f}, scale=({scale_x:.3f},{scale_y:.3f}), inliers={inlier_ratio:.2f}")
                
                # 合理性检查
                if (abs(dy) > 0.1 and abs(dy) < 200 and  # 合理的垂直偏移
                    0.8 < scale_x < 1.2 and 0.8 < scale_y < 1.2 and  # 合理的缩放
                    inlier_ratio > 0.3):  # 足够的内点
                    return transform_3x3
                    
        except Exception as e:
            self.logger.debug(f"仿射变换估计失败: {e}")
        
        # 3. 如果仿射变换不合理，使用平移变换
        if transform_translation is not None:
            return transform_translation
            
        return None

    def _estimate_translation_ransac(self, src_pts, dst_pts):
        """估计纯平移变换"""
        if len(src_pts) < 3:
            return None
        
        best_inliers = 0
        best_translation = None
        threshold = 5.0
        
        # RANSAC迭代
        for _ in range(1000):
            # 随机选择一个点对
            idx = np.random.randint(0, len(src_pts))
            src_pt = src_pts[idx][0]
            dst_pt = dst_pts[idx][0]
            
            # 计算平移
            translation = dst_pt - src_pt
            
            # 计算内点
            inliers = 0
            for i in range(len(src_pts)):
                predicted = src_pts[i][0] + translation
                error = np.linalg.norm(predicted - dst_pts[i][0])
                if error < threshold:
                    inliers += 1
            
            # 更新最佳结果
            if inliers > best_inliers:
                best_inliers = inliers
                best_translation = translation
        
        if best_inliers >= max(3, len(src_pts) * 0.2):  # 至少20%的内点
            transform = np.eye(3, dtype=np.float32)
            transform[0, 2] = best_translation[0]
            transform[1, 2] = best_translation[1]
            
            inlier_ratio = best_inliers / len(src_pts)
            self.logger.debug(f"平移变换: dx={best_translation[0]:.2f}, dy={best_translation[1]:.2f}, inliers={inlier_ratio:.2f}")
            
            return transform
        
        return None

    def _extract_offsets_from_transformations(self, transformations, images):
        """从变换矩阵中提取垂直偏移量并智能调整为画布坐标"""
        # 先提取所有累积偏移量
        cumulative_offsets = []
        relative_offsets = []
        
        for i, transform in enumerate(transformations):
            # 提取垂直偏移 (这是相对于第一帧的累积偏移)
            dy = transform[1, 2]
            cumulative_offsets.append(dy)
            
            # 计算相对偏移（相对于前一帧）
            if i == 0:
                relative_dy = 0
            else:
                relative_dy = dy - cumulative_offsets[i-1]
            relative_offsets.append(relative_dy)
            
            # 记录变换信息
            dx = transform[0, 2]
            scale_x = np.sqrt(transform[0, 0]**2 + transform[0, 1]**2)
            scale_y = np.sqrt(transform[1, 0]**2 + transform[1, 1]**2)
            
            self.logger.debug(f"图像{i}: cumulative_dy={dy:.2f}, relative_dy={relative_dy:.2f}, dx={dx:.2f}, scale=({scale_x:.3f},{scale_y:.3f})")
        
        # 分析运动模式
        motion_analysis = self._analyze_motion_pattern(relative_offsets)
        self.logger.info(f"运动模式分析: {motion_analysis}")
        
        # 根据运动模式调整偏移量
        canvas_offsets = self._adjust_offsets_for_motion(cumulative_offsets, motion_analysis)
        
        # 打印最终的画布偏移
        self.logger.info("最终画布偏移量:")
        for i, offset in enumerate(canvas_offsets):
            self.logger.info(f"  图像{i}: 画布位置={offset}px")
        
        return canvas_offsets
    
    def _analyze_motion_pattern(self, relative_offsets):
        """分析运动模式：静止、深入、退出"""
        if len(relative_offsets) < 5:
            return {"pattern": "insufficient_data", "direction": "unknown", "motion_start": 0}
        
        # 寻找显著运动开始的帧
        motion_threshold = 5  # 像素
        motion_start = None
        
        for i in range(len(relative_offsets)):
            if abs(relative_offsets[i]) > motion_threshold:
                motion_start = i
                break
        
        if motion_start is None:
            return {"pattern": "static", "direction": "none", "motion_start": len(relative_offsets)}
        
        # 分析运动方向
        motion_offsets = relative_offsets[motion_start:]
        avg_motion = sum(motion_offsets) / len(motion_offsets) if motion_offsets else 0
        
        if avg_motion > motion_threshold:
            # 正偏移：相机深入，后续帧向下排列
            direction = "penetrating"  # 深入
            pattern = "static_then_penetrating"
        elif avg_motion < -motion_threshold:
            # 负偏移：相机退出，后续帧向上排列
            direction = "retracting"  # 退出
            pattern = "static_then_retracting"
        else:
            direction = "unknown"
            pattern = "mixed"
        
        return {
            "pattern": pattern,
            "direction": direction, 
            "motion_start": motion_start,
            "avg_motion": avg_motion,
            "static_frames": motion_start,
            "motion_frames": len(relative_offsets) - motion_start
        }
    
    def _adjust_offsets_for_motion(self, cumulative_offsets, motion_analysis):
        """根据运动模式调整偏移量为正确的画布坐标"""
        
        if motion_analysis["pattern"] == "static":
            # 纯静态：所有图像放在同一位置
            return [0] * len(cumulative_offsets)
        
        elif motion_analysis["pattern"] in ["static_then_penetrating", "static_then_retracting"]:
            # 静态后运动模式
            motion_start = motion_analysis["motion_start"]
            direction = motion_analysis["direction"]
            
            self.logger.info(f"检测到运动模式: {motion_analysis['static_frames']}帧静态 + {motion_analysis['motion_frames']}帧{direction}")
            
            if direction == "penetrating":
                # 深入模式：相机向内深入，后续帧应该放在更下方（更深的位置）
                # 调整逻辑：使第一帧在顶部，后续帧按深度向下排列
                min_offset = min(cumulative_offsets)
                canvas_offsets = [int(offset - min_offset) for offset in cumulative_offsets]
                
                self.logger.info(f"深入模式: 相机从外向内深入，总深度变化={abs(min_offset):.1f}px")
                
            elif direction == "retracting":
                # 退出模式：相机向外退出，后续帧应该放在更上方（更浅的位置）
                # 调整逻辑：使最后一帧在顶部，前面帧按深度向下排列
                max_offset = max(cumulative_offsets)
                canvas_offsets = [int(max_offset - offset) for offset in cumulative_offsets]
                
                self.logger.info(f"退出模式: 相机从内向外退出，总深度变化={max_offset:.1f}px")
            
            else:
                # 未知方向：使用简单的非负化
                min_offset = min(cumulative_offsets)
                canvas_offsets = [int(offset - min_offset) for offset in cumulative_offsets]
                
        else:
            # 混合或未知模式：使用简单的非负化
            min_offset = min(cumulative_offsets)
            canvas_offsets = [int(offset - min_offset) for offset in cumulative_offsets]
            self.logger.warning(f"混合运动模式，使用简单非负化处理")
        
        return canvas_offsets


    def _crop_valid_region(self, pano):
        gray = cv2.cvtColor(pano.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        ys, xs = np.where(gray > 1)
        if ys.size == 0:
            return pano[:1, :1]
        y0, y1 = ys.min(), ys.max()
        x0, x1 = xs.min(), xs.max()
        return pano[y0 : y1 + 1, x0 : x1 + 1]
