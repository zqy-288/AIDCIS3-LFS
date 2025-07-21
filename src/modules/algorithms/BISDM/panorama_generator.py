#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
展平图像全景拼接器
功能: 将data目录中的展平图像拼接成全景图，添加深度和角度坐标轴及图例
"""

import cv2
import numpy as np
import os
import glob
import logging
from pathlib import Path
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Union
import time
from PIL import Image, ImageDraw, ImageFont
import argparse

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PanoramaGenerator:
    """全景图生成器 - 拼接展平图像并添加坐标轴和图例"""
    
    def __init__(self, pipe_length_mm: Optional[float] = None):
        # 基本配置
        self.enable_depth_axis = True  # 启用深度坐标轴
        self.enable_angle_axis = True  # 启用角度坐标轴
        self.save_intermediate = True  # 保存中间结果
        
        # 坐标轴配置
        self.depth_axis_tick_interval = 50  # 深度轴刻度间隔(mm)
        self.angle_axis_tick_interval = 30  # 角度轴刻度间隔(度)
        
        # 像素与物理单位的换算关系及深度配置
        self.default_frame_offset = 30  # 默认帧间偏移量(px)
        self.initial_depth_mm = 10  # 初始深度(mm)
        
        # 如果提供了管道长度参数，则使用该参数，否则使用默认值
        self.total_depth_mm = pipe_length_mm if pipe_length_mm is not None else 900  # 总深度(mm)
        
        # 内部数据
        self.offsets_data = []  # 存储图像偏移量
        self.pair_dy_data = []  # 存储相邻图像间的偏移量
        self.depth_positions_mm = []  # 深度位置(mm)
        self.total_pixels = 0  # 总像素数
        
        # 图像尺寸
        self.image_width = 0  # 图像宽度
        self.image_height = 0  # 图像高度
        
        # 颜色配置
        self.axis_color = (255, 255, 255)  # 坐标轴颜色(白色)
        self.legend_text_color = (255, 255, 255)  # 图例文字颜色
        self.legend_bg_color = (50, 50, 50)  # 图例背景颜色
        self.legend_opacity = 0.8  # 图例背景透明度
        
        # 图例配置
        self.show_scale_bar = True  # 显示比例尺
        self.show_legend = True  # 显示图例
        self.legend_width = 220  # 图例宽度（放大）
        self.legend_height = 220  # 图例高度（放大）
        
        logger.info("全景图生成器初始化完成")
    
    def load_images(self, data_dir: str, max_frames: Optional[int] = None) -> List[np.ndarray]:
        """
        加载展平图像
        :param data_dir: 展平图像目录
        :param max_frames: 最大加载帧数，如果指定，则只加载前max_frames帧图像
        :return: 图像列表
        """
        # 查找所有展平图像
        unwrapped_images = sorted(glob.glob(os.path.join(data_dir, "unwrapped_*.png")))
        if not unwrapped_images:
            raise FileNotFoundError(f"在 {data_dir} 目录中未找到展平图像")
        
        # 如果指定了最大帧数，则只取前max_frames帧
        if max_frames is not None and max_frames > 0:
            unwrapped_images = unwrapped_images[:max_frames]
            logger.info(f"限制加载前 {max_frames} 帧图像")
        
        logger.info(f"找到{len(unwrapped_images)}个图像文件")
        
        # 加载图像
        images = []
        for i, img_path in enumerate(unwrapped_images):
            logger.info(f"加载图像: {img_path}")
            img = cv2.imread(img_path)
            if img is None:
                logger.error(f"无法加载图像: {img_path}")
                continue
            
            # 保存第一张图像的尺寸
            if i == 0:
                self.image_height, self.image_width = img.shape[:2]
                
            images.append(img)
        
        return images
    
    def create_panorama(self, images: List[np.ndarray]) -> np.ndarray:
        """
        生成全景图
        :param images: 图像列表
        :return: 生成的全景图
        """
        if not images:
            raise ValueError("输入图像列表为空")
        if len(images) == 1:
            return images[0]
        
        logger.info(f"开始拼接 {len(images)} 张图像")
        
        # 计算图像偏移量
        offsets, pair_dy = self._calculate_variable_offsets(images)
        
        # 保存数据用于可视化
        self.offsets_data = offsets.copy()
        self.pair_dy_data = pair_dy.copy()
        
        # 计算深度位置
        self._calculate_depth_positions(images)
        
        # 创建画布
        max_w = max(im.shape[1] for im in images)
        
        # 计算画布高度
        canvas_height_needed = 0
        for i, (im, y_start) in enumerate(zip(images, offsets)):
            img_bottom = y_start + im.shape[0]
            canvas_height_needed = max(canvas_height_needed, img_bottom)
        
        # 添加缓冲空间
        canvas_height_needed += 300
        
        # 确保画布尺寸是整数
        canvas_height_needed = int(canvas_height_needed)
        max_w = int(max_w)
        logger.info(f"创建画布: {canvas_height_needed}x{max_w}")
        panorama = np.zeros((canvas_height_needed, max_w, 3), dtype=np.float64)
        
        # 逐步融合图像
        current_end = 0
        for idx, (im, y_start) in enumerate(zip(images, offsets)):
            img_height, img_width = im.shape[:2]
            img_end = y_start + img_height
            
            logger.info(f"放置第 {idx+1}/{len(images)} 张图像: 位置[{y_start}:{img_end}]")
            
            # 检查画布边界
            if img_end > panorama.shape[0]:
                logger.warning(f"图像{idx}超出画布边界!")
                continue
            
            if idx == 0:
                # 第一张图像直接放置
                panorama[y_start:y_start + img_height, :img_width] = im.astype(np.float64)
                current_end = y_start + img_height
            else:
                # 后续图像使用融合
                try:
                    current_end = self._seamless_blend(
                        panorama, im, y_start, current_end, idx
                    )
                except Exception as e:
                    logger.error(f"图像{idx}融合失败: {e}")
                    # 备用方案：直接放置
                    panorama[y_start:y_start + img_height, :img_width] = im.astype(np.float64)
                    current_end = max(current_end, y_start + img_height)
        
        logger.info(f"所有图像放置完成，最终画布高度: {current_end}/{panorama.shape[0]}")
        
        # 保存总像素数
        self.total_pixels = current_end
        
        # 裁剪有效区域
        panorama = self._crop_valid_region(panorama, current_end)
        
        # 旋转并添加坐标轴
        panorama = self._rotate_and_add_axes(panorama, images)
        
        # 转换为uint8
        panorama_uint8 = np.clip(panorama, 0, 255).astype(np.uint8)
        
        return panorama_uint8
        
    def process(self, images: List[np.ndarray], output_path: Union[str, Path]) -> np.ndarray:
        """
        处理图像并生成全景图
        :param images: 图像列表
        :param output_path: 输出路径
        :return: 生成的全景图
        """
        # 生成全景图
        panorama_image = self.create_panorama(images)
        
        # 创建输出目录
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        # 保存全景图
        output_file = output_dir / "panorama.png"
        cv2.imwrite(str(output_file), panorama_image)
        logger.info(f"全景图已保存: {output_file}")
        
        return panorama_image
    
    def _calculate_variable_offsets(self, images: List[np.ndarray]) -> Tuple[List[int], List[int]]:
        """
        计算可变偏移量
        
        Args:
            images: 图像列表
            
        Returns:
            (偏移量列表, 相邻图像间偏移量列表)
        """
        offsets = [0]  # 第一张图像偏移量为0
        pair_dy = []
        
        for i in range(1, len(images)):
            # 根据帧索引设置不同的偏移量
            if i <= 10 or (50 <= i <= 59):
                # 前10帧和50-59帧的相对位移为0
                offset = 0
            else:
                # 其余帧使用默认偏移量
                offset = self.default_frame_offset
            
            # 记录偏移量
            offsets.append(offsets[-1] + offset)
            pair_dy.append(offset)
        
        logger.info(f"计算可变偏移量完成，总偏移: {offsets[-1]}像素")
        return offsets, pair_dy
    
    def _calculate_depth_positions(self, images: List[np.ndarray]):
        """
        计算每帧图像对应的深度位置
        
        Args:
            images: 图像列表
        """
        num_images = len(images)
        
        # 计算每帧的深度增量
        depth_increment = (self.total_depth_mm - self.initial_depth_mm) / (num_images - 1) if num_images > 1 else 0
        
        # 计算每帧的深度位置
        self.depth_positions_mm = [self.initial_depth_mm + i * depth_increment for i in range(num_images)]
        
        # 计算每像素对应的毫米数
        if num_images > 1 and self.offsets_data:
            total_pixels = self.offsets_data[-1]
            if total_pixels > 0:
                self.mm_per_pixel = (self.total_depth_mm - self.initial_depth_mm) / total_pixels
            else:
                self.mm_per_pixel = 1.0  # 默认值
        else:
            self.mm_per_pixel = 1.0  # 默认值
        
        logger.info(f"深度范围: {self.initial_depth_mm}mm - {self.total_depth_mm}mm")
        logger.info(f"每像素对应: {self.mm_per_pixel:.4f}mm")
    
    def _seamless_blend(self, panorama: np.ndarray, new_image: np.ndarray, 
                         y_start: int, current_end: int, idx: int) -> int:
        """
        无缝融合两张图像
        
        Args:
            panorama: 全景画布
            new_image: 新图像
            y_start: 新图像起始y坐标
            current_end: 当前画布有效区域结束位置
            idx: 图像索引
            
        Returns:
            更新后的画布有效区域结束位置
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
        
        logger.info(f"  图像{idx}重叠区域高度: {overlap_height}px")
        
        # 提取重叠区域
        canvas_overlap = panorama[overlap_start:overlap_end, :img_w]
        newimg_overlap = new_image[:overlap_height, :]
        
        # 创建融合掩码 (线性渐变)
        mask = self._create_mask(overlap_height, img_w)
        
        # 融合重叠区域
        blended_overlap = canvas_overlap * (1 - mask) + newimg_overlap * mask
        
        # 将融合后的重叠区域写回画布
        panorama[overlap_start:overlap_end, :img_w] = blended_overlap
        
        # 处理非重叠区域
        if img_end > current_end:
            non_overlap_start = current_end
            non_overlap_end = img_end
            non_overlap_height = non_overlap_end - non_overlap_start
            
            if non_overlap_height > 0:
                # 新图像的非重叠部分
                non_overlap_img = new_image[overlap_height:, :]
                
                # 写入画布
                panorama[non_overlap_start:non_overlap_end, :img_w] = non_overlap_img
        
        # 返回新的有效内容结束位置
        return max(current_end, img_end)
    
    def _create_mask(self, height: int, width: int) -> np.ndarray:
        """
        创建线性渐变掩码
        
        Args:
            height: 掩码高度
            width: 掩码宽度
            
        Returns:
            渐变掩码
        """
        # 创建从上到下渐变的掩码
        y = np.linspace(0, 1, height)  # 从上到下，权重从0到1
        mask = np.repeat(y[:, np.newaxis], width, axis=1)
        
        # 扩展为3通道
        return np.repeat(mask[:, :, np.newaxis], 3, axis=2)
    
    def _crop_valid_region(self, panorama: np.ndarray, current_end: int) -> np.ndarray:
        """
        裁剪有效区域
        
        Args:
            panorama: 全景图
            current_end: 有效区域结束位置
            
        Returns:
            裁剪后的全景图
        """
        # 裁剪底部未使用的空间
        return panorama[:current_end, :, :]
    
    def _rotate_and_add_axes(self, panorama: np.ndarray, images: List[np.ndarray]) -> np.ndarray:
        """
        旋转全景图并添加坐标轴
        
        Args:
            panorama: 全景图
            images: 图像列表
            
        Returns:
            处理后的全景图
        """
        # 转换为uint8用于OpenCV绘制
        panorama_vis = np.clip(panorama, 0, 255).astype(np.uint8)
        
        # 逆时针旋转90度
        rotated = cv2.rotate(panorama_vis, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        # 获取旋转后的尺寸
        height, width = rotated.shape[:2]
        
        # 设置边距
        bottom_margin = 100  # 底部边距（用于深度轴）
        left_margin = 250    # 左侧边距（增加左侧留白，从150改为250）
        right_margin = 50    # 右侧边距
        top_margin = 50      # 顶部边距
        
        # 创建扩展画布
        expanded_height = height + bottom_margin + top_margin
        expanded_width = width + left_margin + right_margin
        expanded = np.zeros((expanded_height, expanded_width, 3), dtype=np.uint8)
        
        # 填充背景色
        expanded.fill(0)  # 黑色背景
        
        # 将旋转后的图像放在扩展画布的中央
        expanded[top_margin:top_margin+height, left_margin:left_margin+width] = rotated
        
        # 设置字体和颜色
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.4
        thickness = 2
        
        # 添加深度轴（横轴）
        if self.enable_depth_axis:
            # 使用预设深度范围
            min_depth = self.initial_depth_mm
            max_depth = self.total_depth_mm
            
            # 绘制主轴线
            axis_y = expanded_height - bottom_margin // 2
            cv2.line(expanded, (left_margin, axis_y), (left_margin + width, axis_y), self.axis_color, 2)
            
            # 计算刻度间隔
            tick_interval_mm = self.depth_axis_tick_interval
            start_depth = int(min_depth / tick_interval_mm) * tick_interval_mm
            end_depth = int(max_depth / tick_interval_mm + 1) * tick_interval_mm
            
            # 计算深度到像素的映射
            def depth_to_pixel(d):
                return int(left_margin + (float(d) - float(min_depth)) / (float(max_depth) - float(min_depth)) * width)
            
            # 绘制刻度和标签
            for depth in np.arange(start_depth, end_depth + tick_interval_mm, tick_interval_mm):
                # 计算刻度在图像中的位置
                pixel_pos = depth_to_pixel(depth)
                
                # 确保刻度在有效范围内
                if left_margin <= pixel_pos <= left_margin + width:
                    # 绘制刻度线
                    cv2.line(expanded, (pixel_pos, axis_y - 10), (pixel_pos, axis_y + 10), 
                             self.axis_color, 2)
                    
                    # 绘制深度标签
                    label = f"{int(depth)}"
                    text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
                    text_x = pixel_pos - text_size[0] // 2
                    text_y = axis_y + 35
                    
                    cv2.putText(expanded, label, (text_x, text_y), font, 
                                font_scale, self.axis_color, thickness)
            
            # 添加深度轴标题 - 移至横轴最右侧上方，不遮挡文字
            depth_title = "Depth (mm)"
            title_size = cv2.getTextSize(depth_title, font, font_scale + 0.2, thickness + 1)[0]
            # 右对齐，位于轴线上方
            title_x = left_margin + width - title_size[0] - 10
            title_y = axis_y - 20
            
            cv2.putText(expanded, depth_title, (title_x, title_y), font, 
                        font_scale + 0.2, self.axis_color, thickness + 1)
        
        # 添加角度轴（纵轴）
        if self.enable_angle_axis:
            # 绘制主轴线
            axis_x = left_margin // 2
            cv2.line(expanded, (axis_x, top_margin), (axis_x, top_margin + height), 
                     self.axis_color, 2)
            
            # 计算角度范围：0-360度对应旋转后图像的高度
            angle_tick_interval = self.angle_axis_tick_interval
            
            # 绘制刻度和标签
            for angle in np.arange(0, 361, angle_tick_interval):
                # 计算刻度在图像中的y位置（映射到图像高度）
                ratio = angle / 360.0
                y_pos = int(top_margin + height - ratio * height)  # 从下到上数字依次增大
                
                # 确保刻度在有效范围内
                if top_margin <= y_pos <= top_margin + height:
                    # 绘制刻度线
                    cv2.line(expanded, (axis_x - 10, y_pos), (axis_x + 10, y_pos), 
                             self.axis_color, 2)
                    
                    # 绘制角度标签
                    label = f"{int(angle)}"
                    text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
                    text_x = axis_x - text_size[0] - 15
                    text_y = y_pos + 5
                    
                    cv2.putText(expanded, label, (text_x, text_y), font, 
                                font_scale, self.axis_color, thickness)
            
            # 添加角度轴标题 - 使用与stitch.py相同的方式
            angle_title = "Angle (degrees)"
            title_x = 20
            title_y = top_margin + 30
            
            # 使用普通水平文本而不是垂直文本，与stitch.py保持一致
            cv2.putText(expanded, angle_title, (title_x, title_y), font, 
                        font_scale + 0.2, self.axis_color, thickness + 1)
        
        # 添加图例 - 参考stitch.py的设置
        if self.show_legend:
            # 设置图例区域
            margin = 20  # 与图像边界的距离
            
            # 创建一个更大的画布以容纳图例
            new_expanded_height = expanded_height
            new_expanded_width = expanded_width + 120  # 进一步减小额外添加的宽度，从180改为120
            
            new_expanded = np.zeros((new_expanded_height, new_expanded_width, 3), dtype=np.uint8)
            # 复制原始扩展画布内容
            new_expanded[:expanded_height, :expanded_width] = expanded
            
            # 调整图例尺寸和位置
            self.legend_width = 400  # 保持宽度不变
            self.legend_height = 320  # 保持高度不变
            
            # 将图例放在右侧，适应缩小的留白
            x1 = expanded_width - 360  # 调整为新的右侧留白宽度
            y1 = top_margin + margin
            x2 = x1 + self.legend_width
            y2 = y1 + self.legend_height
            
            # 创建半透明覆盖层
            overlay = new_expanded.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), self.legend_bg_color, -1)
            cv2.addWeighted(overlay, self.legend_opacity, new_expanded, 1 - self.legend_opacity, 0, new_expanded)
            
            # 绘制边框
            cv2.rectangle(new_expanded, (x1, y1), (x2, y2), self.legend_text_color, 1)
            
            # 使用PIL绘制中文文本
            # 转换OpenCV图像到PIL图像
            pil_img = Image.fromarray(cv2.cvtColor(new_expanded, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)
            
            # 尝试加载中文字体，如果不可用则使用默认字体
            try:
                # 尝试使用系统字体
                font_size = int(20 * (font_scale + 0.4))
                pil_font = ImageFont.truetype("Arial Unicode.ttf", font_size)
            except IOError:
                try:
                    # 尝试使用另一个常见字体
                    pil_font = ImageFont.truetype("SimHei.ttf", font_size)
                except IOError:
                    # 使用默认字体
                    pil_font = ImageFont.load_default()
            
            # 标题
            draw.text((x1 + 10, y1 + 10), "图例", fill=tuple(reversed(self.legend_text_color)), font=pil_font)
            
            # 文本起始位置和行距
            text_x = x1 + 20
            text_y = y1 + 70
            line_height = 40  # 行高（增大）
            text_spacing = line_height
            
            # 文本内容
            font_size = int(18 * (font_scale + 0.2))
            try:
                pil_font = ImageFont.truetype("Arial Unicode.ttf", font_size)
            except IOError:
                try:
                    pil_font = ImageFont.truetype("SimHei.ttf", font_size)
                except IOError:
                    pil_font = ImageFont.load_default()
            
            # 1. 图像尺寸
            image_size_text = f"图像尺寸: {self.image_width}x{self.image_height}像素"
            draw.text((text_x, text_y), image_size_text, fill=tuple(reversed(self.legend_text_color)), font=pil_font)
            text_y += text_spacing
            
            # 2. 比例尺信息
            pixel_to_mm_ratio = self.mm_per_pixel
            min_depth = self.initial_depth_mm
            max_depth = self.total_depth_mm
            total_length_mm = max_depth - min_depth
            
            scale_text = f"比例尺: 1像素 = {pixel_to_mm_ratio:.4f} 毫米"
            draw.text((text_x, text_y), scale_text, fill=tuple(reversed(self.legend_text_color)), font=pil_font)
            text_y += text_spacing
            
            # 3. 总像素数
            pixels_text = f"总像素数: {self.total_pixels}"
            draw.text((text_x, text_y), pixels_text, fill=tuple(reversed(self.legend_text_color)), font=pil_font)
            text_y += text_spacing
            
            # 4. 管道总长
            pipe_length_text = f"管道总长: {total_length_mm:.2f} 毫米"
            draw.text((text_x, text_y), pipe_length_text, fill=tuple(reversed(self.legend_text_color)), font=pil_font)
            text_y += text_spacing + 10
            
            # 5. 绘制比例尺 - 放大比例尺和标签
            scale_length_mm = 50  # 比例尺长度(mm)
            # 计算比例尺长度对应的像素数
            scale_length_pixels = int(scale_length_mm / pixel_to_mm_ratio)
            
            # 确保比例尺不会太长
            if scale_length_pixels > self.legend_width - 40:
                scale_length_pixels = self.legend_width - 40
                scale_length_mm = scale_length_pixels * pixel_to_mm_ratio
            
            # 放大比例尺区域
            scale_x1 = text_x
            scale_x2 = scale_x1 + scale_length_pixels
            scale_y = text_y + 10  # 增加垂直空间
            
            # 在PIL上绘制比例尺线条
            draw.line([(scale_x1, scale_y), (scale_x2, scale_y)], fill=tuple(reversed(self.legend_text_color)), width=3)
            draw.line([(scale_x1, scale_y-8), (scale_x1, scale_y+8)], fill=tuple(reversed(self.legend_text_color)), width=2)
            draw.line([(scale_x2, scale_y-8), (scale_x2, scale_y+8)], fill=tuple(reversed(self.legend_text_color)), width=2)
            
            # 放大比例尺标签文字
            font_size = int(20 * (font_scale + 0.1))
            try:
                pil_font = ImageFont.truetype("Arial Unicode.ttf", font_size)
            except IOError:
                try:
                    pil_font = ImageFont.truetype("SimHei.ttf", font_size)
                except IOError:
                    pil_font = ImageFont.load_default()
                    
            draw.text(((scale_x1 + scale_x2) // 2 - 25, scale_y + 15), f"{scale_length_mm:.1f} 毫米", 
                      fill=tuple(reversed(self.legend_text_color)), font=pil_font)
            
            # 将PIL图像转回OpenCV格式
            new_expanded = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            # 使用新的扩展画布替换原来的
            expanded = new_expanded
        
        return expanded


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='展平图像全景拼接器')
    parser.add_argument('--data-dir', type=str, default='./data',
                        help='展平图像目录路径，默认为./data')
    parser.add_argument('--output-dir', type=str, default='./panorama_output',
                        help='输出全景图目录路径，默认为./panorama_output')
    parser.add_argument('--max-frames', type=int, default=None,
                        help='拼接的最大帧数，如果指定，则只拼接前N帧图像')
    parser.add_argument('--pipe-length', type=float, default=None,
                        help='管道总长度（毫米），如果不指定则使用默认值900mm')
    
    args = parser.parse_args()
    
    # 创建全景拼接器实例，如果指定了管道长度则传入
    panorama = PanoramaGenerator(pipe_length_mm=args.pipe_length)
    
    # 加载图像，如果指定了最大帧数则传入
    images = panorama.load_images(args.data_dir, args.max_frames)
    
    # 生成全景图
    panorama_image = panorama.create_panorama(images)
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 生成文件名，如果指定了max-frames或pipe-length则添加到文件名中
    output_filename = "panorama"
    
    # 如果指定了max-frames，添加帧数到文件名
    if args.max_frames is not None:
        output_filename += f"_frames{args.max_frames}"
        
    # 如果指定了pipe-length，添加长度到文件名
    if args.pipe_length is not None:
        output_filename += f"_length{int(args.pipe_length)}"
        
    output_filename += ".png"
    
    # 保存全景图
    output_path = output_dir / output_filename
    cv2.imwrite(str(output_path), panorama_image)
    logger.info(f"全景图已保存: {output_path}")
    
    logger.info("全景图生成完成")

if __name__ == "__main__":
    main() 