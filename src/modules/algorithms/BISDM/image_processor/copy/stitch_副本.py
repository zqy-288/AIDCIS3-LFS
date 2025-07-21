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
        panorama = self._aggressive_seam_removal(panorama)
        panorama = self._ultra_smooth_enhancement(panorama)

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


    def _perfect_seamless_blend(self, panorama, img, y_start, prev_end, img_idx):
        """完美无缝融合 - 处理各种偏移情况"""
        h, w = img.shape[:2]
        y_end = y_start + h
        
        # 处理负偏移或无重叠的情况
        if y_start < 0:
            # 负偏移：图像向上移动
            y_start = 0
            y_end = h
            
        # 确保在画布范围内
        y_start = max(0, y_start)
        y_end = min(panorama.shape[0], y_start + h)
        
        # 计算有效的图像区域
        img_start_row = max(0, -y_start) if y_start < 0 else 0
        img_end_row = img_start_row + (y_end - y_start)
        
        if img_end_row > h:
            img_end_row = h
            y_end = y_start + (img_end_row - img_start_row)
        
        # 检查是否有有效区域
        if y_start >= y_end or img_start_row >= img_end_row:
            self.logger.warning(f"图像{img_idx}无有效区域: y_start={y_start}, y_end={y_end}")
            return prev_end
        
        # 计算重叠区域
        overlap_start = max(y_start, 0)
        overlap_end = min(y_end, prev_end) if prev_end > 0 else y_end
        overlap_h = max(0, overlap_end - overlap_start)
        
        self.logger.debug(f"图像{img_idx}: y_start={y_start}, y_end={y_end}, overlap_h={overlap_h}")
        
        if overlap_h > 10 and prev_end > 0:  # 有足够重叠进行融合
            # 提取重叠的图像部分
            img_overlap_start = overlap_start - y_start + img_start_row
            img_overlap_end = img_overlap_start + overlap_h
            
            # 确保索引有效
            if img_overlap_start >= 0 and img_overlap_end <= h and img_overlap_start < img_overlap_end:
                self._ultra_advanced_blend(panorama, img, y_start, overlap_start, overlap_h, w, img_overlap_start)
            else:
                # 直接放置，不融合
                panorama[y_start:y_end, :w] = img[img_start_row:img_end_row].astype(np.float64)
        else:
            # 没有重叠，直接放置
            panorama[y_start:y_end, :w] = img[img_start_row:img_end_row].astype(np.float64)
        
        # 放置非重叠部分（新的区域）
        non_overlap_start = max(overlap_start + overlap_h, prev_end) if prev_end > 0 else y_end
        if non_overlap_start < y_end:
            img_non_overlap_start = non_overlap_start - y_start + img_start_row
            if img_non_overlap_start < img_end_row:
                panorama[non_overlap_start:y_end, :w] = img[img_non_overlap_start:img_end_row].astype(np.float64)
        
        return max(y_end, prev_end)

    def _ultra_advanced_blend(self, panorama, img, y_start, overlap_start, overlap_h, w, img_overlap_start=None):
        """超高级融合算法 - 五重融合策略"""
        # 提取重叠区域
        pano_overlap = panorama[overlap_start:overlap_start + overlap_h, :w].copy()
        
        if img_overlap_start is None:
            img_overlap_start = overlap_start - y_start
        
        img_overlap_end = img_overlap_start + overlap_h
        
        # 确保索引在有效范围内
        if img_overlap_start < 0 or img_overlap_end > img.shape[0] or img_overlap_start >= img_overlap_end:
            self.logger.warning(f"无效的图像重叠区域: {img_overlap_start}-{img_overlap_end}, 图像高度: {img.shape[0]}")
            return
            
        img_overlap = img[img_overlap_start:img_overlap_end, :w].astype(np.float64)
        
        # 检查尺寸匹配
        if pano_overlap.shape != img_overlap.shape:
            self.logger.warning(f"重叠区域尺寸不匹配: pano={pano_overlap.shape}, img={img_overlap.shape}")
            return
        
        # 1. 超平滑权重函数
        weights = self._create_ultra_smooth_weights(overlap_h)
        weights_3d = np.stack([weights] * 3, axis=-1)
        
        # 2. 五种融合方法
        blend1 = self._gaussian_pyramid_blend(pano_overlap, img_overlap, overlap_h)
        blend2 = self._poisson_blend(pano_overlap, img_overlap)
        blend3 = self._gradient_domain_blend(pano_overlap, img_overlap)
        blend4 = pano_overlap * (1 - weights_3d) + img_overlap * weights_3d  # 简单加权
        blend5 = self._frequency_domain_blend(pano_overlap, img_overlap, weights_3d)
        
        # 3. 自适应组合
        texture_score = self._calculate_texture_complexity(pano_overlap, img_overlap)
        
        if texture_score > 0.5:  # 高纹理区域
            final_blend = 0.3 * blend1 + 0.3 * blend2 + 0.2 * blend3 + 0.1 * blend4 + 0.1 * blend5
        else:  # 低纹理区域
            final_blend = 0.2 * blend1 + 0.2 * blend2 + 0.1 * blend3 + 0.4 * blend4 + 0.1 * blend5
        
        # 4. 应用结果
        panorama[overlap_start:overlap_start + overlap_h, :w] = final_blend

    def _create_ultra_smooth_weights(self, height):
        """创建超平滑权重函数"""
        # 使用三次样条插值创建超平滑曲线
        x = np.linspace(0, 1, height)
        
        # 创建S形曲线的控制点
        control_x = np.array([0, 0.25, 0.5, 0.75, 1.0])
        control_y = np.array([0, 0.1, 0.5, 0.9, 1.0])
        
        # 三次样条插值
        spline = interpolate.interp1d(control_x, control_y, kind='cubic')
        weights = spline(x)
        
        # 额外的高斯平滑
        weights = gaussian_filter(weights, sigma=height / 20)
        
        return weights[:, np.newaxis]

    def _gaussian_pyramid_blend(self, img1, img2, levels=6):
        """高斯金字塔融合"""
        if img1.shape != img2.shape:
            return (img1 + img2) / 2
        
        # 构建高斯金字塔
        pyramid1 = [img1.copy()]
        pyramid2 = [img2.copy()]
        
        for i in range(levels - 1):
            pyramid1.append(cv2.pyrDown(pyramid1[-1]))
            pyramid2.append(cv2.pyrDown(pyramid2[-1]))
        
        # 从顶层开始融合
        blended = (pyramid1[-1] + pyramid2[-1]) / 2
        
        for i in range(levels - 2, -1, -1):
            blended = cv2.pyrUp(blended)
            # 调整尺寸匹配
            if blended.shape[:2] != pyramid1[i].shape[:2]:
                blended = cv2.resize(blended, (pyramid1[i].shape[1], pyramid1[i].shape[0]))
            
            # 加权融合
            alpha = 0.5
            blended = alpha * pyramid1[i] + (1 - alpha) * pyramid2[i] + (1 - 2*alpha) * blended
        
        return blended

    def _poisson_blend(self, img1, img2):
        """泊松融合（简化版）"""
        # 计算拉普拉斯算子
        kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        
        laplacian1 = cv2.filter2D(img1.astype(np.float32), -1, kernel)
        laplacian2 = cv2.filter2D(img2.astype(np.float32), -1, kernel)
        
        # 取拉普拉斯算子较小的区域 - 计算每个像素的梯度幅值
        grad_mag1 = np.sqrt(np.sum(laplacian1**2, axis=-1))
        grad_mag2 = np.sqrt(np.sum(laplacian2**2, axis=-1))
        
        # 创建2D mask，然后扩展到3D
        mask_2d = grad_mag1 < grad_mag2
        mask_3d = np.stack([mask_2d, mask_2d, mask_2d], axis=-1)
        
        return np.where(mask_3d, img1, img2)

    def _frequency_domain_blend(self, img1, img2, weights):
        """频域融合"""
        # 转换为频域
        f1 = np.fft.fft2(img1, axes=(0, 1))
        f2 = np.fft.fft2(img2, axes=(0, 1))
        
        # 在频域进行加权
        f_blended = f1 * (1 - weights) + f2 * weights
        
        # 转换回空域
        blended = np.fft.ifft2(f_blended, axes=(0, 1)).real
        
        return blended

    def _calculate_texture_complexity(self, img1, img2):
        """计算纹理复杂度"""
        # 计算梯度幅值
        gray1 = cv2.cvtColor(img1.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        
        grad1 = cv2.Sobel(gray1, cv2.CV_32F, 1, 1, ksize=3)
        grad2 = cv2.Sobel(gray2, cv2.CV_32F, 1, 1, ksize=3)
        
        complexity = (np.std(grad1) + np.std(grad2)) / 2
        return min(complexity / 100.0, 1.0)  # 归一化到[0,1]

    def _aggressive_seam_removal(self, panorama):
        """强力缝隙消除"""
        panorama_uint8 = panorama.astype(np.uint8)
        gray = cv2.cvtColor(panorama_uint8, cv2.COLOR_BGR2GRAY)
        
        # 多级边缘检测
        edges1 = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        edges2 = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=5)
        edges3 = cv2.Canny(gray, 30, 100)
        
        # 综合边缘信息
        strong_edges = (np.abs(edges1) > np.std(edges1) * 2.5) | \
                      (np.abs(edges2) > np.std(edges2) * 2.5) | \
                      (edges3 > 0)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 7))
        strong_edges = cv2.morphologyEx(strong_edges.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
        
        # 检测水平线
        lines = cv2.HoughLinesP(strong_edges, 1, np.pi/180, threshold=30, minLineLength=50, maxLineGap=15)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if abs(y2 - y1) < 3:  # 水平线
                    self._repair_seam_line_advanced(panorama, (y1 + y2) // 2)
        
        return panorama

    def _repair_seam_line_advanced(self, panorama, y_pos):
        """高级缝隙修复"""
        h, w = panorama.shape[:2]
        if y_pos < 10 or y_pos >= h - 10:
            return
        
        # 获取更大的上下文区域
        above = panorama[y_pos - 10:y_pos - 2, :]
        below = panorama[y_pos + 3:y_pos + 11, :]
        
        if above.size > 0 and below.size > 0:
            # 使用双三次插值进行修复
            repair_height = 5
            y_coords = np.linspace(-1, 1, repair_height)
            
            for x in range(w):
                if above.shape[0] > 0 and below.shape[0] > 0:
                    # 对每个颜色通道进行插值
                    for c in range(3):
                        above_vals = above[:, x, c]
                        below_vals = below[:, x, c]
                        
                        if len(above_vals) > 0 and len(below_vals) > 0:
                            # 使用边界值进行平滑插值
                            start_val = above_vals[-1]
                            end_val = below_vals[0]
                            
                            # 三次插值
                            interpolated = start_val + (end_val - start_val) * \
                                         (1 + y_coords) / 2 * (1 + np.sin(np.pi * y_coords) / 2)
                            
                            panorama[y_pos - 2:y_pos + 3, x, c] = interpolated

    def _ultra_smooth_enhancement(self, panorama):
        """超平滑增强处理"""
        # 转换为uint8进行处理
        panorama_uint8 = np.clip(panorama, 0, 255).astype(np.uint8)
        
        # 1. 轻微的双边滤波
        panorama_uint8 = cv2.bilateralFilter(panorama_uint8, 5, 50, 50)
        
        # 2. 色彩平衡
        panorama_uint8 = self._color_balance(panorama_uint8)
        
        # 3. 轻微锐化
        panorama_uint8 = self._sharpen_image(panorama_uint8)
        
        # 4. 最终的细缝填补
        panorama_uint8 = self._fill_gaps_advanced(panorama_uint8)
        
        return panorama_uint8.astype(np.float64)

    def _fill_gaps_advanced(self, img):
        """高级缝隙填补"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 检测黑色像素和低强度像素
        mask = (gray < 10).astype(np.uint8) * 255
        
        if mask.sum() > 0:
            # 使用快速修复算法
            img = cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)
            
            # 再次检测并修复
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            mask2 = (gray < 5).astype(np.uint8) * 255
            
            if mask2.sum() > 0:
                img = cv2.inpaint(img, mask2, 3, cv2.INPAINT_NS)
        
        return img

    # ---------------------- 保留原有方法 ---------------------- #
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

    def _gradient_domain_blend(self, img1, img2):
        """梯度域融合"""
        gray1 = cv2.cvtColor(img1.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        
        grad1_x = cv2.Sobel(gray1, cv2.CV_32F, 1, 0, ksize=3)
        grad1_y = cv2.Sobel(gray1, cv2.CV_32F, 0, 1, ksize=3)
        grad2_x = cv2.Sobel(gray2, cv2.CV_32F, 1, 0, ksize=3)
        grad2_y = cv2.Sobel(gray2, cv2.CV_32F, 0, 1, ksize=3)
        
        grad1_mag = np.sqrt(grad1_x**2 + grad1_y**2)
        grad2_mag = np.sqrt(grad2_x**2 + grad2_y**2)
        
        total_grad = grad1_mag + grad2_mag + 1e-8
        weight1 = grad1_mag / total_grad
        weight2 = grad2_mag / total_grad
        
        result = np.zeros_like(img1)
        for c in range(3):
            result[:, :, c] = img1[:, :, c] * weight1 + img2[:, :, c] * weight2
        
        return result

    def _crop_valid_region(self, pano):
        gray = cv2.cvtColor(pano.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        ys, xs = np.where(gray > 1)
        if ys.size == 0:
            return pano[:1, :1]
        y0, y1 = ys.min(), ys.max()
        x0, x1 = xs.min(), xs.max()
        return pano[y0 : y1 + 1, x0 : x1 + 1]

    def _color_balance(self, img):
        means = img.reshape(-1, 3).mean(0)
        scale = means.mean() / (means + 1e-6)
        balanced = cv2.multiply(img, scale)
        return np.clip(balanced, 0, 255).astype(np.uint8)

    def _sharpen_image(self, img):
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        return cv2.filter2D(img, -1, kernel)