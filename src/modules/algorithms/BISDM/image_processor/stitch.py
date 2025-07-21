# -*- coding: utf-8 -*-
"""
工业内窥镜图像拼接处理器 - 增强版（支持相对位移可视化）
版本: v1.1 
日期: 2025-07-03
功能: 基于SIFT特征匹配和RANSAC的自动运动检测拼接算法
特点: 正确处理相机深入/退出运动，支持通用拼接任务，可视化相对位移
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Union
import time
from scipy.ndimage import gaussian_filter
from scipy import interpolate
import matplotlib.pyplot as plt
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    pass  # 如果导入失败，将在需要时处理


class StitchProcessor:
    """垂直图像拼接处理器（完全无缝版）- 增强版支持位移可视化

    改动要点：
    1. **超大融合区域**：使用图像高度50%作为融合区域
    2. **多重融合策略**：结合5种不同的融合方法
    3. **强力缝隙消除**：多级后处理消除任何残留缝隙
    4. **自适应融合**：根据图像特征自动调整融合参数
    5. **双向融合验证**：确保融合的对称性和一致性
    6. **NEW: 相对位移可视化**：在全景图上显示每个图像的相对位移信息
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 位移可视化相关变量
        self.offsets_data = []  # 存储偏移量数据用于可视化
        self.pair_dy_data = []  # 存储相对位移数据
        self.motion_analysis_data = {}  # 存储运动分析数据
        
        # 像素到毫米转换参数
        self.frame_interval = 10  # 关键帧间隔
        self.motion_speed_mm_s = 80.0  # 运动速度 80mm/s
        self.video_fps = 73.15  # 视频帧率
        self.mm_per_pixel = None  # 待计算的转换系数
        self.pair_dy_data_mm = []  # 存储相对位移数据（毫米）
        
        # 管道深度相关参数
        self.initial_depth_mm = getattr(config, "initial_depth_mm", 10.0)
        self.total_pipe_length_mm = getattr(config, "total_pipe_length_mm", 1000.0)
        self.enable_depth_axis = getattr(config, "enable_depth_axis", True)
        # 增加左侧边距从100到150像素
        self.depth_axis_width = getattr(config, "depth_axis_width", 150)
        self.depth_axis_tick_interval = getattr(config, "depth_axis_tick_interval", 10.0)
        self.depth_axis_color = getattr(config, "depth_axis_color", (255, 255, 255))
        self.depth_axis_bg_color = getattr(config, "depth_axis_bg_color", (0, 0, 0))
        self.depth_positions_mm = []  # 存储每个图像对应的管道深度位置
        
        # 展开角度相关参数
        self.enable_angle_axis = getattr(config, "enable_angle_axis", True)
        # 增加底部边距从60到80像素
        self.angle_axis_height = getattr(config, "angle_axis_height", 80)
        self.angle_axis_tick_interval = getattr(config, "angle_axis_tick_interval", 45.0)
        self.angle_axis_color = getattr(config, "angle_axis_color", (255, 255, 255))
        self.angle_axis_bg_color = getattr(config, "angle_axis_bg_color", (0, 0, 0))
        
        # 图例相关参数
        self.enable_legend = getattr(config, "enable_legend", True)
        self.legend_position = getattr(config, "legend_position", "top-right")
        self.legend_width = getattr(config, "legend_width", 300)
        self.legend_height = getattr(config, "legend_height", 120)
        self.legend_bg_color = getattr(config, "legend_bg_color", (0, 0, 0))
        self.legend_text_color = getattr(config, "legend_text_color", (255, 255, 255))
        self.legend_opacity = getattr(config, "legend_opacity", 0.7)
        self.use_english_labels = getattr(config, "use_english_labels", False)
        
        # 边距参数
        # 增加上方边距从50到70像素
        self.top_margin = 70  # 上方边距（像素）
        
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
        
        # 保存位移数据用于可视化
        self.offsets_data = offsets.copy()
        self.pair_dy_data = pair_dy.copy()
        
        # 计算像素到毫米的转换系数
        self._calculate_pixel_to_mm_conversion()
        
        # 转换相对位移数据为毫米
        self.pair_dy_data_mm = [d * self.mm_per_pixel for d in self.pair_dy_data]
        
        # 分析运动模式，获取运动开始的帧索引
        motion_analysis = self._analyze_motion_pattern(self.pair_dy_data)
        motion_start_idx = motion_analysis.get("motion_start", 0)
        self.logger.info(f"检测到运动开始帧索引: {motion_start_idx}")
        
        # ① 根据偏移量创建合适大小的画布
        max_w = max(im.shape[1] for im in images)
        
        # 计算画布高度：考虑所有图像的放置位置
        canvas_height_needed = 0
        for i, (im, y_start) in enumerate(zip(images, offsets)):
            img_bottom = y_start + im.shape[0]
            canvas_height_needed = max(canvas_height_needed, img_bottom)
        
        # 添加一些缓冲空间用于位移信息显示
        canvas_height_needed += 300  # 增加缓冲空间
        
        # 计算深度位置
        self._calculate_depth_positions()
        
        # 计算有效拼接长度（实际长度）- 去除起始重叠区域20mm
        self.effective_pipe_length_mm = self.total_pipe_length_mm - self.initial_depth_mm  # 380mm
        self.logger.info(f"管道有效拼接长度: {self.effective_pipe_length_mm}mm")
        
        # 计算像素到毫米的比例尺 - 基于有效拼接长度和全景图最大高度
        # 这将用于在中间过程中动态计算当前拼接实际长度
        if canvas_height_needed > 0:
            # 修正：不应该用canvas_height_needed而是用实际使用的高度（即最后一帧的偏移量加上帧高度）
            last_frame_offset = offsets[-1]
            last_frame_height = images[-1].shape[0]
            total_used_height = last_frame_offset + last_frame_height
            self.scale_mm_per_pixel = self.effective_pipe_length_mm / total_used_height
            self.logger.info(f"比例尺计算: 1像素 = {self.scale_mm_per_pixel:.4f}mm")
        
        # 深度坐标轴的偏移量，但不在这里扩充画布
        depth_axis_offset = 0
        if self.enable_depth_axis:
            depth_axis_offset = self.depth_axis_width
        
        self.logger.info(f"创建画布: {canvas_height_needed}x{max_w} (原累加高度: {sum(im.shape[0] for im in images)})")
        # 确保画布尺寸是整数
        canvas_height_needed = int(canvas_height_needed)
        max_w = int(max_w)
        panorama = np.zeros((canvas_height_needed, max_w, 3), dtype=np.float64)  # 使用float64提高精度

        # 创建保存拼接过程步骤的目录
        process_steps_dir = None
        if output_path:
            # 使用output_path下的04_stitched/process_steps目录保存中间步骤
            process_steps_dir = output_path / "04_stitched" / "process_steps"
            process_steps_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"将保存拼接过程中间步骤到: {process_steps_dir}")
            # 清除之前的处理步骤文件
            for f in process_steps_dir.glob("step_*.png"):
                f.unlink()
            self.logger.info("已清除之前的处理步骤文件")

        # ③ 逐步完美融合
        current_end = 0
        # 用于给保存的步骤图片编号
        save_step_count = 0
        
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
                
                # 只有当第一帧就是运动开始帧时才保存
                if motion_start_idx == 0 and process_steps_dir:
                    # 裁剪当前有效区域
                    current_panorama = panorama[:current_end, :, :].copy()
                    
                    # 计算当前拼接的实际物理长度
                    current_real_length = current_end * self.scale_mm_per_pixel
                    current_real_length_with_initial = self.initial_depth_mm + current_real_length
                    self.logger.info(f"  当前拼接实际物理长度: {current_real_length:.2f}mm (加上初始深度: {current_real_length_with_initial:.2f}mm)")
                    
                    # 旋转添加坐标轴以便更好观察
                    try:
                        rotated_panorama = self._rotate_and_add_axes(current_panorama, images[:idx+1], 
                                                                     is_final=False, 
                                                                     current_real_length=current_real_length)
                        current_panorama_uint8 = np.clip(rotated_panorama, 0, 255).astype(np.uint8)
                    except Exception as e:
                        self.logger.warning(f"无法为中间步骤添加坐标轴: {e}")
                        current_panorama_uint8 = np.clip(current_panorama, 0, 255).astype(np.uint8)
                    
                    # 使用三位数字格式保存，确保排序正确
                    step_filename = f"step_{save_step_count:03d}.png"
                    cv2.imwrite(str(process_steps_dir / step_filename), current_panorama_uint8)
                    self.logger.info(f"  保存拼接步骤 {save_step_count}: {step_filename}")
                    save_step_count += 1
            else:
                # 后续图像使用完美融合
                try:
                    current_end = self._perfect_seamless_blend(
                        panorama, im, y_start, current_end, idx, 0
                    )
                    self.logger.info(f"  图像{idx}融合完成，当前结束位置: {current_end}")
                except Exception as e:
                    self.logger.error(f"图像{idx}融合失败: {e}")
                    # 备用方案：直接放置
                    panorama[y_start:y_start + img_height, :img_width] = im.astype(np.float64)
                    current_end = max(current_end, y_start + img_height)
                    self.logger.info(f"  使用备用放置方案，当前结束位置: {current_end}")
            
                # 只在达到或超过运动开始帧时保存拼接状态
                if idx >= motion_start_idx and process_steps_dir:
                    # 裁剪当前有效区域
                    current_panorama = panorama[:current_end, :, :].copy()
                    
                    # 计算当前拼接的实际物理长度
                    current_real_length = current_end * self.scale_mm_per_pixel
                    current_real_length_with_initial = self.initial_depth_mm + current_real_length
                    self.logger.info(f"  当前拼接实际物理长度: {current_real_length:.2f}mm (加上初始深度: {current_real_length_with_initial:.2f}mm)")
                    
                    # 旋转添加坐标轴以便更好观察
                    try:
                        rotated_panorama = self._rotate_and_add_axes(current_panorama, images[:idx+1], 
                                                                     is_final=False, 
                                                                     current_real_length=current_real_length)
                        current_panorama_uint8 = np.clip(rotated_panorama, 0, 255).astype(np.uint8)
                    except Exception as e:
                        self.logger.warning(f"无法为中间步骤添加坐标轴: {e}")
                        current_panorama_uint8 = np.clip(current_panorama, 0, 255).astype(np.uint8)
                    
                    # 使用三位数字格式保存，确保排序正确
                    step_filename = f"step_{save_step_count:03d}.png"
                    cv2.imwrite(str(process_steps_dir / step_filename), current_panorama_uint8)
                    self.logger.info(f"  保存拼接步骤 {save_step_count}: {step_filename}")
                    save_step_count += 1
        
        self.logger.info(f"所有图像放置完成，最终画布使用高度: {current_end}/{panorama.shape[0]}")

        # ④ 强力后处理 - 多级缝隙消除
        panorama = self._crop_valid_region(panorama)
        # panorama = self._aggressive_seam_removal(panorama)
        # panorama = self._ultra_smooth_enhancement(panorama)
        
        # 旋转图像并添加新的坐标轴（横轴为深度，纵轴为角度）
        self.logger.info("旋转全景图并重新添加坐标轴")
        panorama = self._rotate_and_add_axes(panorama, images, is_final=True)
        
        # ⑤ 保存
        if output_path:
            output_path.mkdir(parents=True, exist_ok=True)
            # 转换回uint8保存
            panorama_uint8 = np.clip(panorama, 0, 255).astype(np.uint8)
            cv2.imwrite(str(output_path / "panorama.png"), panorama_uint8)
            
            if self.save_intermediate:
                np.save(str(output_path / "offsets.npy"), np.array(offsets))
                # NEW: 保存位移数据和创建统计图表
                self._save_displacement_analysis(output_path)

        return np.clip(panorama, 0, 255).astype(np.uint8)

    # ------------------------------------------------------------------
    #   NEW: 像素到毫米转换计算
    # ------------------------------------------------------------------
    def _calculate_pixel_to_mm_conversion(self):
        """基于运动速度计算像素到毫米的转换系数"""
        
        # 计算每个关键帧间隔的时间
        time_interval_s = self.frame_interval / self.video_fps
        
        # 计算理论上每个帧间隔应该移动的距离（毫米）
        theoretical_mm_per_frame = self.motion_speed_mm_s * time_interval_s
        
        # 计算实际观测到的平均像素位移（排除静止帧）
        non_zero_displacements = [abs(d) for d in self.pair_dy_data if abs(d) > 1.0]
        
        if not non_zero_displacements:
            # 如果没有明显位移，使用默认转换系数
            self.mm_per_pixel = 0.1
            self.logger.warning("No significant displacement detected, using default conversion: 0.1 mm/pixel")
        else:
            # 使用平均位移计算转换系数
            average_pixel_displacement = sum(non_zero_displacements) / len(non_zero_displacements)
            self.mm_per_pixel = theoretical_mm_per_frame / average_pixel_displacement
        
        self.logger.info(f"Pixel to mm conversion calculated:")
        self.logger.info(f"  Frame interval: {self.frame_interval} frames")
        self.logger.info(f"  Time interval: {time_interval_s:.4f} seconds")
        self.logger.info(f"  Motion speed: {self.motion_speed_mm_s} mm/s")
        self.logger.info(f"  Theoretical displacement: {theoretical_mm_per_frame:.2f} mm/frame")
        self.logger.info(f"  Conversion factor: {self.mm_per_pixel:.4f} mm/pixel")

    # ------------------------------------------------------------------
    #   NEW: 相对位移可视化方法
    # ------------------------------------------------------------------
    def _add_displacement_visualization(self, panorama: np.ndarray, images: List[np.ndarray]) -> np.ndarray:
        """在全景图上添加相对位移信息的可视化"""
        
        # 转换为uint8用于OpenCV绘制
        panorama_vis = np.clip(panorama, 0, 255).astype(np.uint8)
        
        # 设置文本参数
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        
        # 颜色定义
        text_color = (255, 255, 255)  # 白色文本
        bg_color = (0, 0, 0)  # 黑色背景
        arrow_color = (0, 255, 255)  # 黄色箭头
        frame_border_color = (255, 0, 0)  # 红色边框
        
        # 在每个图像位置添加位移信息
        for idx in range(len(images)):
            y_pos = self.offsets_data[idx]
            img_height = images[idx].shape[0]
            img_width = images[idx].shape[1]
            
            # 绘制图像边界框
            cv2.rectangle(panorama_vis, 
                         (0, y_pos), 
                         (img_width-1, y_pos + img_height-1), 
                         frame_border_color, 2)
            
            # 准备位移信息文本（同时显示像素和毫米）
            if idx == 0:
                displacement_text = f"Frame {idx}: Start (Position: {y_pos}px)"
                arrow_text = ""
            else:
                relative_displacement_px = self.pair_dy_data[idx-1]
                relative_displacement_mm = self.pair_dy_data_mm[idx-1]
                displacement_text = f"Frame {idx}: {relative_displacement_px:+.1f}px ({relative_displacement_mm:+.2f}mm)"
                
                # 准备箭头方向指示（使用英文字符）
                if relative_displacement_px > 0:
                    arrow_text = "v"  # 向下箭头
                elif relative_displacement_px < 0:
                    arrow_text = "^"  # 向上箭头
                else:
                    arrow_text = "="  # 无位移
            
            # 计算文本位置（图像左上角）
            text_x = 10
            text_y = y_pos + 30
            
            # 绘制文本背景
            text_size = cv2.getTextSize(displacement_text, font, font_scale, thickness)[0]
            cv2.rectangle(panorama_vis,
                         (text_x - 5, text_y - text_size[1] - 5),
                         (text_x + text_size[0] + 5, text_y + 5),
                         bg_color, -1)
            
            # 绘制位移信息文本
            cv2.putText(panorama_vis, displacement_text, 
                       (text_x, text_y), font, font_scale, text_color, thickness)
            
            # 绘制箭头指示
            if arrow_text and idx > 0:
                arrow_x = img_width - 50
                arrow_y = y_pos + 30
                
                # 绘制箭头背景
                cv2.circle(panorama_vis, (arrow_x, arrow_y), 20, bg_color, -1)
                cv2.circle(panorama_vis, (arrow_x, arrow_y), 20, arrow_color, 2)
                
                # 绘制箭头符号
                cv2.putText(panorama_vis, arrow_text, 
                           (arrow_x - 8, arrow_y + 8), font, 1.2, arrow_color, 3)
        
        # 添加总体统计信息（右下角）
        self._add_summary_statistics(panorama_vis)
        
        return panorama_vis.astype(np.float64)
    
    def _add_summary_statistics(self, panorama_vis: np.ndarray):
        """在全景图右下角添加总体统计信息"""
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        text_color = (255, 255, 255)
        bg_color = (0, 0, 0)
        
        # 计算统计数据（像素）
        total_displacement_px = sum(abs(d) for d in self.pair_dy_data)
        max_displacement_px = max(abs(d) for d in self.pair_dy_data) if self.pair_dy_data else 0
        avg_displacement_px = sum(self.pair_dy_data) / len(self.pair_dy_data) if self.pair_dy_data else 0
        
        # 计算统计数据（毫米）
        total_displacement_mm = sum(abs(d) for d in self.pair_dy_data_mm) if hasattr(self, 'pair_dy_data_mm') else 0
        max_displacement_mm = max(abs(d) for d in self.pair_dy_data_mm) if hasattr(self, 'pair_dy_data_mm') and self.pair_dy_data_mm else 0
        avg_displacement_mm = sum(self.pair_dy_data_mm) / len(self.pair_dy_data_mm) if hasattr(self, 'pair_dy_data_mm') and self.pair_dy_data_mm else 0
        
        # 运动方向分析
        positive_moves = sum(1 for d in self.pair_dy_data if d > 5)
        negative_moves = sum(1 for d in self.pair_dy_data if d < -5)
        static_moves = len(self.pair_dy_data) - positive_moves - negative_moves
        
        # 准备统计文本（同时显示像素和毫米数据）
        stats_lines = [
            "=== Displacement Stats ===",
            f"Total Frames: {len(self.offsets_data)}",
            f"Total: {total_displacement_px:.1f}px ({total_displacement_mm:.2f}mm)",
            f"Max: {max_displacement_px:.1f}px ({max_displacement_mm:.2f}mm)", 
            f"Avg: {avg_displacement_px:+.1f}px ({avg_displacement_mm:+.2f}mm)",
            f"Forward: {positive_moves} times",
            f"Backward: {negative_moves} times",
            f"Static: {static_moves} times",
            f"Conversion: {self.mm_per_pixel:.4f}mm/px" if hasattr(self, 'mm_per_pixel') and self.mm_per_pixel else "N/A"
        ]
        
        # 计算文本区域位置（右下角）
        h, w = panorama_vis.shape[:2]
        max_text_width = max(cv2.getTextSize(line, font, font_scale, thickness)[0][0] for line in stats_lines)
        total_text_height = len(stats_lines) * 25
        
        # 背景区域
        bg_x1 = w - max_text_width - 20
        bg_y1 = h - total_text_height - 20
        bg_x2 = w - 5
        bg_y2 = h - 5
        
        # 绘制背景
        cv2.rectangle(panorama_vis, (bg_x1, bg_y1), (bg_x2, bg_y2), bg_color, -1)
        cv2.rectangle(panorama_vis, (bg_x1, bg_y1), (bg_x2, bg_y2), (255, 255, 0), 2)
        
        # 绘制统计文本
        for i, line in enumerate(stats_lines):
            text_x = bg_x1 + 10
            text_y = bg_y1 + 20 + i * 25
            cv2.putText(panorama_vis, line, (text_x, text_y), font, font_scale, text_color, thickness)
    
    def _save_displacement_analysis(self, output_path: Path):
        """保存位移分析数据和创建统计图表"""
        
        try:
            # 设置matplotlib支持中文字体（避免字体警告）
            try:
                # 尝试设置中文字体
                plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
            except:
                # 如果设置失败，使用英文标题
                pass
            
            # 创建位移统计图表
            plt.figure(figsize=(12, 8))
            
            # 子图1：累积位移
            plt.subplot(2, 2, 1)
            frame_numbers = list(range(len(self.offsets_data)))
            plt.plot(frame_numbers, [float(x) for x in self.offsets_data], 'bo-', linewidth=2, markersize=6)
            plt.title('Cumulative Displacement', fontsize=12, fontweight='bold')
            plt.xlabel('Frame Number')
            plt.ylabel('Displacement (pixels)')
            plt.grid(True, alpha=0.3)
            
            # 子图2：相对位移
            plt.subplot(2, 2, 2)
            if self.pair_dy_data:
                relative_frames = list(range(1, len(self.pair_dy_data) + 1))
                colors = ['red' if d < 0 else 'green' if d > 0 else 'gray' for d in self.pair_dy_data]
                plt.bar(relative_frames, [float(x) for x in self.pair_dy_data], color=colors, alpha=0.7)
                plt.title('Relative Displacement', fontsize=12, fontweight='bold')
                plt.xlabel('Frame Number')
                plt.ylabel('Displacement (pixels)')
                plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                plt.grid(True, alpha=0.3)
            
            # 子图3：位移分布直方图
            plt.subplot(2, 2, 3)
            if self.pair_dy_data:
                plt.hist(self.pair_dy_data, bins=15, color='skyblue', alpha=0.7, edgecolor='black')
                plt.title('Displacement Distribution', fontsize=12, fontweight='bold')
                plt.xlabel('Displacement (pixels)')
                plt.ylabel('Frequency')
                plt.grid(True, alpha=0.3)
            
            # 子图4：运动模式分析
            plt.subplot(2, 2, 4)
            if self.pair_dy_data:
                positive_moves = sum(1 for d in self.pair_dy_data if d > 5)
                negative_moves = sum(1 for d in self.pair_dy_data if d < -5)
                static_moves = len(self.pair_dy_data) - positive_moves - negative_moves
                
                labels = ['Forward', 'Backward', 'Static']
                sizes = [positive_moves, negative_moves, static_moves]
                colors = ['lightgreen', 'lightcoral', 'lightgray']
                
                plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                plt.title('Movement Type Distribution', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = output_path / "displacement_analysis.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Displacement analysis chart saved: {chart_path}")
            
            # 保存原始数据
            import json
            import numpy as np
            
            # 将numpy类型转换为Python内置类型以支持JSON序列化
            def convert_numpy(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj
            
            # 递归转换所有numpy类型
            def convert_nested(data):
                if isinstance(data, dict):
                    return {k: convert_nested(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [convert_nested(v) for v in data]
                else:
                    return convert_numpy(data)
            
            analysis_data = {
                "cumulative_offsets": [convert_numpy(x) for x in self.offsets_data],
                "relative_displacements_px": [convert_numpy(x) for x in self.pair_dy_data],
                "relative_displacements_mm": [convert_numpy(x) for x in self.pair_dy_data_mm] if hasattr(self, 'pair_dy_data_mm') else [],
                "motion_analysis": convert_nested(self.motion_analysis_data),
                "conversion_factor": {
                    "mm_per_pixel": float(self.mm_per_pixel) if hasattr(self, 'mm_per_pixel') and self.mm_per_pixel else 0.0,
                    "frame_interval": self.frame_interval,
                    "motion_speed_mm_s": self.motion_speed_mm_s,
                    "video_fps": self.video_fps
                },
                "statistics": {
                    "total_frames": len(self.offsets_data),
                    "total_displacement_px": float(sum(abs(d) for d in self.pair_dy_data)),
                    "total_displacement_mm": float(sum(abs(d) for d in self.pair_dy_data_mm)) if hasattr(self, 'pair_dy_data_mm') else 0.0,
                    "max_displacement_px": float(max(abs(d) for d in self.pair_dy_data)) if self.pair_dy_data else 0.0,
                    "max_displacement_mm": float(max(abs(d) for d in self.pair_dy_data_mm)) if hasattr(self, 'pair_dy_data_mm') and self.pair_dy_data_mm else 0.0,
                    "avg_displacement_px": float(sum(self.pair_dy_data) / len(self.pair_dy_data)) if self.pair_dy_data else 0.0,
                    "avg_displacement_mm": float(sum(self.pair_dy_data_mm) / len(self.pair_dy_data_mm)) if hasattr(self, 'pair_dy_data_mm') and self.pair_dy_data_mm else 0.0,
                    "positive_moves": sum(1 for d in self.pair_dy_data if d > 5),
                    "negative_moves": sum(1 for d in self.pair_dy_data if d < -5),
                    "static_moves": sum(1 for d in self.pair_dy_data if abs(d) <= 5)
                }
            }
            
            json_path = output_path / "displacement_data.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=True, indent=2)
            
            self.logger.info(f"Displacement data saved: {json_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save displacement analysis: {e}")

    # ------------------------------------------------------------------
    #   ULTRA ENHANCED METHODS
    # ------------------------------------------------------------------
    # def _ultra_precise_offset_estimation(self, images):
    #     """先进的图像配准和偏移估计 - 基于RANSAC和全局优化"""
    #     self.logger.info("开始先进图像配准估计...")
        
    #     # 使用先进的图像配准方法
    #     transformations = self._estimate_global_transformations(images)
    #     offsets = self._extract_offsets_from_transformations(transformations, images)
        
    #     # 打印偏移量校验报告
    #     self.logger.info("\n=== 先进配准位移校验(累积偏移) ===")
    #     pair_dy = []
    #     for i in range(1, len(offsets)):
    #         dy = offsets[i] - offsets[i-1] if i > 0 else 0
    #         pair_dy.append(dy)
    #         self.logger.info(f"frame {i}: 累积={offsets[i]}px, 相对前帧=+{dy}px")
    #     self.logger.info("=" * 48)
        
    #     return offsets, pair_dy

    def _ultra_precise_offset_estimation(self, images):
        """先进的图像配准和偏移估计 - 基于RANSAC和全局优化，增加运动模型修正"""
        self.logger.info("开始先进图像配准估计...")
        
        # 1. 初始配准
        transformations = self._estimate_global_transformations(images)
        offsets = self._extract_offsets_from_transformations(transformations, images)
        
        # 2. 打印原始偏移量
        self.logger.info("\n=== 原始配准位移校验(累积偏移) ===")
        pair_dy = []
        for i in range(1, len(offsets)):
            dy = offsets[i] - offsets[i-1] if i > 0 else 0
            pair_dy.append(dy)
            self.logger.info(f"frame {i}: 累积={offsets[i]}px, 相对前帧=+{dy}px")
        self.logger.info("=" * 48)
        
        # 3. 运动模型修正（假设匀速运动）
        adjusted_offsets = self._adjust_offsets_for_constant_motion(offsets)
        
        # 4. 打印修正后偏移量
        self.logger.info("\n=== 修正后位移校验(匀速运动模型) ===")
        adjusted_dy = []
        for i in range(1, len(adjusted_offsets)):
            dy = adjusted_offsets[i] - adjusted_offsets[i-1] if i > 0 else 0
            adjusted_dy.append(dy)
            self.logger.info(f"frame {i}: 累积={adjusted_offsets[i]}px, 相对前帧=+{dy}px")
        self.logger.info("=" * 48)
        
        return adjusted_offsets, adjusted_dy

    def _adjust_offsets_for_constant_motion(self, offsets, static_threshold=5):
        """基于匀速运动假设修正偏移量，跳过初始静止帧"""
        if len(offsets) <= 1:
            return offsets
        
        # 1. 计算原始帧间位移
        deltas = [offsets[i] - offsets[i-1] for i in range(1, len(offsets))]
        
        # 2. 检测运动起始点（跳过初始静止帧）
        motion_start_idx = 0
        for i, dy in enumerate(deltas):
            if dy >= static_threshold:
                motion_start_idx = i
                break
        
        # 3. 如果全程静止，直接返回原数据
        if motion_start_idx == len(deltas):
            return offsets
        
        # 4. 仅对运动阶段计算中位数位移
        motion_deltas = deltas[motion_start_idx:]
        median_delta = np.median(motion_deltas)
        
        # 5. 修正累积偏移
        adjusted_offsets = offsets.copy()  # 初始保持原值
        for i in range(motion_start_idx + 1, len(offsets)):
            adjusted_offsets[i] = int(adjusted_offsets[i-1] + median_delta)
        
        return adjusted_offsets
    
   
    def _perfect_seamless_blend(self, panorama: np.ndarray, new_image: np.ndarray, 
                            y_start: int, current_end: int, idx: int, depth_axis_offset: int = 0) -> int:
        """
        增强版无缝融合实现，确保消除拼接细缝
        
        参数:
            panorama: 当前全景画布 (HxWx3)
            new_image: 待融合的新图像 (hxwx3)
            y_start: 新图像在画布上的起始Y坐标
            current_end: 当前画布的有效内容结束位置
            idx: 当前图像索引
            depth_axis_offset: 左侧深度坐标轴的宽度（现在不再使用，保留参数兼容性）
            
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
            self.logger.info(f"  图像{idx}无重叠区域，直接放置")
            return y_start + img_h
        
        self.logger.info(f"  图像{idx}重叠区域高度: {overlap_height}px")
        
        # 提取重叠区域（不再考虑深度坐标轴偏移）
        canvas_overlap = panorama[overlap_start:overlap_end, :img_w]
        newimg_overlap = new_image[:overlap_height, :]
        
        # 确保重叠区域有效（避免形状为(0,n,3)的数组）
        if canvas_overlap.shape[0] == 0 or newimg_overlap.shape[0] == 0:
            # 重叠区域为空，直接放置图像
            panorama[y_start:y_start+img_h, :img_w] = new_image
            self.logger.info(f"  图像{idx}重叠区域无效，直接放置")
            return y_start + img_h
        
        # 步骤1: 颜色一致性调整 (颜色匹配以保持连贯性)
        try:
            newimg_adjusted = self._match_histograms(newimg_overlap, canvas_overlap)
        except Exception as e:
            self.logger.warning(f"  直方图匹配失败，使用原始图像: {e}")
            newimg_adjusted = newimg_overlap
        
        # 步骤2: 生成高级融合掩码
        try:
            # 使用基于图像内容的自适应掩码
            mask = self._create_adaptive_mask(canvas_overlap, newimg_adjusted, overlap_height)
        except Exception as e:
            self.logger.warning(f"  创建自适应掩码失败，使用简单掩码: {e}")
            # 备用方案：使用简单线性掩码
        mask = self._create_simple_mask(overlap_height, img_w)
        
        # 步骤3: 多种融合方式尝试
        try:
            # 多波段融合 (更稳定可靠)
            blended_overlap = self._multiband_blend(canvas_overlap, newimg_adjusted, mask)
        except Exception as e:
            self.logger.warning(f"  多波段融合失败: {e}")
            # 最后备选：直接线性融合
            blended_overlap = canvas_overlap * (1 - mask) + newimg_adjusted * mask
            self.logger.info("  使用备用简单线性融合")
        
        # 步骤4: 边缘增强和平滑处理
        try:
            blended_overlap = self._enhance_seams(blended_overlap)
        except Exception as e:
            self.logger.warning(f"  边缘增强失败: {e}")
        
        # 将融合后的重叠区域写回画布
        panorama[overlap_start:overlap_end, :img_w] = blended_overlap
        
        # 处理非重叠区域
        if img_end > current_end:
            non_overlap_start = current_end
            non_overlap_end = img_end
            non_overlap_height = non_overlap_end - non_overlap_start
            
            # 如果存在非重叠区域，对边界进行特殊处理
            if non_overlap_height > 0:
                # 新图像的非重叠部分
                non_overlap_img = new_image[overlap_height:overlap_height+non_overlap_height, :]
                
                # 平滑边界过渡 (约10像素的过渡带)
                transition_zone = 10
                if overlap_height > 0 and non_overlap_height > transition_zone:
                    # 获取最后10行重叠区域和前10行非重叠区域
                    last_rows = blended_overlap[-transition_zone:].copy()
                    first_rows = non_overlap_img[:transition_zone].copy()
                    
                    # 创建过渡权重
                    transition_weights = np.linspace(0, 1, transition_zone)[:, np.newaxis, np.newaxis]
                    
                    # 平滑过渡
                    smoothed_transition = last_rows * (1 - transition_weights) + first_rows * transition_weights
                    non_overlap_img[:transition_zone] = smoothed_transition
                
                # 写入画布
                panorama[non_overlap_start:non_overlap_end, :img_w] = non_overlap_img
                self.logger.info(f"  添加非重叠区域: {non_overlap_height}px")
        
        # 返回新的有效内容结束位置
        return max(current_end, img_end)

    def _match_histograms(self, src: np.ndarray, ref: np.ndarray) -> np.ndarray:
        """ 增强版直方图匹配以确保颜色一致性 """
        matched = np.zeros_like(src)
        
        # 对每个通道分别进行直方图匹配
        for ch in range(3):
            src_hist, _ = np.histogram(src[..., ch].flatten(), 256, (0, 256), density=True)
            ref_hist, _ = np.histogram(ref[..., ch].flatten(), 256, (0, 256), density=True)
            
            # 计算累积分布函数
            src_cdf = src_hist.cumsum()
            if src_cdf[-1] > 0:  # 防止除零错误
                src_cdf = 255 * src_cdf / src_cdf[-1]  # 归一化到0-255
            
            ref_cdf = ref_hist.cumsum()
            if ref_cdf[-1] > 0:  # 防止除零错误
                ref_cdf = 255 * ref_cdf / ref_cdf[-1]  # 归一化到0-255
            
            # 创建映射函数
            interp_values = np.interp(src[..., ch].flatten(), np.arange(256), src_cdf)
            interp_values = np.interp(interp_values, ref_cdf, np.arange(256))
            
            # 应用映射
            matched[..., ch] = interp_values.reshape(src[..., ch].shape)
        
        return matched.astype(np.float64)

    def _create_adaptive_mask(self, img1: np.ndarray, img2: np.ndarray, height: int) -> np.ndarray:
        """ 创建基于图像内容的自适应融合掩码 """
        width = img1.shape[1]
        
        # 转换为灰度图
        gray1 = cv2.cvtColor(img1.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        
        # 计算梯度 (Sobel算子)
        sobelx1 = cv2.Sobel(gray1, cv2.CV_64F, 1, 0, ksize=3)
        sobely1 = cv2.Sobel(gray1, cv2.CV_64F, 0, 1, ksize=3)
        sobelx2 = cv2.Sobel(gray2, cv2.CV_64F, 1, 0, ksize=3)
        sobely2 = cv2.Sobel(gray2, cv2.CV_64F, 0, 1, ksize=3)
        
        # 计算梯度幅值
        gradient1 = np.sqrt(sobelx1**2 + sobely1**2)
        gradient2 = np.sqrt(sobelx2**2 + sobely2**2)
        
        # 基于梯度创建权重掩码 (强梯度区域应该保持原样)
        weight = gradient1 < gradient2
        
        # 使用形态学处理平滑掩码
        weight_smooth = cv2.GaussianBlur(weight.astype(np.float64), (15, 15), 0)
        
        # 基础线性权重 (垂直方向渐变)
        base_weights = np.linspace(1, 0, height)[:, np.newaxis]
        base_weights = np.repeat(base_weights, width, axis=1)
        
        # 结合基础线性权重和梯度权重
        combined_weight = base_weights * 0.7 + weight_smooth * 0.3
        
        # 扩展为3通道
        mask = np.repeat(combined_weight[:, :, np.newaxis], 3, axis=2)
        
        return np.clip(mask, 0, 1)

    def _multiband_blend(self, img1: np.ndarray, img2: np.ndarray, mask: np.ndarray, levels: int = 4) -> np.ndarray:
        """ 多波段金字塔融合 (拉普拉斯金字塔) """
        # 确保图像格式一致
        img1 = img1.astype(np.float64)
        img2 = img2.astype(np.float64)
        
        # 创建高斯金字塔
        def build_gaussian_pyramid(img, levels):
            pyramid = [img]
            for i in range(levels-1):
                img = cv2.pyrDown(img)
                pyramid.append(img)
            return pyramid
        
        # 创建拉普拉斯金字塔
        def build_laplacian_pyramid(gaussian_pyramid, levels):
            laplacian_pyramid = []
            for i in range(levels-1):
                size = (gaussian_pyramid[i].shape[1], gaussian_pyramid[i].shape[0])
                laplacian = gaussian_pyramid[i] - cv2.resize(cv2.pyrUp(gaussian_pyramid[i+1]), size)
                laplacian_pyramid.append(laplacian)
            laplacian_pyramid.append(gaussian_pyramid[-1])  # 添加最高层
            return laplacian_pyramid
        
        # 构建各个金字塔
        gaussian_pyramid_1 = build_gaussian_pyramid(img1, levels)
        gaussian_pyramid_2 = build_gaussian_pyramid(img2, levels)
        gaussian_pyramid_mask = build_gaussian_pyramid(mask, levels)
        
        laplacian_pyramid_1 = build_laplacian_pyramid(gaussian_pyramid_1, levels)
        laplacian_pyramid_2 = build_laplacian_pyramid(gaussian_pyramid_2, levels)
        
        # 融合拉普拉斯金字塔
        laplacian_pyramid_blended = []
        for i in range(levels):
            # 调整掩码大小以匹配当前层
            current_mask = gaussian_pyramid_mask[i]
            current_lap1 = laplacian_pyramid_1[i]
            current_lap2 = laplacian_pyramid_2[i]
            
            # 融合当前层
            blended = current_lap1 * (1 - current_mask) + current_lap2 * current_mask
            laplacian_pyramid_blended.append(blended)
        
        # 重建图像
        blended_image = laplacian_pyramid_blended[-1]
        for i in range(levels-2, -1, -1):
            size = (laplacian_pyramid_blended[i].shape[1], laplacian_pyramid_blended[i].shape[0])
            blended_image = cv2.resize(cv2.pyrUp(blended_image), size) + laplacian_pyramid_blended[i]
        
        return np.clip(blended_image, 0, 255)

    def _enhance_seams(self, img: np.ndarray) -> np.ndarray:
        """ 增强融合边缘和缝隙 """
        # 使用双边滤波保留边缘细节同时平滑缝隙
        img_uint8 = np.clip(img, 0, 255).astype(np.uint8)
        filtered = cv2.bilateralFilter(img_uint8, 5, 35, 35)
        
        # 结合原始图像和滤波结果 (保留更多细节)
        enhanced = cv2.addWeighted(img_uint8, 0.7, filtered, 0.3, 0)
        
        return enhanced.astype(np.float64)

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
        
        # 保存运动分析数据用于可视化
        self.motion_analysis_data = motion_analysis
        
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


    def _crop_valid_region(self, panorama: np.ndarray) -> np.ndarray:
        """剪裁掉全景图中的无效区域（例如全黑区域）"""
        if panorama is None:
            # 返回一个空数组而不是None
            return np.zeros((1, 1, 3), dtype=panorama.dtype)
            
        # 计算非零区域的边界
        gray = cv2.cvtColor(np.clip(panorama, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY) if len(panorama.shape) == 3 else np.clip(panorama, 0, 255).astype(np.uint8)
        
        # 找到非零区域的边界
        rows = np.any(gray, axis=1)
        cols = np.any(gray, axis=0)
        
        try:
            # 转换为整数索引
            rows_idx = np.where(rows)[0]
            cols_idx = np.where(cols)[0]
            
            if len(rows_idx) > 0 and len(cols_idx) > 0:
                min_row, max_row = int(rows_idx.min()), int(rows_idx.max())
                min_col, max_col = int(cols_idx.min()), int(cols_idx.max())
                
                # 确保裁剪区域有效
                if min_row < max_row and min_col < max_col:
                    return panorama[min_row:max_row+1, min_col:max_col+1]
        except Exception as e:
            self.logger.error(f"剪裁区域计算错误: {e}")
            
        return panorama

    # ------------------------------------------------------------------
    #   NEW: 深度坐标轴相关方法
    # ------------------------------------------------------------------
    def _calculate_depth_positions(self):
        """基于位移数据计算管道深度位置（毫米）"""
        if not hasattr(self, 'offsets_data') or not self.offsets_data:
            self.logger.warning("无位移数据，无法计算深度位置")
            return
        
        # 计算全景图总高度（像素）
        if len(self.offsets_data) == 0:
            return
            
        # 获取最后一个偏移量和对应图像高度来估计全景图总高度
        # 这里假设图像高度相同，如果不同，需要修改逻辑
        total_height_pixels = 0
        if hasattr(self, 'offsets_data') and self.offsets_data:
            total_height_pixels = max(self.offsets_data)
        
        # 计算像素到毫米的比例尺 - 基于管道总长度和全景图高度
        # 注意：这里不再使用之前基于运动速度的计算方法
        if total_height_pixels > 0:
            # 管道总长度减去初始深度，得到全景图覆盖的管道长度
            pipe_length_covered = self.total_pipe_length_mm - self.initial_depth_mm
            # 计算每像素对应的毫米数
            self.mm_per_pixel = pipe_length_covered / total_height_pixels
            self.logger.info(f"基于管道总长度计算比例尺: 1像素 = {self.mm_per_pixel:.4f}mm")
        else:
            # 如果无法计算，使用默认值
            self.mm_per_pixel = 0.1
            self.logger.warning("无法计算像素到毫米的比例尺，使用默认值: 0.1 mm/pixel")
        
        # 计算各帧深度位置
        depth_positions = []
        for offset in self.offsets_data:
            # 确保偏移是整数
            offset = int(offset)
            # 计算深度位置 - 初始深度加上偏移对应的毫米数
            depth_mm = self.initial_depth_mm + offset * self.mm_per_pixel
            depth_positions.append(depth_mm)
            
        self.depth_positions_mm = depth_positions
        self.logger.info(f"计算深度位置: 从 {min(depth_positions):.1f}mm 到 {max(depth_positions):.1f}mm")

    def _add_depth_axis(self, panorama: np.ndarray, depth_axis_offset: int) -> np.ndarray:
        """在全景图左侧和上方添加深度坐标轴，先扩充左侧和上方空白像素再添加坐标轴"""
        if depth_axis_offset == 0:
            return panorama
        
        # 转换为uint8用于OpenCV绘制
        panorama_vis = np.clip(panorama, 0, 255).astype(np.uint8)
        
        # 获取原图尺寸
        height, width = panorama_vis.shape[:2]
        
        # 上方扩充的高度（像素）使用已定义的top_margin
        
        # 创建扩充后的画布（左侧和上方添加空白）
        expanded_height = int(height + self.top_margin)
        expanded_width = int(width + depth_axis_offset)
        expanded_panorama = np.zeros((expanded_height, expanded_width, 3), dtype=np.uint8)
        
        # 填充左侧和上方坐标轴区域为背景色
        expanded_panorama[:, :depth_axis_offset] = self.depth_axis_bg_color  # 左侧
        expanded_panorama[:self.top_margin, :] = self.depth_axis_bg_color  # 上方
        
        # 将原图放在右下角
        expanded_panorama[self.top_margin:, depth_axis_offset:] = panorama_vis
        
        # 计算深度范围
        if not self.depth_positions_mm:
            return expanded_panorama.astype(np.float64)
        
        min_depth = min(self.depth_positions_mm)
        max_depth = max(self.depth_positions_mm)
        depth_range = max_depth - min_depth
        
        if depth_range == 0:
            return expanded_panorama.astype(np.float64)
        
        # 计算坐标轴参数
        axis_height = height  # 使用原图高度
        # 增加坐标轴与边缘的距离
        axis_x = depth_axis_offset - 30  # 坐标轴主线位置
        
        # 绘制主坐标轴线
        cv2.line(expanded_panorama, (axis_x, self.top_margin), (axis_x, self.top_margin + axis_height), self.depth_axis_color, 2)
        
        # 绘制刻度和标签
        font = cv2.FONT_HERSHEY_SIMPLEX
        # 增大字体与横轴一致
        font_scale = 0.7
        # 增加线条粗细与横轴一致
        thickness = 2
        
        # 计算刻度间隔
        tick_interval_mm = self.depth_axis_tick_interval
        start_depth = int(min_depth / tick_interval_mm) * tick_interval_mm
        
        for depth_mm in np.arange(start_depth, max_depth + tick_interval_mm, tick_interval_mm):
            if depth_mm < min_depth or depth_mm > max_depth:
                continue
            
            # 计算在画布上的位置
            ratio = (depth_mm - min_depth) / depth_range
            y_pos = int(ratio * axis_height) + self.top_margin
            
            # 绘制刻度线，增加长度与横轴一致
            cv2.line(expanded_panorama, (axis_x - 12, y_pos), (axis_x, y_pos), self.depth_axis_color, 2)
            
            # 绘制深度标签
            label = f"{depth_mm:.0f}"
            text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
            # 增加文字与刻度线的距离
            text_x = axis_x - text_size[0] - 20
            text_y = y_pos + 5
            
            cv2.putText(expanded_panorama, label, (text_x, text_y), font, font_scale, self.depth_axis_color, thickness)
        
        # 添加单位标签 (使用英文避免乱码)
        unit_label = "Depth (mm)"
        # 增大单位标签字体与横轴一致
        text_size = cv2.getTextSize(unit_label, font, font_scale + 0.2, thickness + 1)[0]
        text_x = (depth_axis_offset - text_size[0]) // 2
        text_y = self.top_margin // 2 + 5  # 放置在上方空白区域的中部
        
        # 绘制单位标签背景
        cv2.rectangle(expanded_panorama, (text_x - 5, text_y - 20), (text_x + text_size[0] + 5, text_y + 5), 
                     self.depth_axis_bg_color, -1)
        cv2.putText(expanded_panorama, unit_label, (text_x, text_y), font, font_scale + 0.2, 
                   self.depth_axis_color, thickness + 1)
        
        return expanded_panorama.astype(np.float64)

    def _add_depth_visualization(self, panorama: np.ndarray, images: List[np.ndarray], depth_axis_offset: int) -> np.ndarray:
        """在全景图上添加简化的深度信息可视化（仅保留坐标轴指示器）"""
        
        # 转换为uint8用于OpenCV绘制
        panorama_vis = np.clip(panorama, 0, 255).astype(np.uint8)
        
        # 颜色定义
        depth_indicator_color = (0, 255, 255)  # 黄色深度指示器
        
        # 获取顶部边距
        top_margin = getattr(self, 'top_margin', 0)  # 如果属性不存在则默认为0
        
        # 仅在坐标轴上添加深度指示器，不显示文本和边框
        if self.enable_depth_axis and depth_axis_offset > 0 and self.depth_positions_mm:
            min_depth = min(self.depth_positions_mm)
            max_depth = max(self.depth_positions_mm)
            depth_range = max_depth - min_depth
            
            if depth_range > 0:
                for idx in range(len(images)):
                    if idx < len(self.depth_positions_mm):
                        y_pos = self.offsets_data[idx]
                        img_height = images[idx].shape[0]
                        depth_mm = self.depth_positions_mm[idx]
                        
                        # 计算在坐标轴上的位置（考虑顶部边距）
                        ratio = (depth_mm - min_depth) / depth_range
                        axis_y = int(ratio * (panorama_vis.shape[0] - top_margin)) + top_margin
                        axis_x = depth_axis_offset - 20
                        
                        # 绘制深度指示点（更小更简洁）
                        cv2.circle(panorama_vis, (axis_x, axis_y), 3, depth_indicator_color, -1)
                        cv2.circle(panorama_vis, (axis_x, axis_y), 3, (255, 255, 255), 1)
                        
                        # 绘制简化的连接线到图像中心（注意图像已向右移动了depth_axis_offset个像素，向下移动了top_margin个像素）
                        cv2.line(panorama_vis, (axis_x + 3, axis_y), 
                                (depth_axis_offset, top_margin + y_pos + img_height // 2), depth_indicator_color, 1)
        
        return panorama_vis.astype(np.float64)

    def _add_angle_axis(self, panorama_vis: np.ndarray, depth_axis_offset: int) -> np.ndarray:
        """在全景图底部添加角度坐标轴（横坐标：0-360度），并扩充四周空白"""
        if not self.enable_angle_axis:
            return panorama_vis
        
        # 转换为 uint8 用于 OpenCV 绘制
        panorama_vis = np.clip(panorama_vis, 0, 255).astype(np.uint8)
        height, width = panorama_vis.shape[:2]
        angle_axis_offset = self.angle_axis_height
        
        # 定义右侧留白（增加到70像素）
        right_margin = 70
        
        # 扩展图像尺寸（底部和右侧添加空白）
        expanded_width = int(width + right_margin)
        expanded_height = int(height + angle_axis_offset)
        expanded_panorama = np.zeros((expanded_height, expanded_width, 3), dtype=np.uint8)
        
        # 将原图复制到新画布的左上角
        expanded_panorama[:height, :width] = panorama_vis
        
        # 在扩展后的图像底部绘制角度坐标轴背景
        cv2.rectangle(expanded_panorama, (0, height), (expanded_width, expanded_height), 
                    self.angle_axis_bg_color, -1)
        
        # 绘制主轴线（水平线），从 depth_axis_offset 到原图宽度（不包含右侧空白）
        axis_y = height + angle_axis_offset // 2
        cv2.line(expanded_panorama, (depth_axis_offset, axis_y), (width, axis_y), 
                self.angle_axis_color, 2)
        
        # 计算角度范围：0-360 度对应原图的全景宽度（不包含右侧空白）
        panorama_width = width - depth_axis_offset
        
        # 绘制刻度和标签
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        
        for angle in np.arange(0, 361, self.angle_axis_tick_interval):
            # 计算刻度在图像中的 x 位置（映射到原图宽度）
            tick_x = int(depth_axis_offset + (angle / 360.0) * panorama_width)
            
            # 确保刻度在有效范围内（不进入右侧空白区）
            if depth_axis_offset <= tick_x <= width:
                # 绘制刻度线
                tick_start_y = axis_y - 12
                tick_end_y = axis_y + 12
                cv2.line(expanded_panorama, (tick_x, tick_start_y), (tick_x, tick_end_y), 
                        self.angle_axis_color, thickness)
                
                # 使用 Unicode 转义序列显示度数符号
                label = f"{int(angle)}"
                text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
                text_x = tick_x - text_size[0] // 2
                # 增加文字与刻度线的距离
                text_y = tick_end_y + 25
                
                # 确保文字不超出边界
                if text_x >= 0 and (text_x + text_size[0]) <= expanded_width:
                    cv2.putText(expanded_panorama, label, (text_x, text_y), font, 
                            font_scale, self.angle_axis_color, thickness)
        
        # 添加单位标签（居中在原图区域）
        unit_label = "Angle (degrees)"
        text_size = cv2.getTextSize(unit_label, font, font_scale + 0.2, thickness + 1)[0]
        # 调整单位标签位置，避免与数字重叠
        text_x = width - text_size[0] - 30
        text_y = height + angle_axis_offset - 20
        
        # 绘制单位标签背景
        cv2.rectangle(expanded_panorama, (text_x - 5, text_y - 15), (text_x + text_size[0] + 5, text_y + 5), 
                    self.angle_axis_bg_color, -1)
        cv2.putText(expanded_panorama, unit_label, (text_x, text_y), font, 
                font_scale + 0.2, self.angle_axis_color, thickness + 1)
        
        return expanded_panorama.astype(np.float64)

    def _add_legend(self, panorama: np.ndarray) -> np.ndarray:
        """
        在全景图上添加图例，包括像素值、孔道长度和比例尺
        支持中英文切换，解决中文乱码问题
        """
        # 如果禁用图例，直接返回
        if not self.enable_legend:
            return panorama
            
        # 转换为uint8用于OpenCV绘制
        panorama_vis = np.clip(panorama, 0, 255).astype(np.uint8)
        
        # 获取图像尺寸
        height, width = panorama_vis.shape[:2]
        
        # 设置图例区域
        legend_width = self.legend_width
        legend_height = self.legend_height
        margin = 20  # 与图像边界的距离
        
        # 根据配置的位置计算图例坐标
        if self.legend_position == "top-right":
            x1 = width - legend_width - margin
            y1 = self.top_margin + margin
        elif self.legend_position == "top-left":
            x1 = margin
            y1 = self.top_margin + margin
        elif self.legend_position == "bottom-right":
            x1 = width - legend_width - margin
            y1 = height - legend_height - margin
        elif self.legend_position == "bottom-left":
            x1 = margin
            y1 = height - legend_height - margin
        else:  # 默认右上角
            x1 = width - legend_width - margin
            y1 = self.top_margin + margin
            
        x2 = x1 + legend_width
        y2 = y1 + legend_height
        
        # 绘制图例背景（半透明）
        overlay = panorama_vis.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), self.legend_bg_color, -1)
        cv2.addWeighted(overlay, self.legend_opacity, panorama_vis, 1 - self.legend_opacity, 0, panorama_vis)
        
        # 绘制图例边框
        cv2.rectangle(panorama_vis, (x1, y1), (x2, y2), self.legend_text_color, 1)
        
        # 计算关键信息
        if self.depth_positions_mm:
            min_depth = min(self.depth_positions_mm)
            max_depth = max(self.depth_positions_mm)
            total_length_mm = max_depth - min_depth
        else:
            total_length_mm = 0
            
        # 计算像素到毫米的比例尺
        pixel_to_mm_ratio = self.mm_per_pixel if self.mm_per_pixel else 0.1
        
        # 计算图像实际尺寸 - 旋转后宽高互换
        original_width = height  # 旋转后，原高度变为宽度
        original_height = width  # 旋转后，原宽度变为高度
        
        # 设置文本内容（根据语言选择）
        if self.use_english_labels:
            # 英文标签
            image_size_text = f"Image Size: {original_width} x {original_height} px"
            pipe_length_text = f"Pipe Length: {self.total_pipe_length_mm:.2f} mm"
            scale_text = f"Scale: 1px = {pixel_to_mm_ratio:.4f} mm"
            pixels_per_cm = 10.0 / pixel_to_mm_ratio if pixel_to_mm_ratio > 0 else 100
            scale_bar_text = f"{10.0} mm = {pixels_per_cm:.1f} px"
        else:
            # 中文标签
            image_size_text = f"图像尺寸: {original_width} × {original_height} 像素"
            pipe_length_text = f"管道总长: {self.total_pipe_length_mm:.2f} mm"
            scale_text = f"比例尺: 1像素 = {pixel_to_mm_ratio:.4f} mm"
            pixels_per_cm = 10.0 / pixel_to_mm_ratio if pixel_to_mm_ratio > 0 else 100
            scale_bar_text = f"10 mm = {pixels_per_cm:.1f} 像素"
        
        # 尝试使用PIL渲染（支持中文）
        try:
            # 确保PIL库可用
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建PIL图像
            pil_img = Image.fromarray(panorama_vis)
            draw = ImageDraw.Draw(pil_img)
            
            # 尝试加载字体
            font = None
            font_size = 16
            
            # 通用字体搜索路径（优先尝试支持中文的字体）
            font_paths = [
                # macOS字体
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
                # Windows字体
                "C:/Windows/Fonts/msyh.ttf",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "C:/Windows/Fonts/simkai.ttf",  # 楷体
                # Linux字体
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/truetype/arphic/uming.ttc"
            ]
            
            # 尝试加载字体
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, font_size)
                    self.logger.info(f"成功加载字体: {path}")
                    break
                except Exception:
                    continue
            
            # 如果找不到支持中文的字体但启用了中文标签，切换到英文
            if font is None and not self.use_english_labels:
                self.logger.warning("未找到支持中文的字体，自动切换为英文标签")
                # 切换到英文标签
                image_size_text = f"Image Size: {original_width} x {original_height} px"
                pipe_length_text = f"Pipe Length: {self.total_pipe_length_mm:.2f} mm"
                scale_text = f"Scale: 1px = {pixel_to_mm_ratio:.4f} mm"
                
                # 再次尝试加载常见英文字体
                english_font_paths = [
                    "/System/Library/Fonts/Helvetica.ttc",
                    "C:/Windows/Fonts/arial.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                ]
                
                for path in english_font_paths:
                    try:
                        font = ImageFont.truetype(path, font_size)
                        self.logger.info(f"加载英文字体: {path}")
                        break
                    except Exception:
                        continue
            
            # 如果仍然找不到字体，使用默认字体
            if font is None:
                self.logger.warning("使用默认字体")
                font = ImageFont.load_default()
            
            # 绘制文本
            line_height = 25
            text_x = x1 + 10
            text_y = y1 + 10
            
            # 1. 图像尺寸
            draw.text((text_x, text_y), image_size_text, fill=tuple(self.legend_text_color), font=font)
            text_y += line_height
            
            # 2. 孔道长度
            draw.text((text_x, text_y), pipe_length_text, fill=tuple(self.legend_text_color), font=font)
            text_y += line_height
            
            # 3. 比例尺文本
            draw.text((text_x, text_y), scale_text, fill=tuple(self.legend_text_color), font=font)
            text_y += line_height
            
            # 将PIL图像转回OpenCV格式
            panorama_vis = np.array(pil_img)
            
            # 4. 绘制视觉比例尺
            # 直接使用pixels_per_cm作为比例尺长度（10mm对应的像素数）
            pixels_per_cm = 10.0 / pixel_to_mm_ratio if pixel_to_mm_ratio > 0 else 100
            scale_length_pixels = int(pixels_per_cm)
            scale_length_mm = 10.0  # 固定为10mm
            
            # 调整比例尺长度，确保在合理范围内
            if scale_length_pixels > legend_width - 30:  # 确保比例尺不超出图例宽度
                scale_length_pixels = legend_width - 30
                scale_length_mm = scale_length_pixels * pixel_to_mm_ratio
            elif scale_length_pixels < 50:
                scale_length_pixels = 50
                scale_length_mm = scale_length_pixels * pixel_to_mm_ratio
            
            scale_x1 = text_x
            scale_x2 = scale_x1 + scale_length_pixels
            scale_y = text_y + 10
            
            # 绘制比例尺线
            cv2.line(panorama_vis, (scale_x1, scale_y), (scale_x2, scale_y), self.legend_text_color, 2)
            cv2.line(panorama_vis, (scale_x1, scale_y-5), (scale_x1, scale_y+5), self.legend_text_color, 1)
            cv2.line(panorama_vis, (scale_x2, scale_y-5), (scale_x2, scale_y+5), self.legend_text_color, 1)
            
            # 绘制比例尺标签
            scale_label = f"{scale_length_mm:.1f} mm"
            # 重新创建PIL图像绘制最后的标签
            pil_img = Image.fromarray(panorama_vis)
            draw = ImageDraw.Draw(pil_img)
            draw.text(((scale_x1 + scale_x2) // 2 - 20, scale_y + 10), scale_label, 
                    fill=tuple(self.legend_text_color), font=font)
            
            # 最终转回OpenCV格式
            panorama_vis = np.array(pil_img)
            
        except Exception as e:
            # 如果PIL渲染失败，使用OpenCV渲染（仅支持英文）
            self.logger.error(f"PIL渲染失败，使用OpenCV渲染英文: {e}")
            
            # OpenCV英文渲染
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            line_height = 25
            
            text_x = x1 + 10
            text_y = y1 + 20
            
            # 使用英文文本
            cv2.putText(panorama_vis, f"Image Size: {original_width} x {original_height} px", 
                       (text_x, text_y), font, font_scale, self.legend_text_color, thickness)
            text_y += line_height
            
            cv2.putText(panorama_vis, f"Pipe Length: {self.total_pipe_length_mm:.2f} mm", 
                       (text_x, text_y), font, font_scale, self.legend_text_color, thickness)
            text_y += line_height
            
            cv2.putText(panorama_vis, f"Scale: 1px = {pixel_to_mm_ratio:.4f} mm", 
                       (text_x, text_y), font, font_scale, self.legend_text_color, thickness)
            text_y += line_height
            
            # 绘制比例尺
            # 直接使用pixels_per_cm作为比例尺长度（10mm对应的像素数）
            pixels_per_cm = 10.0 / pixel_to_mm_ratio if pixel_to_mm_ratio > 0 else 100
            scale_length_pixels = int(pixels_per_cm)
            scale_length_mm = 10.0  # 固定为10mm
            
            # 调整比例尺长度，确保在合理范围内
            if scale_length_pixels > legend_width - 30:  # 确保比例尺不超出图例宽度
                scale_length_pixels = legend_width - 30
                scale_length_mm = scale_length_pixels * pixel_to_mm_ratio
            elif scale_length_pixels < 50:
                scale_length_pixels = 50
                scale_length_mm = scale_length_pixels * pixel_to_mm_ratio
            
            scale_x1 = text_x
            scale_x2 = scale_x1 + scale_length_pixels
            scale_y = text_y
            
            cv2.line(panorama_vis, (scale_x1, scale_y), (scale_x2, scale_y), self.legend_text_color, 2)
            cv2.line(panorama_vis, (scale_x1, scale_y-5), (scale_x1, scale_y+5), self.legend_text_color, 1)
            cv2.line(panorama_vis, (scale_x2, scale_y-5), (scale_x2, scale_y+5), self.legend_text_color, 1)
            cv2.putText(panorama_vis, f"{scale_length_mm:.1f} mm", 
                      ((scale_x1 + scale_x2) // 2 - 15, scale_y + 15), 
                      font, font_scale, self.legend_text_color, thickness)
            
        return panorama_vis

    # ------------------------------------------------------------------
    #   新增：旋转图像并添加新的坐标轴
    # ------------------------------------------------------------------
    def _rotate_and_add_axes(self, panorama: np.ndarray, images: List[np.ndarray], is_final=False, current_real_length=None) -> np.ndarray:
        """
        将全景图逆时针旋转90度，并添加新的坐标轴
        横轴表示深度（从左到右数字依次增大）
        纵轴表示角度（从下到上数字依次增大）
        
        参数:
            panorama: 要处理的全景图
            images: 已拼接的图像列表
            is_final: 是否为最终全景图
            current_real_length: 当前拼接的实际物理长度(mm)，仅用于中间步骤
        """
        # 转换为uint8用于OpenCV绘制
        panorama_vis = np.clip(panorama, 0, 255).astype(np.uint8)
        
        # 逆时针旋转90度
        rotated = cv2.rotate(panorama_vis, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        # 获取旋转后的尺寸
        height, width = rotated.shape[:2]
        
        # 定义坐标轴边距 - 增加左侧边距以完整显示纵轴数字
        bottom_margin = 100  # 底部边距（用于深度轴）
        left_margin = 150    # 左侧边距（用于角度轴）- 从100增加到150
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
        
        # 设置字体和颜色 - 统一字体大小
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7  # 保持一致的字体大小
        thickness = 2
        axis_color = (255, 255, 255)  # 白色坐标轴
        
        # 添加深度轴（横轴）
        if self.depth_positions_mm:
            # 根据是否是最终图像或中间步骤，设置不同的深度范围
            if is_final:
                # 最终全景图显示整个深度范围
                min_depth = self.initial_depth_mm
                max_depth = self.total_pipe_length_mm
            else:
                # 中间步骤根据当前拼接长度计算深度范围
                min_depth = self.initial_depth_mm
                if current_real_length is not None:
                    # 修正：当前实际物理长度已经考虑了比例尺，不需要再乘以比例尺
                    max_depth = min_depth + current_real_length
                else:
                    # 如果没有提供当前实际长度，使用默认计算
                    current_depths = self.depth_positions_mm[:len(images)]
                    max_depth = max(current_depths) if current_depths else min_depth + 10
            
            # 绘制主轴线
            axis_y = expanded_height - bottom_margin // 2
            cv2.line(expanded, (left_margin, axis_y), (left_margin + width, axis_y), axis_color, 2)
            
            # 计算刻度间隔
            tick_interval_mm = self.depth_axis_tick_interval
            start_depth = int(min_depth / tick_interval_mm) * tick_interval_mm
            
            # 绘制刻度和标签
            for depth_mm in np.arange(start_depth, max_depth + tick_interval_mm, tick_interval_mm):
                if depth_mm < min_depth or depth_mm > max_depth:
                    continue
                
                # 计算在画布上的位置 - 根据有效拼接长度等比例映射
                if is_final:
                    # 最终全景图使用总管道长度比例
                    ratio = (depth_mm - min_depth) / (self.total_pipe_length_mm - min_depth)
                else:
                    # 中间步骤根据当前实际拼接长度计算比例
                    ratio = (depth_mm - min_depth) / (max_depth - min_depth) if max_depth > min_depth else 0
                
                x_pos = int(left_margin + ratio * width)
                
                # 确保x_pos在有效范围内
                if x_pos < left_margin or x_pos > left_margin + width:
                    continue
                
                # 绘制刻度线
                cv2.line(expanded, (x_pos, axis_y - 10), (x_pos, axis_y + 10), axis_color, 2)
                
                # 绘制深度标签
                label = f"{depth_mm:.0f}"
                text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
                text_x = x_pos - text_size[0] // 2
                text_y = axis_y + 35
                
                cv2.putText(expanded, label, (text_x, text_y), font, font_scale, axis_color, thickness)
            
            # 添加深度轴标题和比例尺信息
            if self.mm_per_pixel:
                # 计算当前画布的比例尺信息
                pixels_per_cm = 10.0 / self.scale_mm_per_pixel if hasattr(self, 'scale_mm_per_pixel') else 10.0 / self.mm_per_pixel
                
                # 根据是否是最终图像或中间步骤，显示不同的标题
                if is_final:
                    # 最终全景图显示总比例尺信息
                    scale_text = f"Scale: {pixels_per_cm:.1f}px = 10mm"
                    depth_title = f"Depth (mm) - {scale_text}"
                else:
                    # 中间步骤显示当前深度和实际拼接长度
                    current_length = current_real_length if current_real_length is not None else (max_depth - min_depth)
                    depth_title = f"Depth (mm) - Current length: {current_length:.1f}mm"
            else:
                if is_final:
                    depth_title = "Depth (mm)"
                else:
                    current_length = current_real_length if current_real_length is not None else (max_depth - min_depth)
                    depth_title = f"Depth (mm) - Current length: {current_length:.1f}mm"
                
            title_size = cv2.getTextSize(depth_title, font, font_scale + 0.2, thickness + 1)[0]
            title_x = left_margin + (width - title_size[0]) // 2  # 将标题居中
            title_y = expanded_height - 70  # 从-50改为-70，进一步向上平移
            
            cv2.putText(expanded, depth_title, (title_x, title_y), font, font_scale + 0.2, axis_color, thickness + 1)
        
        # 添加角度轴（纵轴）
        if self.enable_angle_axis:
            # 绘制主轴线
            axis_x = left_margin // 2
            cv2.line(expanded, (axis_x, top_margin), (axis_x, top_margin + height), axis_color, 2)
            
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
                    cv2.line(expanded, (axis_x - 10, y_pos), (axis_x + 10, y_pos), axis_color, 2)
                    
                    # 绘制角度标签
                    label = f"{int(angle)}"
                    text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
                    text_x = axis_x - text_size[0] - 15
                    text_y = y_pos + 5
                    
                    cv2.putText(expanded, label, (text_x, text_y), font, font_scale, axis_color, thickness)
            
            # 添加角度轴标题
            angle_title = "Angle (degrees)"
            title_size = cv2.getTextSize(angle_title, font, font_scale + 0.2, thickness + 1)[0]
            title_x = 20
            title_y = top_margin + 30
            
            # 垂直绘制标题（旋转文字）
            # 由于OpenCV不直接支持文字旋转，我们在这里水平绘制
            cv2.putText(expanded, angle_title, (title_x, title_y), font, font_scale + 0.2, axis_color, thickness + 1)
        
        # 添加图例
        if self.enable_legend:
            # 设置图例区域 - 减小宽度并增加高度
            legend_width = self.legend_width - 20  # 减小20像素宽度
            legend_height = self.legend_height + 60  # 增加50像素高度
            margin = 20  # 与图像边界的距离
            
            # 在旋转后的图像中，调整图例位置
            # 默认放在右上角
            x1 = expanded_width - legend_width - margin
            y1 = top_margin + margin
            x2 = x1 + legend_width
            y2 = y1 + legend_height
            
            # 绘制图例背景（半透明）
            overlay = expanded.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), self.legend_bg_color, -1)
            cv2.addWeighted(overlay, self.legend_opacity, expanded, 1 - self.legend_opacity, 0, expanded)
            
            # 绘制图例边框
            cv2.rectangle(expanded, (x1, y1), (x2, y2), self.legend_text_color, 1)
            
            # 计算关键信息
            if is_final:
                # 最终全景图显示总管道长度
                min_depth = self.initial_depth_mm
                max_depth = self.total_pipe_length_mm
                total_length_mm = self.total_pipe_length_mm - self.initial_depth_mm  # 有效拼接长度
            else:
                # 中间步骤显示当前深度范围
                min_depth = self.initial_depth_mm
                if current_real_length is not None:
                    max_depth = min_depth + current_real_length
                    total_length_mm = current_real_length
                else:
                    # 如果没有提供当前实际长度，使用默认计算
                    current_depths = self.depth_positions_mm[:len(images)]
                    max_depth = max(current_depths) if current_depths else min_depth + 10
                    total_length_mm = max_depth - min_depth
            
            # 计算像素到毫米的比例尺
            # 优先使用scale_mm_per_pixel，它是基于有效拼接长度计算的
            pixel_to_mm_ratio = self.scale_mm_per_pixel if hasattr(self, 'scale_mm_per_pixel') else (self.mm_per_pixel if self.mm_per_pixel else 0.1)
            
            # 计算图像实际尺寸 - 旋转后宽高互换
            original_width = height  # 旋转后，原高度变为宽度
            original_height = width  # 旋转后，原宽度变为高度
            
            # 设置文本内容（根据语言选择）
            if self.use_english_labels:
                # 英文标签
                image_size_text = f"Image Size: {original_width} x {original_height} px"
                if is_final:
                    pipe_length_text = f"Pipe Length: {self.total_pipe_length_mm:.2f} mm"
                else:
                    pipe_length_text = f"Current Length: {total_length_mm:.2f} mm"
                scale_text = f"Scale: 1px = {pixel_to_mm_ratio:.4f} mm"
                pixels_per_cm = 10.0 / pixel_to_mm_ratio if pixel_to_mm_ratio > 0 else 100
                scale_bar_text = f"{10.0} mm = {pixels_per_cm:.1f} px"
            else:
                # 中文标签
                image_size_text = f"图像尺寸: {original_width} × {original_height} 像素"
                if is_final:
                    pipe_length_text = f"管道总长: {self.total_pipe_length_mm:.2f} mm"
                else:
                    pipe_length_text = f"当前长度: {total_length_mm:.2f} mm"
                scale_text = f"比例尺: 1像素 = {pixel_to_mm_ratio:.4f} mm"
                pixels_per_cm = 10.0 / pixel_to_mm_ratio if pixel_to_mm_ratio > 0 else 100
                scale_bar_text = f"10 mm = {pixels_per_cm:.1f} 像素"
                
            # 其余图例绘制代码保持不变...
            try:
                # 确保PIL库可用
                from PIL import Image, ImageDraw, ImageFont
                
                # 创建PIL图像
                pil_img = Image.fromarray(expanded)
                draw = ImageDraw.Draw(pil_img)
                
                # 尝试加载字体
                font = None
                font_size = 20  # 增大字体大小，与坐标轴数字保持一致
                
                # 通用字体搜索路径（优先尝试支持中文的字体）
                font_paths = [
                    # macOS字体
                    "/System/Library/Fonts/PingFang.ttc",
                    "/System/Library/Fonts/STHeiti Light.ttc",
                    "/System/Library/Fonts/Hiragino Sans GB.ttc",
                    "/Library/Fonts/Arial Unicode.ttf",
                    # Windows字体
                    "C:/Windows/Fonts/msyh.ttf",  # 微软雅黑
                    "C:/Windows/Fonts/simhei.ttf",  # 黑体
                    "C:/Windows/Fonts/simsun.ttc",  # 宋体
                    "C:/Windows/Fonts/simkai.ttf",  # 楷体
                    # Linux字体
                    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                    "/usr/share/fonts/truetype/arphic/uming.ttc"
                ]
                
                # 尝试加载字体
                for path in font_paths:
                    try:
                        font = ImageFont.truetype(path, font_size)
                        self.logger.info(f"成功加载字体: {path}")
                        break
                    except Exception:
                        continue
                
                # 如果找不到支持中文的字体但启用了中文标签，切换到英文
                if font is None and not self.use_english_labels:
                    self.logger.warning("未找到支持中文的字体，自动切换为英文标签")
                    # 切换到英文标签
                    image_size_text = f"Image Size: {original_width} x {original_height} px"
                    if is_final:
                        pipe_length_text = f"Pipe Length: {self.total_pipe_length_mm:.2f} mm"
                    else:
                        pipe_length_text = f"Current Length: {total_length_mm:.2f} mm"
                    scale_text = f"Scale: 1px = {pixel_to_mm_ratio:.4f} mm"
                    
                    # 再次尝试加载常见英文字体
                    english_font_paths = [
                        "/System/Library/Fonts/Helvetica.ttc",
                        "C:/Windows/Fonts/arial.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                    ]
                    
                    for path in english_font_paths:
                        try:
                            font = ImageFont.truetype(path, font_size)
                            self.logger.info(f"加载英文字体: {path}")
                            break
                        except Exception:
                            continue
                
                # 如果仍然找不到字体，使用默认字体
                if font is None:
                    self.logger.warning("使用默认字体")
                    font = ImageFont.load_default()
                
                # 绘制文本 - 增加行高以适应更窄的图例
                line_height = 40  # 增加行高，从35到40，为更窄的图例留出更多垂直空间
                text_x = x1 + 10  # 减小左侧边距，从15到10，适应更窄的图例
                text_y = y1 + 15  # 保持顶部边距
                
                # 1. 图像尺寸
                draw.text((text_x, text_y), image_size_text, fill=tuple(self.legend_text_color), font=font)
                text_y += line_height
                
                # 2. 管道长度
                draw.text((text_x, text_y), pipe_length_text, fill=tuple(self.legend_text_color), font=font)
                text_y += line_height
                
                # 3. 比例尺文本
                draw.text((text_x, text_y), scale_text, fill=tuple(self.legend_text_color), font=font)
                text_y += line_height
                
                # 将PIL图像转回OpenCV格式
                expanded = np.array(pil_img)
                
                # 4. 绘制视觉比例尺
                # 直接使用pixels_per_cm作为比例尺长度（10mm对应的像素数）
                pixels_per_cm = 10.0 / pixel_to_mm_ratio if pixel_to_mm_ratio > 0 else 100
                scale_length_pixels = int(pixels_per_cm)
                scale_length_mm = 10.0  # 固定为10mm
                
                # 调整比例尺长度，确保在合理范围内
                if scale_length_pixels > legend_width - 30:  # 确保比例尺不超出图例宽度
                    scale_length_pixels = legend_width - 30
                    scale_length_mm = scale_length_pixels * pixel_to_mm_ratio
                elif scale_length_pixels < 50:
                    scale_length_pixels = 50
                    scale_length_mm = scale_length_pixels * pixel_to_mm_ratio
                
                scale_x1 = text_x
                scale_x2 = scale_x1 + scale_length_pixels
                scale_y = text_y + 10
                
                # 绘制比例尺线
                cv2.line(expanded, (scale_x1, scale_y), (scale_x2, scale_y), self.legend_text_color, 2)
                cv2.line(expanded, (scale_x1, scale_y-5), (scale_x1, scale_y+5), self.legend_text_color, 1)
                cv2.line(expanded, (scale_x2, scale_y-5), (scale_x2, scale_y+5), self.legend_text_color, 1)
                
                # 绘制比例尺标签
                scale_label = f"{scale_length_mm:.1f} mm"
                # 重新创建PIL图像绘制最后的标签
                pil_img = Image.fromarray(expanded)
                draw = ImageDraw.Draw(pil_img)
                draw.text(((scale_x1 + scale_x2) // 2 - 20, scale_y + 10), scale_label, 
                        fill=tuple(self.legend_text_color), font=font)
                
                # 最终转回OpenCV格式
                expanded = np.array(pil_img)
                
            except Exception as e:
                # 如果PIL渲染失败，使用OpenCV渲染（仅支持英文）
                self.logger.error(f"PIL渲染失败，使用OpenCV渲染英文: {e}")
                
                # OpenCV英文渲染 - 调整字体大小与坐标轴一致
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7  # 与坐标轴字体大小一致
                thickness = 2
                line_height = 40  # 增加行高，从35到40
                
                text_x = x1 + 10  # 减小左侧边距，从15到10
                text_y = y1 + 25  # 调整起始位置
                
                # 使用英文文本和适当的长度信息
                cv2.putText(expanded, f"Image Size: {original_width} x {original_height} px", 
                           (text_x, text_y), font, font_scale, self.legend_text_color, thickness)
                text_y += line_height
                
                if is_final:
                    cv2.putText(expanded, f"Pipe Length: {self.total_pipe_length_mm:.2f} mm", 
                               (text_x, text_y), font, font_scale, self.legend_text_color, thickness)
                else:
                    cv2.putText(expanded, f"Current Length: {total_length_mm:.2f} mm", 
                               (text_x, text_y), font, font_scale, self.legend_text_color, thickness)
                text_y += line_height
                
                cv2.putText(expanded, f"Scale: 1px = {pixel_to_mm_ratio:.4f} mm", 
                           (text_x, text_y), font, font_scale, self.legend_text_color, thickness)
                text_y += line_height
                
                # 绘制比例尺
                # 直接使用pixels_per_cm作为比例尺长度（10mm对应的像素数）
                pixels_per_cm = 10.0 / pixel_to_mm_ratio if pixel_to_mm_ratio > 0 else 100
                scale_length_pixels = int(pixels_per_cm)
                scale_length_mm = 10.0  # 固定为10mm
                
                # 调整比例尺长度，确保在合理范围内
                if scale_length_pixels > legend_width - 30:  # 确保比例尺不超出图例宽度
                    scale_length_pixels = legend_width - 30
                    scale_length_mm = scale_length_pixels * pixel_to_mm_ratio
                elif scale_length_pixels < 50:
                    scale_length_pixels = 50
                    scale_length_mm = scale_length_pixels * pixel_to_mm_ratio
                
                scale_x1 = text_x
                scale_x2 = scale_x1 + scale_length_pixels
                scale_y = text_y
                
                cv2.line(expanded, (scale_x1, scale_y), (scale_x2, scale_y), self.legend_text_color, 2)
                cv2.line(expanded, (scale_x1, scale_y-5), (scale_x1, scale_y+5), self.legend_text_color, 1)
                cv2.line(expanded, (scale_x2, scale_y-5), (scale_x2, scale_y+5), self.legend_text_color, 1)
                cv2.putText(expanded, f"{scale_length_mm:.1f} mm", 
                          ((scale_x1 + scale_x2) // 2 - 15, scale_y + 15), 
                          font, font_scale, self.legend_text_color, thickness)
        
        return expanded.astype(np.float64)


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
    def _color_balance(self, img):
        means = img.reshape(-1, 3).mean(0)
        scale = means.mean() / (means + 1e-6)
        balanced = cv2.multiply(img, scale)
        return np.clip(balanced, 0, 255).astype(np.uint8)

    def _sharpen_image(self, img):
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        return cv2.filter2D(img, -1, kernel)