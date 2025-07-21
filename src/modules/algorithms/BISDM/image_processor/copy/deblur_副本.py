import cv2
import numpy as np
import logging
from scipy import ndimage, signal
from skimage import restoration, filters, feature
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
        final_radius = np.median(radius_estimates)
        final_strength = np.median(strength_estimates)
        
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
        
        return {'radius': avg_radius, 'strength': avg_strength}
    
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
        radius = max(1.0, 8.0 * (1 - min(sharpness_score, 1.0)))
        strength = 1.0 - min(sharpness_score * 2, 1.0)
        
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
                        gaussian = filters.gaussian(image[:,:,i], sigma=0.8, channel_axis=None)
                    except TypeError:
                        # 兼容较旧版本的scikit-image
                        gaussian = filters.gaussian(image[:,:,i], sigma=0.8)
                    
                    # 自适应锐化：在边缘区域加强锐化
                    edges = feature.canny(image[:,:,i], sigma=1.0, low_threshold=0.1, high_threshold=0.2)
                    edge_factor = np.where(edges, sharpening_factor * 1.5, sharpening_factor)
                    result[:,:,i] = image[:,:,i] + edge_factor * (image[:,:,i] - gaussian)
            else:
                try:
                    gaussian = filters.gaussian(image, sigma=0.8, channel_axis=None)
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
                        result[:,:,i] = filters.gaussian(result[:,:,i], sigma=noise_sigma, channel_axis=None)
                    except TypeError:
                        # 兼容较旧版本的scikit-image
                        result[:,:,i] = filters.gaussian(result[:,:,i], sigma=noise_sigma)
            else:
                try:
                    result = filters.gaussian(result, sigma=noise_sigma, channel_axis=None)
                except TypeError:
                    # 兼容较旧版本的scikit-image
                    result = filters.gaussian(result, sigma=noise_sigma)
            
            return np.clip(result, 0, 1)
        except Exception as e:
            self.logger.warning(f"散焦后处理失败，返回原图像: {e}")
            return image 