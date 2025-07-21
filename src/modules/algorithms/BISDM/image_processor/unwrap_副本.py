from tkinter.constants import W
import cv2
import numpy as np
import math
from pathlib import Path
import logging
from utils.config import Config
import os

class UnwrapProcessor:
    """图像展开处理器 - 使用内窥镜轴心检测和双线性插值极坐标展平"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 轴心检测缓存
        self.axis_center_cache = None
        self.detection_confidence = 0.0
        
    def process(self, images: list, output_path = None) -> list:
        """处理图像序列，进行内窥镜圆环展平
        
        Args:
            images: 输入图像列表
            output_path: 可选的输出路径
            
        Returns:
            展开后的图像列表
        """
        processed_images = []
        interest_region_dir = ""
        if output_path is not None:
            interest_region_dir = str(output_path / "00_interest")
            # 确保感兴趣区域目录存在
            Path(interest_region_dir).mkdir(exist_ok=True)
            self.logger.info(f"感兴趣区域保存目录: {interest_region_dir}")
        else:
            # 如果没有指定输出路径，使用默认目录
            interest_region_dir = "output_interest_regions"
            Path(interest_region_dir).mkdir(exist_ok=True)
            self.logger.warning(f"未指定输出路径，使用默认目录: {interest_region_dir}")
            
        self.logger.info(f"开始处理 {len(images)} 张图像的展平处理")
        
        for i, img in enumerate(images):
            self.logger.info(f"开始处理第{i+1}/{len(images)}帧的内窥镜图像展平")
            
            # 检测轴心（只对第一帧或检测质量不佳时重新检测）
            if self.axis_center_cache is None or self.detection_confidence < 0.5:
                self.logger.info(f"检测第{i}帧的内窥镜轴心...")
                axis_center = self.detect_endoscope_axis_center(img)
                if axis_center is not None:
                    self.axis_center_cache = axis_center
                    self.logger.info(f"轴心检测成功: ({axis_center[0]}, {axis_center[1]})")
                else:
                    # 使用图像中心作为备用
                    h, w = img.shape[:2]
                    self.axis_center_cache = (w // 2, h // 2)
                    self.logger.warning(f"轴心检测失败，使用图像中心: {self.axis_center_cache}")
            
            # 进行圆环展平
            unwrapped_img = self.flatten_endoscope_image(
                img, self.axis_center_cache,
                save_interest_region=True,
                img_id=f"{i:04d}",
                interest_region_dir=interest_region_dir
            )
            processed_images.append(unwrapped_img)
            
            # 保存中间结果（如果需要）
            if self.config.save_intermediate and output_path:
                intermediate_dir = output_path / "02_unwrapped"
                intermediate_dir.mkdir(exist_ok=True)
                
                # 保存展平图像
                unwrap_path = intermediate_dir / f"unwrapped_{i:04d}.png"
                cv2.imwrite(str(unwrap_path), unwrapped_img)
                
            self.logger.info(f"第{i+1}/{len(images)}帧图像展平完成，输出尺寸: {unwrapped_img.shape}")
            
        self.logger.info(f"所有图像展平处理完成，共处理 {len(processed_images)} 张图像")
        return processed_images
    
    def detect_endoscope_axis_center(self, img):
        """
        内窥镜圆孔轴中心点检测
        """
        # 转为灰度图并预处理
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 使用温和的对比度增强
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
        img_enhanced = clahe.apply(img_gray)
        
        # 轻微的高斯模糊减少噪声
        img_processed = cv2.GaussianBlur(img_enhanced, (3, 3), 1.0)
        
        # 使用精确的圆检测策略
        all_circles = self.detect_circles_precisely(img_processed, img.shape)
        
        if all_circles is None or len(all_circles) == 0:
            self.logger.warning("未检测到圆形，使用图像中心作为轴心")
            h, w = img.shape[:2]
            self.detection_confidence = 0.0
            return (w // 2, h // 2)
        
        self.logger.info(f"初始检测到 {len(all_circles)} 个圆形")
        
        # 严格的圆形质量评估和筛选
        valid_circles = self.filter_high_quality_circles(img_gray, all_circles, img.shape)
        
        if len(valid_circles) > 0:
            # 计算轴中心
            axis_center = self.calculate_robust_axis_center(valid_circles, img.shape)
            self.detection_confidence = self.calculate_detection_confidence(valid_circles, img.shape)
            self.logger.info(f"使用 {len(valid_circles)} 个高质量圆形")
            self.logger.info(f"确定的轴心位置: ({axis_center[0]:.1f}, {axis_center[1]:.1f})")
            self.logger.info(f"检测置信度: {self.detection_confidence:.3f}")
            return axis_center
        else:
            self.logger.warning("筛选后无有效圆形，使用图像中心")
            h, w = img.shape[:2]
            self.detection_confidence = 0.0
            return (w // 2, h // 2)

    def detect_circles_precisely(self, img_processed, img_shape):
        """
        使用精确和严格的圆检测策略
        """
        h, w = img_shape[:2]
        img_size = min(h, w)
        all_circles = []
        
        # 策略1: 检测主要的大圆（内窥镜主体），100表示两个圆心间的距离，p2越小检测的圆越多
        circles_large = cv2.HoughCircles(
        img_processed, cv2.HOUGH_GRADIENT, 1, 100,
        param1=180, param2=80,
        minRadius=int(img_size * 0.15), 
        maxRadius=int(img_size * 0.35)
        )
        if circles_large is not None:
            all_circles.extend(circles_large[0])
            self.logger.info(f"大圆检测: {len(circles_large[0])} 个")
        
        # 策略2: 检测中等圆（管道结构）
        circles_medium = cv2.HoughCircles(
            img_processed, cv2.HOUGH_GRADIENT, 1, 80,
            param1=160, param2=70,
            minRadius=int(img_size * 0.08), 
            maxRadius=int(img_size * 0.20)
        )
        if circles_medium is not None:
            all_circles.extend(circles_medium[0])
            self.logger.debug(f"中等圆检测: {len(circles_medium[0])} 个")
        
        # 策略3: 检测内部小圆（只在中心区域），检测到的中心坐标转换到原坐标
        center_crop = img_processed[h//4:3*h//4, w//4:3*w//4]
        circles_small = cv2.HoughCircles(
            center_crop, cv2.HOUGH_GRADIENT, 1, 30,
            param1=140, param2=50,
            minRadius=int(img_size * 0.03), 
            maxRadius=int(img_size * 0.12)
        )
        if circles_small is not None:
            # 调整坐标到原图像
            adjusted_circles = []
            for circle in circles_small[0]:
                adj_x = circle[0] + w//4
                adj_y = circle[1] + h//4
                adjusted_circles.append([adj_x, adj_y, circle[2]])
            all_circles.extend(adjusted_circles)
            self.logger.debug(f"小圆检测: {len(adjusted_circles)} 个")
        
        return np.array(all_circles) if all_circles else None

    def filter_high_quality_circles(self, img_gray, circles, img_shape):
        """
        使用严格的质量评估筛选高质量圆形
        """
        if len(circles) == 0:
            return circles
        
        h, w = img_shape[:2]
        img_center = np.array([w // 2, h // 2])
        
        quality_circles = []
        
        for circle in circles:
            cx, cy, radius = circle[0], circle[1], circle[2]
            
            # 质量评估指标
            score = 0
            
            # 1. 位置评估：距离图像中心的程度
            distance_to_center = np.linalg.norm([cx - img_center[0], cy - img_center[1]])
            max_acceptable_distance = min(w, h) // 4
            
            if distance_to_center > max_acceptable_distance:
                continue
            
            position_score = max(0, 1.0 - distance_to_center / max_acceptable_distance)
            score += position_score * 0.4
            
            # 2. 边界检查：确保圆完全在图像内
            if (cx - radius < 5 or cx + radius >= w - 5 or 
                cy - radius < 5 or cy + radius >= h - 5):
                continue
            
            # 3. 半径合理性评估
            reasonable_min = int(min(w, h) * 0.02)
            reasonable_max = int(min(w, h) * 0.4)
            
            if reasonable_min <= radius <= reasonable_max:
                optimal_radius = (reasonable_min + reasonable_max) // 2
                radius_score = max(0, 1.0 - abs(radius - optimal_radius) / optimal_radius)
                score += radius_score * 0.3
            else:
                continue
            
            # 4. 边缘强度评估
            edge_score = self.evaluate_circle_edge_quality(img_gray, int(cx), int(cy), int(radius))
            score += edge_score * 0.3
            
            # 只保留评分较高的圆
            if score > 0.4:
                quality_circles.append([cx, cy, radius, score])
        
        if not quality_circles:
            return np.array([])
        
        # 按评分排序，选择最好的圆
        quality_circles = sorted(quality_circles, key=lambda x: x[3], reverse=True)
        
        # 最多保留前20个最好的圆
        max_circles = min(20, len(quality_circles))
        selected_circles = np.array(quality_circles[:max_circles])[:, :3]
        
        self.logger.debug(f"质量筛选: {len(circles)} -> {len(selected_circles)} 个高质量圆形")
        
        return selected_circles

    def evaluate_circle_edge_quality(self, img_gray, cx, cy, radius):
        """
        评估圆形边缘的质量
        """
        try:
            # 创建圆形mask
            mask = np.zeros_like(img_gray)
            cv2.circle(mask, (cx, cy), radius, (255,), 2)
            
            # 计算边缘
            edges = cv2.Canny(img_gray, 100, 200)
            
            # 计算圆周上的边缘像素
            circle_edges = cv2.bitwise_and(edges, mask)
            edge_pixels = np.sum(circle_edges > 0)
            
            # 计算理论圆周长
            circumference = 2 * np.pi * radius
            
            # 边缘完整性评分
            edge_ratio = edge_pixels / circumference
            
            return min(edge_ratio * 3, 1.0)  # 归一化到0-1
        except:
            return 0.0

    def calculate_robust_axis_center(self, circles, img_shape):
        """
        在图像中心下方的点中，选择距离图像中心最近的点作为内窥镜内壁圆心
        """
        if len(circles) == 0:
            h, w = img_shape[:2]
            return (w // 2, h // 2)
        
        # 获取图像中心点
        h, w = img_shape[:2]
        img_center = np.array([w // 2, h // 2])
        
        # 筛选出位于图像中心下方的圆心点（y坐标大于图像中心y坐标）
        centers = circles[:, :2]
        radii = circles[:, 2]
        
        # 找出下方的点
        below_center_mask = centers[:, 1] > img_center[1]
        below_centers = centers[below_center_mask]
        below_radii = radii[below_center_mask]
        
        if len(below_centers) == 0:
            # 如果下方没有点，回退到选择所有点中最近的
            distances_to_img_center = np.linalg.norm(centers - img_center, axis=1)
            closest_index = np.argmin(distances_to_img_center)
            closest_center = centers[closest_index]
        else:
            # 计算下方圆心到图像中心的距离
            distances_to_img_center = np.linalg.norm(below_centers - img_center, axis=1)
            
            # 选择距离图像中心最近的下方圆心
            closest_index = np.argmin(distances_to_img_center)
            closest_center = below_centers[closest_index]
        
        return tuple(closest_center.astype(int))

    def calculate_detection_confidence(self, circles, img_shape):
        """
        计算轴心检测的置信度
        """
        if len(circles) == 0:
            return 0.0
        
        h, w = img_shape[:2]
        img_center = np.array([w // 2, h // 2])
        centers = circles[:, :2]
        
        # 基于圆心聚集度计算置信度
        if len(circles) > 1:
            distances = np.linalg.norm(centers - centers.mean(axis=0), axis=1)
            consistency = 1.0 / (1.0 + distances.std() / 25)
        else:
            consistency = 0.5
        
        # 基于圆形数量的置信度
        count_confidence = min(len(circles) / 5.0, 1.0)
        
        # 综合置信度
        confidence = (consistency * 0.7 + count_confidence * 0.3)
        return confidence

    def flatten_endoscope_image(self, img, axis_center, save_interest_region: bool = True, img_id: str = "", interest_region_dir: str = ""):
        """
        基于检测到的轴心对内窥镜图像进行圆环展平
        使用双线性插值算法，保持彩色图像格式
        展平后进行逆时针旋转180度
        新增：在原图上画出展平用的内外圆，并保存到interest_region_dir（如未指定则为output_interest_regions）
        """
        import os
        h, w = img.shape[:2]
        
        # 计算外环半径：圆心到图像边界的最小距离
        C_x, C_y = axis_center[0], axis_center[1]
        distance_to_top = C_y
        distance_to_bottom = h - C_y
        distance_to_left = C_x
        distance_to_right = w - C_x
        
        # 选择最小距离作为外环半径，确保圆环完全在图像内
        outer_radius = int(min(distance_to_top, distance_to_bottom, distance_to_left, distance_to_right))
        inner_radius = int(outer_radius / 2)  # 内环半径为外环的1/10
        
        # 使用配置参数调整半径
        # if hasattr(self.config, 'unwrap_outer_radius_ratio'):
        #     outer_radius = int(outer_radius * self.config.unwrap_outer_radius_ratio)
        # if hasattr(self.config, 'unwrap_inner_radius_ratio'):
        #     inner_radius = int(outer_radius * self.config.unwrap_inner_radius_ratio)
        
        self.logger.debug(f"展平参数: 轴心({C_x}, {C_y}), 外环半径: {outer_radius}, 内环半径: {inner_radius}")
        
        # ----------- 新增：在原图上画出内外圆并保存 -----------
        if save_interest_region:
            try:
                img_marked = img.copy()
                # 画外圆（绿色）
                cv2.circle(img_marked, (int(C_x), int(C_y)), outer_radius, (0,255,0), 2)
                # 画内圆（红色）
                cv2.circle(img_marked, (int(C_x), int(C_y)), inner_radius, (0,0,255), 2)
                
                # 保存目录处理
                if interest_region_dir and interest_region_dir.strip():
                    save_dir = interest_region_dir
                else:
                    save_dir = "output_interest_regions"
                    self.logger.warning(f"未指定感兴趣区域目录，使用默认目录: {save_dir}")
                
                # 确保目录存在
                os.makedirs(save_dir, exist_ok=True)
                
                # 生成文件名
                if img_id and isinstance(img_id, str) and img_id.strip():
                    filename = f"interest_region_{img_id}.png"
                else:
                    import time
                    timestamp = str(int(time.time() * 1000))
                    filename = f"interest_region_{timestamp}.png"
                    self.logger.warning(f"未提供有效的img_id，使用时间戳: {timestamp}")
                
                save_path = os.path.join(save_dir, filename)
                
                # 保存图像
                success = cv2.imwrite(save_path, img_marked)
                if success:
                    self.logger.info(f"感兴趣区域已保存: {save_path}")
                    # 验证文件是否真的保存成功
                    if os.path.exists(save_path):
                        file_size = os.path.getsize(save_path)
                        self.logger.debug(f"保存成功，文件大小: {file_size} bytes")
                    else:
                        self.logger.error(f"文件保存失败，路径不存在: {save_path}")
                else:
                    self.logger.error(f"cv2.imwrite失败，无法保存到: {save_path}")
                    
            except Exception as e:
                self.logger.error(f"保存感兴趣区域图像时发生错误: {str(e)}")
                self.logger.error(f"错误详情 - 保存目录: {save_dir}, 文件名: {filename if 'filename' in locals() else 'Unknown'}")
        # ----------- END -----------
        
        # 使用双线性插值的展平算法，保持彩色图像
        if len(img.shape) == 3:
            # 彩色图像，分别处理每个通道
            flattened_img = self.flatten_ring_area_bilinear_color(img, C_x, C_y, outer_radius, inner_radius)
        else:
            # 灰度图像
            flattened_img = self.flatten_ring_area_bilinear(img, C_x, C_y, outer_radius, inner_radius)
            # 将灰度图转换为3通道以保持一致性
            if flattened_img is not None and len(flattened_img.shape) == 2:
                flattened_img = cv2.cvtColor(flattened_img, cv2.COLOR_GRAY2BGR)
        
        # 展平后进行逆时针旋转180度
        rotated_img = cv2.rotate(flattened_img, cv2.ROTATE_180)
        self.logger.debug(f"展平图像已逆时针旋转180度")

        # target_height = 400  # 保留原始高度的80%
        # target_width = int(w)
        # # 使用高质量细节放大算法
        # enhanced_img = self.enhance_image_details(rotated_img, (target_width, target_height))
        
        # fx=fy=2.0
        # enhanced_img = cv2.resize(rotated_img, dsize=None, fx=fx, fy=fy, 
        #              interpolation=cv2.INTER_LANCZOS4)
        # self.logger.debug(f"展平图像已从 {rotated_img.shape} 高质量放大到 {enhanced_img.shape}")
        
        # return enhanced_img
        
        return rotated_img

    def flatten_ring_area_bilinear(self, img_gray, C_x, C_y, outer_radius, inner_radius):
        """
        使用双线性插值的圆环区域极坐标展平算法
        """
        # 计算展平后图像的尺寸
        W = int(np.ceil(2 * np.pi * outer_radius))  # 宽度使用全圆周长
        H = int(np.ceil(outer_radius - inner_radius))  # 高度使用环宽
        
        height, width = img_gray.shape
        imgt = np.zeros((H, W), dtype=np.uint8)
        
        for U in range(W):
            for V in range(H):
                # 极坐标变换
                r = inner_radius + V
                theta = 2 * np.pi * (U / W)
                
                # 转换为原图像的笛卡尔坐标（浮点数）
                x = r * np.cos(theta) + C_x
                y = r * np.sin(theta) + C_y
                
                # 使用双线性插值获取像素值
                pixel_value = self.bilinear_interpolation(x, y, img_gray, width, height)
                imgt[V, U] = pixel_value
        
                return imgt 

    def enhance_image_details(self, img, target_size):
        """
        高质量细节放大算法
        
        Args:
            img: 输入图像
            target_size: 目标尺寸 (width, height)
        
        Returns:
            增强后的图像
        """
        target_width, target_height = target_size
        current_height, current_width = img.shape[:2]
        
        # 如果目标尺寸与当前尺寸相同，直接返回
        if target_width == current_width and target_height == current_height:
            return img
        
        self.logger.debug(f"开始高质量细节放大: {img.shape} -> {target_size}")
        
        # 步骤1: 预处理 - 去噪和细节保护
        enhanced_img = self.preprocess_for_scaling(img)
        
        # 步骤2: 多尺度插值
        if target_width > current_width or target_height > current_height:
            # 放大情况
            enhanced_img = self.multi_scale_upsampling(enhanced_img, target_size)
        else:
            # 缩小情况
            enhanced_img = self.high_quality_downsampling(enhanced_img, target_size)
        
        # 步骤3: 后处理 - 锐化和细节增强
        enhanced_img = self.post_process_scaling(enhanced_img)
        
        return enhanced_img
    
    def preprocess_for_scaling(self, img):
        """
        缩放前的预处理
        """
        # 轻微的双边滤波去噪，保护边缘
        denoised = cv2.bilateralFilter(img, d=5, sigmaColor=10, sigmaSpace=10)
        
        # 简化的锐化处理，避免复杂的类型转换
        kernel = np.array([[0, -1, 0],
                          [-1, 5, -1],
                          [0, -1, 0]], dtype=np.float32)
        
        if len(img.shape) == 3:
            enhanced = denoised.copy().astype(np.float32)
            for c in range(3):
                enhanced[:, :, c] = cv2.filter2D(enhanced[:, :, c], -1, kernel)
            enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
        else:
            enhanced = denoised.astype(np.float32)
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
        
        return enhanced
    
    def multi_scale_upsampling(self, img, target_size):
        """
        多尺度上采样算法
        """
        target_width, target_height = target_size
        current_height, current_width = img.shape[:2]
        
        # 计算缩放比例
        scale_x = target_width / current_width
        scale_y = target_height / current_height
        max_scale = max(scale_x, scale_y)
        
        # 如果缩放比例较大，分步进行
        if max_scale > 2.0:
            # 分步放大，每次最多放大2倍
            current_img = img
            while True:
                curr_h, curr_w = current_img.shape[:2]
                next_scale_x = target_width / curr_w
                next_scale_y = target_height / curr_h
                next_max_scale = max(next_scale_x, next_scale_y)
                
                if next_max_scale <= 2.0:
                    # 最后一步，直接缩放到目标尺寸
                    break
                
                # 中间步骤，放大2倍
                intermediate_w = int(curr_w * 2)
                intermediate_h = int(curr_h * 2)
                
                # 使用EDSR风格的插值
                current_img = cv2.resize(current_img, (intermediate_w, intermediate_h),
                                       interpolation=cv2.INTER_LANCZOS4)
                
                # 应用锐化滤波器
                current_img = self.apply_sharpening_filter(current_img)
        else:
            current_img = img
        
        # 最终缩放到目标尺寸
        final_img = cv2.resize(current_img, target_size, interpolation=cv2.INTER_LANCZOS4)
        
        return final_img
    
    def high_quality_downsampling(self, img, target_size):
        """
        高质量下采样算法
        """
        target_width, target_height = target_size
        current_height, current_width = img.shape[:2]
        
        # 计算缩放比例
        scale_x = target_width / current_width
        scale_y = target_height / current_height
        min_scale = min(scale_x, scale_y)
        
        # 预先应用抗锯齿滤波
        if min_scale < 0.5:
            # 强烈下采样，使用高斯模糊防止混叠
            kernel_size = int(1.0 / min_scale)
            if kernel_size % 2 == 0:
                kernel_size += 1
            kernel_size = min(kernel_size, 15)  # 限制核大小
            
            img = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)
        
        # 使用区域插值进行下采样
        downsampled = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
        
        return downsampled
    
    def apply_sharpening_filter(self, img):
        """
        应用锐化滤波器
        """
        # Unsharp masking锐化
        gaussian_blur = cv2.GaussianBlur(img, (3, 3), 1.0)
        sharpened = cv2.addWeighted(img, 1.5, gaussian_blur, -0.5, 0)
        
        # 确保像素值在有效范围内
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        
        return sharpened
    
    def post_process_scaling(self, img):
        """
        缩放后的后处理
        """
        # 应用适度的锐化
        sharpened = self.apply_sharpening_filter(img)
        
        # 对比度自适应增强
        if len(img.shape) == 3:
            # 彩色图像使用CLAHE
            lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
            l_channel = lab[:, :, 0]
            
            # 应用CLAHE到L通道
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_channel = clahe.apply(l_channel)
            
            lab[:, :, 0] = l_channel
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # 灰度图像直接应用CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(sharpened)
        
        # 轻微的细节增强
        if len(img.shape) == 3:
            gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        else:
            gray = enhanced
        
        # 使用高通滤波器增强细节
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]], dtype=np.float32)
        
        if len(img.shape) == 3:
            detail_enhanced = enhanced.copy()
            for c in range(3):
                channel = enhanced[:, :, c].astype(np.float32)
                filtered = cv2.filter2D(channel, -1, kernel)
                detail_enhanced[:, :, c] = np.clip(filtered, 0, 255).astype(np.uint8)
        else:
            channel = enhanced.astype(np.float32)
            detail_enhanced = cv2.filter2D(channel, -1, kernel)
            detail_enhanced = np.clip(detail_enhanced, 0, 255).astype(np.uint8)
        
        # 混合原图和增强图像
        final_img = cv2.addWeighted(enhanced, 0.7, detail_enhanced, 0.3, 0)
        
        return final_img
    
    def bilinear_interpolation(self, x, y, img_gray, width, height):
        """
        双线性插值算法
        
        Args:
            x, y: 浮点坐标
            img_gray: 灰度图像
            width, height: 图像尺寸
        
        Returns:
            插值后的像素值
        """
        # 边界处理
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))
        
        # 获取周围4个整数坐标点
        x1 = int(np.floor(x))
        x2 = int(np.ceil(x))
        y1 = int(np.floor(y))
        y2 = int(np.ceil(y))
        
        # 确保坐标在图像范围内
        x1 = max(0, min(width - 1, x1))
        x2 = max(0, min(width - 1, x2))
        y1 = max(0, min(height - 1, y1))
        y2 = max(0, min(height - 1, y2))
        
        # 获取4个角点的像素值
        if x1 == x2 and y1 == y2:
            # 如果正好在整数坐标上，直接返回该点的值
            return img_gray[y1, x1]
        elif x1 == x2:
            # 垂直插值
            t = y - y1
            return int(img_gray[y1, x1] * (1 - t) + img_gray[y2, x1] * t)
        elif y1 == y2:
            # 水平插值
            t = x - x1
            return int(img_gray[y1, x1] * (1 - t) + img_gray[y1, x2] * t)
        else:
            # 双线性插值
            # 获取4个角点的像素值
            I11 = float(img_gray[y1, x1])  # 左上
            I12 = float(img_gray[y2, x1])  # 左下
            I21 = float(img_gray[y1, x2])  # 右上
            I22 = float(img_gray[y2, x2])  # 右下
            
            # 计算权重
            wx = x - x1  # x方向权重
            wy = y - y1  # y方向权重
            
            # 双线性插值公式
            gray_value = (I11 * (1 - wx) * (1 - wy) + 
                         I21 * wx * (1 - wy) + 
                         I12 * (1 - wx) * wy + 
                         I22 * wx * wy)
            
            return int(np.clip(gray_value, 0, 255))

    # def flatten_ring_area_bilinear_color(self, img, C_x, C_y, outer_radius, inner_radius):
    #     """
    #     使用双线性插值的圆环区域极坐标展平算法 - 彩色版本
    #     """
    #     # 计算展平后图像的尺寸
    #     W = int(np.ceil(2 * np.pi * outer_radius))  # 宽度使用全圆周长
    #     H = int(np.ceil(outer_radius - inner_radius)) *2 # 高度使用环宽
        
    #     height, width = img.shape[:2]
    #     imgt = np.zeros((H, W, 3), dtype=np.uint8)  # 3通道彩色图像
        
    #     for U in range(W):
    #         for V in range(H):
    #             # 极坐标变换
    #             r = inner_radius + V
    #             theta = 2 * np.pi * (U / W)
                
    #             # 转换为原图像的笛卡尔坐标（浮点数）
    #             x = r * np.cos(theta) + C_x
    #             y = r * np.sin(theta) + C_y
                
    #             # 对每个颜色通道使用双线性插值获取像素值
    #             for c in range(3):  # BGR三个通道
    #                 pixel_value = self.bilinear_interpolation(x, y, img[:, :, c], width, height)
    #                 imgt[V, U, c] = pixel_value
        
    #     return imgt 
    # def flatten_ring_area_bilinear_color(
    #     self, img, C_x, C_y, outer_radius, inner_radius, height_scale=2.0
    # ):
    #     """
    #     支持高度缩放的极坐标展平算法
    #     Args:
    #         height_scale: 高度缩放因子（如2.0表示高度加倍）
    #     """
    #     # 基础尺寸计算
    #     W = int(2 * np.pi * outer_radius)
    #     H_physical = outer_radius - inner_radius
    #     H = int(H_physical * height_scale)  # 应用缩放因子
        
    #     height, width = img.shape[:2]
    #     imgt = np.zeros((H, W, 3), dtype=np.uint8)
        
    #     for U in range(W):
    #         theta = 2 * np.pi * (U / W)
    #         for V in range(H):
    #             # 关键：按物理比例映射，与height_scale无关
    #             r = inner_radius + (V / H) * H_physical
    #             x = r * np.cos(theta) + C_x
    #             y = r * np.sin(theta) + C_y
                
    #             # 边界保护
    #             x = np.clip(x, 0, width - 1)
    #             y = np.clip(y, 0, height - 1)
                
    #             for c in range(3):
    #                 imgt[V, U, c] = self.bilinear_interpolation(x, y, img[:, :, c], width, height)
        
    #     return imgt
    def flatten_ring_area_bilinear_color(
        self, img, C_x, C_y, outer_radius, inner_radius, height_scale=2.0
    ):
        W, H = 1891, 542
        U = np.arange(W)
        V = np.arange(H)[:, np.newaxis]  # 转换为列向量
        
        # 向量化计算所有坐标
        theta = 2 * np.pi * U / W
        r = inner_radius + (V / H) * (outer_radius - inner_radius)
        x = (r * np.cos(theta) + C_x).astype(np.float32)
        y = (r * np.sin(theta) + C_y).astype(np.float32)
        
        # 边界裁剪
        x = np.clip(x, 0, img.shape[1]-1)
        y = np.clip(y, 0, img.shape[0]-1)
        
        # 使用OpenCV的remap一次性插值
        return cv2.remap(img, x, y, interpolation=cv2.INTER_LINEAR)