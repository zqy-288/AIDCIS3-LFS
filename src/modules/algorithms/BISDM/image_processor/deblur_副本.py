import cv2
import numpy as np
import logging
from scipy import ndimage, signal
from skimage import restoration, filters, feature, exposure
from utils.config import Config

class DeblurProcessor:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.defocus_history = []  # 存储散焦估计历史
        self.prev_frame = None
    
    def process(self, image: np.ndarray, frame_idx: int = 0) -> np.ndarray:
        """处理图像散焦去模糊
        
        Args:
            image: 输入图像
            frame_idx: 帧索引
            
        Returns:
            去模糊后的图像
        """
        self.logger.info(f"开始处理第{frame_idx}帧的散焦去模糊")
        
        # 转换为浮点型以提高精度
        if len(image.shape) == 3:
            img_float = image.astype(np.float32) / 255.0
        else:
            img_float = image.astype(np.float32) / 255.0
        
        # 估计散焦模糊参数
        defocus_params = self._estimate_defocus_blur(img_float, frame_idx)
        self.logger.info(f"估计的散焦模糊参数 - 半径: {defocus_params['radius']:.2f}, 强度: {defocus_params['strength']:.2f}")
        
        # 生成散焦模糊核
        kernel = self._generate_defocus_kernel(defocus_params['radius'])
        
        # 选择去模糊方法
        if hasattr(self.config, 'defocus_method') and self.config.defocus_method == "lucy_richardson":
            deblurred = self._lucy_richardson_deblur(img_float, kernel)
        else:
            # 对于散焦模糊，维纳滤波通常效果更好
            deblurred = self._wiener_deblur(img_float, kernel)
        
        # 后处理：自适应锐化和降噪
        deblurred = self._post_process_defocus(deblurred, defocus_params['strength'])
        
        # 曝光调整：处理过亮区域
        deblurred = self._adjust_exposure(deblurred)
        
        # 转换回uint8
        result = np.clip(deblurred * 255, 0, 255).astype(np.uint8)
        
        self.logger.info(f"第{frame_idx}帧散焦去模糊处理完成")
        return result
    
    def _estimate_defocus_blur(self, image: np.ndarray, frame_idx: int) -> dict:
        """估计散焦模糊参数
        
        Args:
            image: 输入图像
            frame_idx: 帧索引
            
        Returns:
            包含散焦模糊参数的字典
        """
        # 使用多种方法估计散焦程度
        edge_method_params = self._estimate_defocus_edge_analysis(image)
        freq_method_params = self._estimate_defocus_frequency_domain(image)
        gradient_method_params = self._estimate_defocus_gradient_analysis(image)
        
        # 综合多种方法的结果
        radius_estimates = [
            edge_method_params['radius'],
            freq_method_params['radius'],
            gradient_method_params['radius']
        ]
        
        strength_estimates = [
            edge_method_params['strength'],
            freq_method_params['strength'],
            gradient_method_params['strength']
        ]
        
        # 使用中位数作为最终估计，减少异常值影响
        final_radius = float(np.median(radius_estimates))
        final_strength = float(np.median(strength_estimates))
        
        # 存储估计历史用于平滑
        self.defocus_history.append({'radius': final_radius, 'strength': final_strength})
        if len(self.defocus_history) > 3:  # 保持最近3帧的历史
            self.defocus_history.pop(0)
        
        # 使用历史平均值平滑估计
        avg_radius = np.mean([dh['radius'] for dh in self.defocus_history])
        avg_strength = np.mean([dh['strength'] for dh in self.defocus_history])
        
        # 限制散焦半径范围
        avg_radius = np.clip(avg_radius, 0.5, 10.0)
        avg_strength = np.clip(avg_strength, 0.1, 1.0)
        
        return {'radius': float(avg_radius), 'strength': float(avg_strength)}
    
    def _estimate_defocus_edge_analysis(self, image: np.ndarray) -> dict:
        """使用边缘分析估计散焦模糊"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        else:
            gray = (image * 255).astype(np.uint8)
        
        # 计算边缘响应强度
        edges_canny = cv2.Canny(gray, 50, 150)
        edges_sobel = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=3))
        
        # 边缘密度和强度分析
        edge_density = np.sum(edges_canny > 0) / edges_canny.size
        edge_strength = np.mean(edges_sobel[edges_sobel > 0]) if np.any(edges_sobel > 0) else 0
        
        # 计算边缘宽度（散焦程度的指标）
        edge_width = self._estimate_edge_width(gray)
        
        # 根据边缘特征估计散焦参数
        # 边缘密度低、强度弱、宽度大 -> 散焦严重
        radius = max(1.0, edge_width / 2.0)
        strength = 1.0 - min(edge_density * 10, 1.0)  # 密度越低，散焦越严重
        
        return {'radius': radius, 'strength': strength}
    
    def _estimate_edge_width(self, gray: np.ndarray) -> float:
        """估计边缘宽度"""
        # 使用Laplacian响应的零交叉点来估计边缘宽度
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        
        # 寻找零交叉点
        zero_crossings = np.zeros_like(laplacian)
        for i in range(1, laplacian.shape[0] - 1):
            for j in range(1, laplacian.shape[1] - 1):
                if laplacian[i, j] * laplacian[i+1, j] < 0 or laplacian[i, j] * laplacian[i, j+1] < 0:
                    zero_crossings[i, j] = 1
        
        # 计算平均边缘宽度
        if np.sum(zero_crossings) > 0:
            # 使用形态学操作估计边缘宽度
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(zero_crossings.astype(np.uint8), kernel, iterations=1)
            width_estimate = np.sum(dilated) / max(np.sum(zero_crossings), 1)
            return min(width_estimate, 10.0)
        else:
            return 3.0  # 默认宽度
    
    def _estimate_defocus_frequency_domain(self, image: np.ndarray) -> dict:
        """使用频域分析估计散焦模糊"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        else:
            gray = (image * 255).astype(np.uint8)
        
        # 计算频谱
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)
        
        # 计算径向功率谱密度
        h, w = gray.shape
        center_x, center_y = w // 2, h // 2
        
        # 创建径向距离矩阵
        y, x = np.ogrid[:h, :w]
        distances = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        # 计算径向平均功率谱
        max_radius = min(center_x, center_y)
        radial_profile = []
        
        for r in range(1, max_radius):
            mask = (distances >= r - 0.5) & (distances < r + 0.5)
            if np.any(mask):
                radial_profile.append(np.mean(magnitude_spectrum[mask]))
            else:
                radial_profile.append(0)
        
        radial_profile = np.array(radial_profile)
        
        # 分析高频衰减来估计散焦程度
        if len(radial_profile) > 10:
            # 计算高频部分的衰减率
            high_freq_start = len(radial_profile) // 3
            high_freq_power = np.mean(radial_profile[high_freq_start:])
            low_freq_power = np.mean(radial_profile[:len(radial_profile)//4])
            
            if low_freq_power > 0:
                attenuation_ratio = high_freq_power / low_freq_power
                # 衰减比越小，散焦越严重
                radius = max(1.0, 5.0 * (1 - attenuation_ratio))
                strength = attenuation_ratio
            else:
                radius = 3.0
                strength = 0.5
        else:
            radius = 3.0
            strength = 0.5
        
        return {'radius': radius, 'strength': strength}
    
    def _estimate_defocus_gradient_analysis(self, image: np.ndarray) -> dict:
        """使用梯度分析估计散焦模糊"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        else:
            gray = (image * 255).astype(np.uint8)
        
        # 计算图像梯度
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # 计算梯度统计特征
        grad_mean = np.mean(gradient_magnitude)
        grad_std = np.std(gradient_magnitude)
        grad_max = np.max(gradient_magnitude)
        
        # 使用Brenner梯度函数评估清晰度
        brenner_grad = np.sum((grad_x[:-2, :] - grad_x[2:, :])**2) + np.sum((grad_y[:, :-2] - grad_y[:, 2:])**2)
        brenner_grad = brenner_grad / (gray.shape[0] * gray.shape[1])
        
        # 使用Tenengrad函数评估清晰度
        tenengrad = np.sum(gradient_magnitude**2) / (gray.shape[0] * gray.shape[1])
        
        # 根据梯度特征估计散焦程度
        # 清晰图像应该有高梯度值和高变化
        normalized_brenner = brenner_grad / (grad_max + 1e-6)
        normalized_tenengrad = tenengrad / (grad_max**2 + 1e-6)
        
        # 综合评估：梯度越低，散焦越严重
        sharpness_score = (normalized_brenner + normalized_tenengrad) / 2
        
        # 将清晰度分数转换为散焦参数
        radius = float(max(1.0, 8.0 * (1.0 - min(sharpness_score, 1.0))))
        strength = float(1.0 - min(sharpness_score * 2, 1.0))
        
        return {'radius': radius, 'strength': strength}
    
    def _generate_defocus_kernel(self, radius: float) -> np.ndarray:
        """生成散焦模糊核（圆形核）"""
        if radius < 0.5:
            return np.array([[1]])
        
        # 创建核的尺寸（必须是奇数）
        kernel_size = int(2 * radius) + 1
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        kernel = np.zeros((kernel_size, kernel_size))
        center = kernel_size // 2
        
        # 生成圆形核
        for i in range(kernel_size):
            for j in range(kernel_size):
                distance = np.sqrt((i - center)**2 + (j - center)**2)
                if distance <= radius:
                    # 使用高斯权重而不是均匀权重，更符合光学散焦特性
                    kernel[i, j] = np.exp(-(distance**2) / (2 * (radius/3)**2))
        
        # 归一化
        if kernel.sum() > 0:
            kernel = kernel / kernel.sum()
        else:
            kernel[center, center] = 1
        
        return kernel
    
    def _lucy_richardson_deblur(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """使用Lucy-Richardson算法去模糊"""
        try:
            if len(image.shape) == 3:
                result = np.zeros_like(image)
                for i in range(3):
                    # 分通道处理以避免维度解释警告
                    try:
                        result[:,:,i] = restoration.richardson_lucy(
                            image[:,:,i], kernel, 
                            num_iter=self.config.lucy_richardson_iterations,
                            channel_axis=None  # 单通道处理
                        )
                    except TypeError:
                        # 兼容较旧版本的scikit-image
                        result[:,:,i] = restoration.richardson_lucy(
                            image[:,:,i], kernel, 
                            num_iter=self.config.lucy_richardson_iterations
                        )
            else:
                try:
                    result = restoration.richardson_lucy(
                        image, kernel, 
                        num_iter=self.config.lucy_richardson_iterations,
                        channel_axis=None
                    )
                except TypeError:
                    # 兼容较旧版本的scikit-image
                    result = restoration.richardson_lucy(
                        image, kernel, 
                        num_iter=self.config.lucy_richardson_iterations
                    )
        except Exception as e:
            self.logger.warning(f"Lucy-Richardson去模糊失败，使用维纳滤波: {e}")
            result = self._wiener_deblur(image, kernel)
        
        return result
    
    def _wiener_deblur(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """使用维纳滤波去模糊"""
        try:
            # 获取平衡参数（噪声比率）
            balance = getattr(self.config, 'wiener_noise_ratio', 0.01)
            
            if len(image.shape) == 3:
                result = np.zeros_like(image)
                for i in range(3):
                    # 分通道处理
                    result[:,:,i] = restoration.wiener(
                        image[:,:,i], kernel, balance
                    )
            else:
                result = restoration.wiener(image, kernel, balance)
                
        except Exception as e:
            self.logger.warning(f"维纳滤波失败，返回原图像: {e}")
            result = image
        
        return result
    
    def _post_process_defocus(self, image: np.ndarray, strength: float) -> np.ndarray:
        """针对散焦去模糊的后处理：自适应锐化和降噪"""
        try:
            # 根据散焦强度调整锐化程度
            sharpening_factor = 0.2 + 0.3 * strength  # 散焦越严重，锐化越强
            
            # 自适应锐化处理
            if len(image.shape) == 3:
                result = np.zeros_like(image)
                for i in range(3):
                    # 使用unsharp mask进行锐化，分通道处理避免警告
                    try:
                        gaussian = filters.gaussian(image[:,:,i], sigma=0.8, mode='reflect')
                    except TypeError:
                        # 兼容较旧版本的scikit-image
                        gaussian = filters.gaussian(image[:,:,i], sigma=0.8)
                    
                    # 自适应锐化：在边缘区域加强锐化
                    edges = feature.canny(image[:,:,i], sigma=1.0, low_threshold=0.1, high_threshold=0.2)
                    edge_factor = np.where(edges, sharpening_factor * 1.5, sharpening_factor)
                    result[:,:,i] = image[:,:,i] + edge_factor * (image[:,:,i] - gaussian)
            else:
                try:
                    gaussian = filters.gaussian(image, sigma=0.8, mode='reflect')
                except TypeError:
                    # 兼容较旧版本的scikit-image
                    gaussian = filters.gaussian(image, sigma=0.8)
                
                # 自适应锐化
                edges = feature.canny(image, sigma=1.0, low_threshold=0.1, high_threshold=0.2)
                edge_factor = np.where(edges, sharpening_factor * 1.5, sharpening_factor)
                result = image + edge_factor * (image - gaussian)
            
            # 轻微降噪，但保持边缘清晰
            noise_sigma = 0.3 * (1 - strength)  # 散焦越严重，降噪越轻
            if len(result.shape) == 3:
                for i in range(3):
                    try:
                        result[:,:,i] = filters.gaussian(result[:,:,i], sigma=noise_sigma, mode='reflect')
                    except TypeError:
                        # 兼容较旧版本的scikit-image
                        result[:,:,i] = filters.gaussian(result[:,:,i], sigma=noise_sigma)
            else:
                try:
                    result = filters.gaussian(result, sigma=noise_sigma, mode='reflect')
                except TypeError:
                    # 兼容较旧版本的scikit-image
                    result = filters.gaussian(result, sigma=noise_sigma)
            
            return np.clip(result, 0, 1)
        except Exception as e:
            self.logger.warning(f"散焦后处理失败，返回原图像: {e}")
            return image 

    def _adjust_exposure(self, image: np.ndarray) -> np.ndarray:
        """调整图像曝光，处理过亮区域
        
        Args:
            image: 输入图像（范围为0-1的浮点数）
            
        Returns:
            调整曝光后的图像
        """
        self.logger.info("开始处理过亮区域曝光调整")
        
        try:
            # 确保没有NaN值
            image = np.nan_to_num(image, nan=0.0, posinf=1.0, neginf=0.0)
            image = np.clip(image, 0, 1)
            
            # 从配置中获取参数，如果不存在则使用默认值
            overexposed_threshold = getattr(self.config, 'overexposed_threshold', 0.9)
            overexposed_area_threshold = getattr(self.config, 'overexposed_area_threshold', 0.05)
            shadow_boost_factor = getattr(self.config, 'shadow_boost', 1.2)
            shadow_threshold = getattr(self.config, 'shadow_threshold', 0.3)
            gamma_value = getattr(self.config, 'gamma_correction', 1.05)
            
            # 获取直方图均衡相关参数
            use_hist_equalization = getattr(self.config, 'use_hist_equalization', True)
            hist_eq_method = getattr(self.config, 'hist_eq_method', 'adaptive')
            clahe_clip_limit = getattr(self.config, 'clahe_clip_limit', 2.0)
            clahe_grid_size = getattr(self.config, 'clahe_grid_size', 8)
            
            # 如果是彩色图像
            if len(image.shape) == 3:
                # 1. 高动态范围处理 (HDR-like)
                # 将图像分为高光、中间调和阴影区域，分别处理
                image_yuv = cv2.cvtColor(image.astype(np.float32), cv2.COLOR_RGB2YUV)
                y_channel = image_yuv[:,:,0]  # 亮度通道
                
                # 识别过亮区域（亮度大于阈值）
                overexposed_mask = y_channel > overexposed_threshold
                overexposed_ratio = float(np.sum(overexposed_mask)) / float(overexposed_mask.size)
                self.logger.info(f"检测到的过亮区域占比: {overexposed_ratio:.2%}")
                
                # 2. 应用多种直方图均衡化处理
                if use_hist_equalization:
                    self.logger.info(f"应用直方图均衡化方法: {hist_eq_method}")
                    
                    # 创建暗区、中间区和亮区掩码
                    dark_mask = y_channel < shadow_threshold
                    mid_mask = (y_channel >= shadow_threshold) & (y_channel <= overexposed_threshold)
                    bright_mask = y_channel > overexposed_threshold
                    
                    # 创建YUV空间的结果图像
                    result_y = np.copy(y_channel)
                    
                    # 对亮度通道进行处理
                    if hist_eq_method == 'global':
                        # 全局直方图均衡
                        equalized_y = exposure.equalize_hist(y_channel)
                        
                        # 只对过亮区域应用较强的均衡
                        if overexposed_ratio > overexposed_area_threshold:
                            kernel = np.ones((5, 5), np.uint8)
                            dilated_bright_mask = cv2.dilate(bright_mask.astype(np.uint8), kernel, iterations=2)
                            bright_weight = filters.gaussian(dilated_bright_mask.astype(float), sigma=3.0, mode='reflect')
                            
                            # 混合亮区和原图
                            result_y = y_channel * (1 - bright_weight) + equalized_y * bright_weight
                            
                    elif hist_eq_method == 'adaptive':
                        # 自适应直方图均衡 (CLAHE)
                        # 创建CLAHE对象
                        clahe_y = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(clahe_grid_size, clahe_grid_size))
                        
                        # 将浮点图像转换为8位以应用CLAHE
                        y_uint8 = np.clip(y_channel * 255, 0, 255).astype(np.uint8)
                        equalized_y_uint8 = clahe_y.apply(y_uint8)
                        equalized_y = equalized_y_uint8.astype(np.float32) / 255.0
                        
                        # 使用权重混合，平滑过渡
                        result_y = y_channel.copy()
                        
                        # 对亮区应用强均衡
                        if np.any(bright_mask):
                            kernel = np.ones((5, 5), np.uint8)
                            dilated_bright_mask = cv2.dilate(bright_mask.astype(np.uint8), kernel, iterations=2)
                            bright_weight = filters.gaussian(dilated_bright_mask.astype(float), sigma=3.0, mode='reflect')
                            result_y = result_y * (1 - bright_weight) + equalized_y * bright_weight
                        
                        # 对中间区域应用中等均衡
                        if np.any(mid_mask):
                            mid_strength = 0.5  # 中间区域均衡强度
                            kernel = np.ones((3, 3), np.uint8)
                            dilated_mid_mask = cv2.dilate(mid_mask.astype(np.uint8), kernel, iterations=1)
                            mid_weight = filters.gaussian(dilated_mid_mask.astype(float), sigma=2.0, mode='reflect') * mid_strength
                            result_y = result_y * (1 - mid_weight) + equalized_y * mid_weight
                        
                    elif hist_eq_method == 'hdr':
                        # HDR风格处理
                        # 1. 提取亮区、中间区和暗区
                        y_bright = np.copy(y_channel)
                        y_bright[~bright_mask] = 0
                        
                        y_mid = np.copy(y_channel) 
                        y_mid[~mid_mask] = 0
                        
                        y_dark = np.copy(y_channel)
                        y_dark[~dark_mask] = 0
                        
                        # 2. 分别处理每个区域
                        # 亮区: 压缩高光，增加细节
                        if np.any(bright_mask):
                            # 局部自适应直方图均衡，降低clip limit以减少过均衡
                            clahe_bright = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(clahe_grid_size, clahe_grid_size))
                            y_bright_uint8 = np.clip(y_bright * 255, 0, 255).astype(np.uint8)
                            y_bright_eq = clahe_bright.apply(y_bright_uint8).astype(np.float32) / 255.0
                            # 额外的高光压缩
                            y_bright_eq = np.power(np.clip(y_bright_eq, 0.01, 1.0), 1.2)
                            y_bright = np.where(bright_mask, y_bright_eq, 0)
                        
                        # 中间区: 增加对比度和细节
                        if np.any(mid_mask):
                            clahe_mid = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(clahe_grid_size, clahe_grid_size))
                            # 归一化中间区域到0-255范围
                            y_mid_norm = np.zeros_like(y_mid)
                            y_mid_valid = mid_mask & (y_mid > 0)
                            if np.any(y_mid_valid):
                                y_mid_min = np.min(y_mid[y_mid_valid])
                                y_mid_max = np.max(y_mid[y_mid_valid])
                                if y_mid_max > y_mid_min:
                                    y_mid_norm[y_mid_valid] = (y_mid[y_mid_valid] - y_mid_min) / (y_mid_max - y_mid_min)
                            
                            y_mid_uint8 = np.clip(y_mid_norm * 255, 0, 255).astype(np.uint8)
                            y_mid_eq = clahe_mid.apply(y_mid_uint8).astype(np.float32) / 255.0
                            
                            # 恢复到原始亮度范围
                            if np.any(y_mid_valid) and y_mid_max > y_mid_min:
                                y_mid_eq[y_mid_valid] = y_mid_eq[y_mid_valid] * (y_mid_max - y_mid_min) + y_mid_min
                            
                            y_mid = np.where(mid_mask, y_mid_eq, 0)
                        
                        # 暗区: 提升亮度，增强细节
                        if np.any(dark_mask):
                            # 对暗区应用gamma校正，提高亮度
                            y_dark_boost = np.power(np.clip(y_dark, 0.01, 1.0), 0.7)  # gamma < 1 提升暗区
                            # 应用局部对比度增强
                            y_dark_boost_uint8 = np.clip(y_dark_boost * 255, 0, 255).astype(np.uint8)
                            clahe_dark = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(clahe_grid_size, clahe_grid_size))
                            y_dark_eq = clahe_dark.apply(y_dark_boost_uint8).astype(np.float32) / 255.0
                            y_dark = np.where(dark_mask, y_dark_eq, 0)
                        
                        # 3. 融合三个区域，确保平滑过渡
                        # 创建平滑过渡掩码
                        bright_weight = filters.gaussian(bright_mask.astype(float), sigma=2.0, mode='reflect')
                        mid_weight = filters.gaussian(mid_mask.astype(float), sigma=2.0, mode='reflect')
                        dark_weight = filters.gaussian(dark_mask.astype(float), sigma=2.0, mode='reflect')
                        
                        # 归一化权重
                        total_weight = bright_weight + mid_weight + dark_weight
                        total_weight[total_weight == 0] = 1  # 避免除零
                        
                        bright_weight = bright_weight / total_weight
                        mid_weight = mid_weight / total_weight
                        dark_weight = dark_weight / total_weight
                        
                        # 加权融合
                        result_y = y_bright * bright_weight + y_mid * mid_weight + y_dark * dark_weight
                    
                    # 更新YUV图像的Y通道
                    image_yuv[:,:,0] = result_y
                    
                    # 转回RGB
                    image = cv2.cvtColor(image_yuv, cv2.COLOR_YUV2RGB)
                else:
                    # 如果不使用直方图均衡，则使用原来的HSV空间处理
                    image_hsv = cv2.cvtColor(image.astype(np.float32), cv2.COLOR_RGB2HSV)
                    v_channel = image_hsv[:,:,2]
                    
                    if overexposed_ratio > overexposed_area_threshold:
                        # 自适应局部对比度增强
                        v_adjusted = exposure.equalize_adapthist(v_channel, clip_limit=0.03)
                        
                        # 混合调整
                        kernel = np.ones((5, 5), np.uint8)
                        dilated_mask = cv2.dilate(overexposed_mask.astype(np.uint8), kernel, iterations=2)
                        weight_mask = filters.gaussian(dilated_mask.astype(float), sigma=3.0, mode='reflect')
                        
                        v_channel_adjusted = v_channel * (1 - weight_mask) + v_adjusted * weight_mask
                        image_hsv[:,:,2] = v_channel_adjusted
                        image = cv2.cvtColor(image_hsv, cv2.COLOR_HSV2RGB)
                
                # 应用额外的伽马校正来调整整体亮度
                if self.config.exposure_adjustment:
                    gamma = gamma_value
                    # 避免出现NaN值
                    image = np.clip(image, 0.001, 1.0)  # 避免零值
                    image = np.power(image, gamma)
                    
                    # 轻微提升阴影区域
                    shadow_mask = np.all(image < shadow_threshold, axis=2) if len(image.shape) == 3 else image < shadow_threshold
                    if np.any(shadow_mask):
                        shadow_boost = shadow_boost_factor
                        shadow_weight = filters.gaussian(shadow_mask.astype(float), sigma=2.0, mode='reflect')
                        for i in range(3):
                            image[:,:,i] = image[:,:,i] * (1 - shadow_weight) + image[:,:,i] * shadow_boost * shadow_weight
                
                # 最后应用细节增强
                detail_enhancement_factor = getattr(self.config, 'detail_enhancement_factor', 0.3)
                if detail_enhancement_factor > 0:
                    # 使用unsharp mask增强细节
                    for i in range(3):
                        blur = cv2.GaussianBlur(image[:,:,i], (0, 0), 2.0)
                        image[:,:,i] = image[:,:,i] + detail_enhancement_factor * (image[:,:,i] - blur)
                
            else:
                # 灰度图像处理
                # 检测过亮区域
                overexposed_mask = image > overexposed_threshold
                overexposed_ratio = float(np.sum(overexposed_mask)) / float(overexposed_mask.size)
                
                if use_hist_equalization:
                    self.logger.info(f"应用直方图均衡化方法 (灰度图): {hist_eq_method}")
                    
                    if hist_eq_method == 'global':
                        # 全局直方图均衡
                        equalized = exposure.equalize_hist(image)
                        
                        # 混合处理
                        kernel = np.ones((5, 5), np.uint8)
                        dilated_mask = cv2.dilate(overexposed_mask.astype(np.uint8), kernel, iterations=2)
                        weight_mask = filters.gaussian(dilated_mask.astype(float), sigma=3.0, mode='reflect')
                        image = image * (1 - weight_mask) + equalized * weight_mask
                        
                    elif hist_eq_method == 'adaptive' or hist_eq_method == 'hdr':
                        # 自适应直方图均衡 (CLAHE)
                        # 创建CLAHE对象
                        clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(clahe_grid_size, clahe_grid_size))
                        
                        # 将浮点图像转换为8位以应用CLAHE
                        img_uint8 = np.clip(image * 255, 0, 255).astype(np.uint8)
                        equalized_uint8 = clahe.apply(img_uint8)
                        equalized = equalized_uint8.astype(np.float32) / 255.0
                        
                        # 混合处理
                        if overexposed_ratio > overexposed_area_threshold:
                            kernel = np.ones((5, 5), np.uint8)
                            dilated_mask = cv2.dilate(overexposed_mask.astype(np.uint8), kernel, iterations=2)
                            weight_mask = filters.gaussian(dilated_mask.astype(float), sigma=3.0, mode='reflect')
                            image = image * (1 - weight_mask) + equalized * weight_mask
                        
                        # 提升暗区
                        dark_mask = image < shadow_threshold
                        if np.any(dark_mask):
                            shadow_boost = shadow_boost_factor
                            shadow_weight = filters.gaussian(dark_mask.astype(float), sigma=2.0, mode='reflect')
                            # 确保不会有零值导致的NaN
                            dark_boost = np.power(np.clip(image, 0.001, 1.0), 0.7)  # gamma < 1 提升暗区
                            image = image * (1 - shadow_weight) + dark_boost * shadow_weight
                
                else:
                    if overexposed_ratio > overexposed_area_threshold:
                        # 自适应局部对比度增强
                        image_adjusted = exposure.equalize_adapthist(image, clip_limit=0.03)
                        
                        # 创建平滑过渡
                        kernel = np.ones((5, 5), np.uint8)
                        dilated_mask = cv2.dilate(overexposed_mask.astype(np.uint8), kernel, iterations=2)
                        weight_mask = filters.gaussian(dilated_mask.astype(float), sigma=3.0, mode='reflect')
                        
                        # 在过亮区域应用调整
                        image = image * (1 - weight_mask) + image_adjusted * weight_mask
                
                # 全局Gamma校正
                if self.config.exposure_adjustment:
                    gamma = gamma_value
                    # 避免出现NaN值
                    image = np.clip(image, 0.001, 1.0)  # 避免零值
                    image = np.power(image, gamma)
                    
                # 增强细节
                detail_enhancement_factor = getattr(self.config, 'detail_enhancement_factor', 0.3)
                if detail_enhancement_factor > 0:
                    blur = cv2.GaussianBlur(image, (0, 0), 2.0)
                    image = image + detail_enhancement_factor * (image - blur)
            
            # 最后确保没有NaN值和数值范围正确
            image = np.nan_to_num(image, nan=0.0, posinf=1.0, neginf=0.0)
            return np.clip(image, 0, 1)
            
        except Exception as e:
            self.logger.warning(f"曝光调整失败: {e}")
            return np.clip(image, 0, 1)  # 确保返回值总是合法的 