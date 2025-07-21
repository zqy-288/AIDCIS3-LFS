#!/usr/bin/env python3
"""
圆形检测器 - 霍夫变换和RANSAC算法实现
基于C++版本翻译为Python
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional
import os

@dataclass
class Circle:
    """圆形数据结构"""
    radius: float
    x_center: int
    y_center: int
    max_vote: int = 0

class CircleDetector:
    """圆形检测器类 - 实现霍夫变换和RANSAC算法"""
    
    def __init__(self):
        self.theta_map = self._precompute_theta_map()
    
    def _precompute_theta_map(self):
        """预计算所有角度的余弦和正弦值"""
        theta_map = {}
        for theta_d in range(360):
            theta_r = np.radians(theta_d)
            theta_map[theta_d] = (np.cos(theta_r), np.sin(theta_r))
        return theta_map
    
    def compute_hough_vote(self, vote_accumulator: np.ndarray, img_edges: np.ndarray, 
                          radius: float) -> int:
        """
        计算霍夫投票
        
        参数:
        - vote_accumulator: 投票累加器
        - img_edges: 边缘图像
        - radius: 圆半径
        
        返回:
        - max_vote: 最大投票数
        """
        rows, cols = img_edges.shape
        max_vote = 0
        
        # 遍历图像的每个像素
        for i in range(rows):
            for j in range(cols):
                # 只在边缘像素上计算霍夫变换
                if img_edges[i, j] != 0:
                    for theta in range(360):
                        cos_theta, sin_theta = self.theta_map[theta]
                        a = int(i - radius * cos_theta)
                        b = int(j + radius * sin_theta)
                        
                        # 只在边界内增加投票
                        if 0 <= a < rows and 0 <= b < cols:
                            vote_accumulator[a, b] += 1
                            if vote_accumulator[a, b] > max_vote:
                                max_vote = vote_accumulator[a, b]
        
        return max_vote
    
    def find_hough_peaks(self, vote_accumulator: np.ndarray, max_vote: int, 
                        number_peaks: int, radius: float) -> List[Circle]:
        """
        找到霍夫峰值
        
        参数:
        - vote_accumulator: 投票累加器
        - max_vote: 最大投票数
        - number_peaks: 要找的峰值数量
        - radius: 圆半径
        
        返回:
        - peak_centers: 峰值中心列表
        """
        threshold = int(0.8 * max_vote)
        
        # 如果阈值小于100，可能不是圆
        if threshold < 100:
            threshold = 100
        
        peak_centers = []
        num_peaks = 0
        clear_zone = 4
        
        # 循环直到达到所需的峰值数量
        while num_peaks < number_peaks:
            # 找到投票累加器的最大值和位置
            max_value = np.max(vote_accumulator)
            max_locations = np.where(vote_accumulator == max_value)
            
            if len(max_locations[0]) == 0:
                break
                
            max_pt_y, max_pt_x = max_locations[0][0], max_locations[1][0]
            
            # 如果最大值超过阈值
            if max_value > threshold:
                num_peaks += 1
                
                # 创建新圆
                new_circle = Circle(
                    radius=radius,
                    x_center=max_pt_x,
                    y_center=max_pt_y,
                    max_vote=int(max_value)
                )
                
                # 存储新圆
                peak_centers.append(new_circle)
                
                # 将邻域区域设置为零，避免在同一区域找到圆
                y_start = max(0, max_pt_y - clear_zone)
                y_end = min(vote_accumulator.shape[0], max_pt_y + clear_zone + 1)
                x_start = max(0, max_pt_x - clear_zone)
                x_end = min(vote_accumulator.shape[1], max_pt_x + clear_zone + 1)
                
                vote_accumulator[y_start:y_end, x_start:x_end] = 0
            else:
                break
        
        return peak_centers
    
    def check_circle_present(self, best_circles: List[Circle], new_circle: Circle, 
                           pixel_interval: int) -> bool:
        """
        检查圆是否已经存在
        
        参数:
        - best_circles: 最佳圆列表
        - new_circle: 新圆
        - pixel_interval: 像素间隔
        
        返回:
        - found: 是否找到相似圆
        """
        found = False
        i = 0
        
        while i < len(best_circles):
            existing_circle = best_circles[i]
            
            # 检查是否有相同中心的圆
            x_close = (new_circle.x_center <= existing_circle.x_center + pixel_interval and 
                      new_circle.x_center >= existing_circle.x_center - pixel_interval)
            y_close = (new_circle.y_center <= existing_circle.y_center + pixel_interval and 
                      new_circle.y_center >= existing_circle.y_center - pixel_interval)
            
            if x_close and y_close:
                # 如果已存在，检查新圆是否有更多投票
                if existing_circle.max_vote < new_circle.max_vote:
                    best_circles.pop(i)
                    found = False
                    break
                else:
                    # 检查是否是圆内圆
                    if existing_circle.radius * 2 < new_circle.radius:
                        found = False
                        i += 1
                    else:
                        found = True
                        i += 1
            else:
                i += 1
        
        return found
    
    def hough_transform(self, img_edges: np.ndarray, radius_start: int, 
                       radius_end: int) -> List[Circle]:
        """
        霍夫变换圆检测
        
        参数:
        - img_edges: 边缘图像
        - radius_start: 起始半径
        - radius_end: 结束半径
        
        返回:
        - best_circles: 最佳圆列表
        """
        rows, cols = img_edges.shape
        best_circles = []
        number_peaks = 10
        pixel_interval = 15
        
        print(f"霍夫变换检测，半径范围: {radius_start}-{radius_end}")
        
        # 遍历每个可能的半径
        for r in range(radius_start, radius_end + 1):
            # 初始化累加器
            vote_accumulator = np.zeros((rows, cols), dtype=np.int32)
            
            # 计算每个边缘像素的投票
            max_vote = self.compute_hough_vote(vote_accumulator, img_edges, r)
            
            if max_vote == 0:
                continue
            
            # 找到具有最大投票的圆
            peak_centers = self.find_hough_peaks(vote_accumulator, max_vote, number_peaks, r)
            
            # 对于找到的每个圆，只保留最佳的（最大投票）并移除重复
            for circle in peak_centers:
                found = self.check_circle_present(best_circles, circle, pixel_interval)
                if not found:
                    best_circles.append(circle)
            
            print(f"  半径 {r}: 找到 {len(peak_centers)} 个候选圆")
        
        return best_circles
    
    def circle_ransac(self, edge_points: List[Tuple[int, int]], iterations: int) -> List[Circle]:
        """
        RANSAC圆检测
        
        参数:
        - edge_points: 边缘点列表
        - iterations: 迭代次数
        
        返回:
        - best_circles: 最佳圆列表
        """
        best_circles = []
        edge_points = edge_points.copy()  # 避免修改原始数据
        
        print(f"RANSAC检测，迭代次数: {iterations}, 边缘点数: {len(edge_points)}")
        
        for iteration in range(iterations):
            if len(edge_points) < 100:
                print(f"边缘点不足，停止迭代 (剩余点数: {len(edge_points)})")
                break
            
            # 随机选择三个点
            if len(edge_points) < 3:
                break
                
            indices = random.sample(range(len(edge_points)), 3)
            A = edge_points[indices[0]]
            B = edge_points[indices[1]]
            C = edge_points[indices[2]]
            
            # 计算中点
            midpt_AB = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
            midpt_BC = ((B[0] + C[0]) / 2, (B[1] + C[1]) / 2)
            
            # 计算斜率和截距
            try:
                slope_AB = (B[1] - A[1]) / (B[0] - A[0] + 1e-10)
                slope_BC = (C[1] - B[1]) / (C[0] - B[0] + 1e-10)
                
                # 计算垂直斜率和截距
                slope_midpt_AB = -1.0 / slope_AB
                slope_midpt_BC = -1.0 / slope_BC
                intercept_midpt_AB = midpt_AB[1] - slope_midpt_AB * midpt_AB[0]
                intercept_midpt_BC = midpt_BC[1] - slope_midpt_BC * midpt_BC[0]
                
                # 计算垂线的交点以找到圆心和半径
                if abs(slope_midpt_AB - slope_midpt_BC) < 1e-10:
                    continue  # 平行线，跳过
                    
                center_x = (intercept_midpt_BC - intercept_midpt_AB) / (slope_midpt_AB - slope_midpt_BC)
                center_y = slope_midpt_AB * center_x + intercept_midpt_AB
                
                # 计算半径
                diff_x = center_x - A[0]
                diff_y = center_y - A[1]
                radius = np.sqrt(diff_x * diff_x + diff_y * diff_y)
                circumference = 2.0 * np.pi * radius
                
                # 找到符合圆半径的边缘点
                on_circle = []
                not_on_circle = []
                radius_threshold = 3
                
                for i, point in enumerate(edge_points):
                    diff_x = point[0] - center_x
                    diff_y = point[1] - center_y
                    distance_to_center = np.sqrt(diff_x * diff_x + diff_y * diff_y)
                    
                    if abs(distance_to_center - radius) < radius_threshold:
                        on_circle.append(i)
                    else:
                        not_on_circle.append(i)
                
                # 如果边缘点数量超过周长，我们找到了正确的圆
                if len(on_circle) >= circumference:
                    circle_found = Circle(
                        radius=radius,
                        x_center=int(center_x),
                        y_center=int(center_y),
                        max_vote=len(on_circle)
                    )
                    
                    best_circles.append(circle_found)
                    print(f"  找到圆: 中心({center_x:.1f}, {center_y:.1f}), 半径{radius:.1f}, 支持点{len(on_circle)}")
                    
                    # 移除参与投票的边缘点
                    edge_points = [edge_points[i] for i in not_on_circle]
                
            except (ZeroDivisionError, ValueError):
                continue
        
        return best_circles
    
    def draw_circles(self, img: np.ndarray, circles: List[Circle], 
                    color: Tuple[int, int, int] = (255, 0, 0), 
                    thickness: int = 4) -> np.ndarray:
        """
        在图像上绘制圆
        
        参数:
        - img: 输入图像
        - circles: 圆列表
        - color: 绘制颜色 (B, G, R)
        - thickness: 线条粗细
        
        返回:
        - result: 绘制结果图像
        """
        if len(img.shape) == 2:  # 灰度图像
            result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            result = img.copy()
        
        for circle in circles:
            cv2.circle(result, 
                      (circle.x_center, circle.y_center), 
                      int(circle.radius), 
                      color, 
                      thickness)
            # 绘制圆心
            cv2.circle(result, 
                      (circle.x_center, circle.y_center), 
                      3, 
                      color, 
                      -1)
        
        return result
    
    def detect_circles(self, img_path: str, output_dir: str = "circle_detection_results"):
        """
        主要的圆检测函数
        
        参数:
        - img_path: 图像路径
        - output_dir: 输出目录
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 读取图像
        img_input = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img_input is None:
            raise ValueError(f"无法打开图像: {img_path}")
        
        print(f"开始处理图像: {img_path}")
        print(f"图像尺寸: {img_input.shape}")
        print("开始计算 - 请等待，根据图像大小可能需要一些时间...")
        
        # 应用高斯滤波去噪和Canny边缘检测
        img_gaussian = cv2.GaussianBlur(img_input, (5, 5), 1.0)
        img_edges = cv2.Canny(img_gaussian, 160, 320)
        
        # 保存边缘图像
        edge_path = os.path.join(output_dir, "edges.jpg")
        cv2.imwrite(edge_path, img_edges)
        print(f"边缘检测完成，保存到: {edge_path}")
        
        # ============== 霍夫变换 ==============
        print("\n--- 霍夫变换圆检测 ---")
        hough_begin = time.time()
        
        # 半径需要根据图像大小和圆的大小进行调整
        img_size = min(img_input.shape)
        radius_start = max(10, int(img_size * 0.05))  # 图像尺寸的5%
        radius_end = min(int(img_size * 0.3), radius_start + 50)  # 图像尺寸的30%或最大50像素范围
        
        best_circles_hough = self.hough_transform(img_edges, radius_start, radius_end)
        
        hough_end = time.time()
        hough_time = hough_end - hough_begin
        
        print(f"霍夫变换找到的圆数量: {len(best_circles_hough)}")
        print(f"霍夫变换耗时: {hough_time:.2f}秒")
        
        # 绘制霍夫变换结果
        result_img_hough = self.draw_circles(img_input, best_circles_hough, (255, 0, 0))
        hough_path = os.path.join(output_dir, "hough_transform_result.jpg")
        cv2.imwrite(hough_path, result_img_hough)
        print(f"霍夫变换结果保存到: {hough_path}")
        
        # ============== RANSAC ==============
        print("\n--- RANSAC圆检测 ---")
        ransac_begin = time.time()
        
        # 提取边缘点
        edge_points = []
        for i in range(img_edges.shape[0]):
            for j in range(img_edges.shape[1]):
                if img_edges[i, j] != 0:
                    edge_points.append((j, i))  # (x, y)格式
        
        print(f"提取到边缘点数量: {len(edge_points)}")
        
        # RANSAC迭代次数需要根据图像复杂度调整
        iterations = min(1200, len(edge_points) // 10)
        best_circles_ransac = self.circle_ransac(edge_points, iterations)
        
        ransac_end = time.time()
        ransac_time = ransac_end - ransac_begin
        
        print(f"RANSAC找到的圆数量: {len(best_circles_ransac)}")
        print(f"RANSAC耗时: {ransac_time:.2f}秒")
        
        # 绘制RANSAC结果
        result_img_ransac = self.draw_circles(img_input, best_circles_ransac, (0, 255, 0))
        ransac_path = os.path.join(output_dir, "ransac_result.jpg")
        cv2.imwrite(ransac_path, result_img_ransac)
        print(f"RANSAC结果保存到: {ransac_path}")
        
        # ============== 综合结果 ==============
        print("\n--- 综合结果 ---")
        
        # 创建综合可视化
        self._create_summary_visualization(img_input, img_edges, 
                                         best_circles_hough, best_circles_ransac,
                                         output_dir)
        
        # 打印检测到的圆的详细信息
        self._print_circle_details(best_circles_hough, best_circles_ransac)
        
        return best_circles_hough, best_circles_ransac
    
    def _create_summary_visualization(self, img_input: np.ndarray, img_edges: np.ndarray,
                                    hough_circles: List[Circle], ransac_circles: List[Circle],
                                    output_dir: str):
        """创建综合可视化"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 原始图像
        axes[0, 0].imshow(img_input, cmap='gray')
        axes[0, 0].set_title('原始图像')
        axes[0, 0].axis('off')
        
        # 边缘图像
        axes[0, 1].imshow(img_edges, cmap='gray')
        axes[0, 1].set_title('边缘检测结果')
        axes[0, 1].axis('off')
        
        # 霍夫变换结果
        hough_result = self.draw_circles(img_input, hough_circles, (255, 0, 0))
        axes[1, 0].imshow(cv2.cvtColor(hough_result, cv2.COLOR_BGR2RGB))
        axes[1, 0].set_title(f'霍夫变换检测 ({len(hough_circles)}个圆)')
        axes[1, 0].axis('off')
        
        # RANSAC结果
        ransac_result = self.draw_circles(img_input, ransac_circles, (0, 255, 0))
        axes[1, 1].imshow(cv2.cvtColor(ransac_result, cv2.COLOR_BGR2RGB))
        axes[1, 1].set_title(f'RANSAC检测 ({len(ransac_circles)}个圆)')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        summary_path = os.path.join(output_dir, "detection_summary.png")
        plt.savefig(summary_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"综合结果保存到: {summary_path}")
    
    def _print_circle_details(self, hough_circles: List[Circle], ransac_circles: List[Circle]):
        """打印圆的详细信息"""
        print("\n=== 检测结果详情 ===")
        
        print(f"\n霍夫变换检测到的圆 ({len(hough_circles)}个):")
        for i, circle in enumerate(hough_circles):
            print(f"  圆{i+1}: 中心({circle.x_center}, {circle.y_center}), "
                  f"半径{circle.radius:.1f}, 投票数{circle.max_vote}")
        
        print(f"\nRANSAC检测到的圆 ({len(ransac_circles)}个):")
        for i, circle in enumerate(ransac_circles):
            print(f"  圆{i+1}: 中心({circle.x_center}, {circle.y_center}), "
                  f"半径{circle.radius:.1f}, 支持点{circle.max_vote}")

def main():
    """主函数"""
    # 创建检测器
    detector = CircleDetector()
    
    # 测试图像路径
    img_paths = [
        "output_80mms/01_deblurred/enhanced_0000.png",
        # 可以添加更多图像路径
    ]
    
    # 检测圆形
    for img_path in img_paths:
        if os.path.exists(img_path):
            try:
                print(f"\n{'='*60}")
                print(f"处理图像: {img_path}")
                print(f"{'='*60}")
                
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                output_dir = f"circle_detection_{base_name}"
                
                hough_circles, ransac_circles = detector.detect_circles(img_path, output_dir)
                
            except Exception as e:
                print(f"处理图像 {img_path} 时出错: {e}")
        else:
            print(f"图像文件不存在: {img_path}")

if __name__ == "__main__":
    main() 