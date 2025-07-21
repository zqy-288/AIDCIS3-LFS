from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class Config:
    """
    工业内窥镜图像处理系统配置类
    只保留实际使用的参数，并提供详细的调整说明
    """
    
    # =============================================================================
    # 视频处理核心参数 (必须设置)
    # =============================================================================
    start_time_seconds: float = 2.0  # 开始时间（秒）- 根据视频内容调整
    end_time_seconds: float = 7.0   # 结束时间（秒）- 根据需要的帧数调整
    
    # =============================================================================
    # 管道深度配置参数 (NEW)
    # =============================================================================
    initial_depth_mm: float = 10.0      # 开始拍摄时的管道深度（毫米）
    total_pipe_length_mm: float = 910.0  # 管道总长度（毫米）
    enable_depth_axis: bool = True       # 是否显示深度坐标轴
    depth_axis_width: int = 100          # 深度坐标轴宽度（像素）
    depth_axis_tick_interval: float = 20.0  # 坐标轴刻度间隔（毫米）
    depth_axis_color: tuple = (255, 255, 255)  # 坐标轴颜色 (白色)
    depth_axis_bg_color: tuple = (0, 0, 0)     # 坐标轴背景颜色 (黑色)
    
    # =============================================================================
    # 展开角度坐标轴配置参数 (NEW)
    # =============================================================================
    enable_angle_axis: bool = True       # 是否显示角度坐标轴
    angle_axis_height: int = 60          # 角度坐标轴高度（像素）
    angle_axis_tick_interval: float = 45.0  # 角度刻度间隔（度）
    angle_axis_color: tuple = (255, 255, 255)   # 角度坐标轴颜色 (白色)
    angle_axis_bg_color: tuple = (0, 0, 0)      # 角度坐标轴背景颜色 (黑色)
    
    # =============================================================================
    # 图例配置参数 (NEW)
    # =============================================================================
    enable_legend: bool = True           # 是否显示图例
    legend_position: str = "top-right"   # 图例位置: "top-right", "top-left", "bottom-right", "bottom-left"
    legend_width: int = 300              # 图例宽度（像素）
    legend_height: int = 120             # 图例高度（像素）
    legend_bg_color: tuple = (0, 0, 0)   # 图例背景颜色 (黑色)
    legend_text_color: tuple = (255, 255, 255)  # 图例文本颜色 (白色)
    legend_opacity: float = 0.7          # 图例背景透明度 (0-1)
    use_english_labels: bool = False     # 是否使用英文标签（解决中文乱码问题）
    
    # =============================================================================
    # 关键帧选择参数 (优化内存占用)
    # =============================================================================
    enable_keyframe_selection: bool = True    # 是否启用关键帧选择
    keyframe_strategy: str = "interval"       # 关键帧选择策略: "interval", "similarity", "motion"
    keyframe_interval: int = 5               # 固定间隔帧数 (仅interval策略使用)
    similarity_threshold: float = 0.15       # 相似度阈值 (仅similarity策略使用, 0.1-0.3)
    motion_threshold: float = 0.05           # 运动检测阈值 (仅motion策略使用, 0.01-0.1)
    max_keyframes: int = 50                  # 最大关键帧数量限制
    
    # =============================================================================
    # 去模糊处理参数 (影响图像质量)
    # =============================================================================
    defocus_method: str = "wiener"           # 去模糊方法: "wiener" 或 "lucy_richardson"
    lucy_richardson_iterations: int = 10     # Lucy-Richardson迭代次数 (10-30)
    wiener_noise_ratio: float = 0.1         # 维纳滤波噪声比 (0.001-0.1)
    
    # =============================================================================
    # 曝光调整参数 (NEW - 处理过亮区域)
    # =============================================================================
    exposure_adjustment: bool = True          # 是否启用曝光调整
    overexposed_threshold: float = 0.8        # 过曝区域亮度阈值 (0.8-0.95)
    overexposed_area_threshold: float = 0.01  # 过曝区域占比阈值 (0.01-0.1)
    shadow_boost: float = 1.2                 # 阴影区域提升系数 (1.0-1.5)
    shadow_threshold: float = 0.4             # 阴影区域亮度阈值 (0.2-0.4)
    gamma_correction: float = 1.2            # 伽马校正系数 (1.0-1.2)
    
    # =============================================================================
    # 直方图均衡化参数 (NEW - 增强图像质量)
    # =============================================================================
    use_hist_equalization: bool = True        # 是否启用直方图均衡化
    hist_eq_method: str = "adaptive"          # 均衡方法: "global", "adaptive", "hdr"
    clahe_clip_limit: float = 4.0             # CLAHE裁剪限制 (1.0-4.0)
    clahe_grid_size: int = 8                 # CLAHE网格大小 (4-16)
    detail_enhancement_factor: float = 0.8    # 细节增强因子 (0.0-1.0)
    
    # =============================================================================
    # 图像展开参数 (影响展开效果)
    # =============================================================================
    circle_detection_method: str = "adaptive"  # 圆形检测方法: "hough" 或 "adaptive"
    
    # Hough圆检测参数 (仅当circle_detection_method="hough"时使用)
    circle_detection_dp: float = 1.0               # 累加器分辨率比例 (1.0-2.0)
    circle_detection_min_dist_ratio: float = 0.5   # 最小距离比例 (0.3-0.8)
    circle_detection_param1: int = 50              # Canny边缘检测上阈值 (30-100)
    circle_detection_param2: int = 30              # 累加器阈值 (20-50)
    circle_min_radius_ratio: float = 0.2           # 最小半径比例 (0.1-0.3)
    circle_max_radius_ratio: float = 0.4           # 最大半径比例 (0.3-0.5)
    
    # 展开半径参数 (控制展开区域)
    unwrap_outer_radius_ratio: float = 0.9  # 外圆半径比例 (0.8-1.0)
    unwrap_inner_radius_ratio: float = 0.3  # 内圆半径比例 (0.2-0.4)
    
    # 内外环半径计算参数 (NEW)
    use_auto_outer_radius: bool = True      # 是否自动计算外环半径
    outer_radius_margin: int = 0           # 外环半径安全边距 (5-20)
    inner_outer_radius_ratio: float = 2.0   # 内环是外环半径的几分之一 (1.5-5.0)
    
    # =============================================================================
    # 形态学操作参数 (NEW - 影响圆形检测)
    # =============================================================================
    morph_kernel_size: int = 3              # 形态学操作结构元素大小 (3-9)
    morph_close_iterations: int = 2         # 闭操作迭代次数 (1-3)
    morph_open_iterations: int = 17         # 开操作迭代次数 (5-20)
    
    # =============================================================================
    # 圆心稳定性参数 (NEW - 影响展开稳定性)
    # =============================================================================
    initial_frames_for_center: int = 10      # 用于计算平均圆心的初始帧数 (3-10)
    
    # =============================================================================
    # 图像拼接参数 (影响拼接质量)
    # =============================================================================
    overlap: int = 300                # 重叠区域像素数 (200-400，降低避免过度融合)
    
    # =============================================================================
    # 输出控制参数
    # =============================================================================
    save_intermediate: bool = True     # 是否保存中间结果
    output_format: str = "png"         # 输出格式: "png" 或 "tiff"
    
    # =============================================================================
    # 参数调整指南
    # =============================================================================
    """
    参数调整指南：
    
    1. 时间段参数 (start_time_seconds, end_time_seconds):
       - 根据视频内容选择清晰、稳定的片段
       - 建议每次处理0.5-5秒的视频片段
       - 启用关键帧选择后可以处理更长的时间段
    
    2. 管道深度参数 (NEW):
       - initial_depth_mm: 开始拍摄时的管道深度
       - total_pipe_length_mm: 管道的总长度，用于坐标轴比例尺计算
       - enable_depth_axis: 是否在全景图左侧显示深度坐标轴
       - depth_axis_width: 坐标轴区域宽度，建议80-120像素
       - depth_axis_tick_interval: 刻度间隔，建议5-20毫米
       - depth_axis_color/depth_axis_bg_color: 坐标轴显示颜色
    
    3. 关键帧选择参数:
       - enable_keyframe_selection: 
         * True: 启用关键帧选择，减少内存占用
         * False: 处理所有帧，内存占用大但质量最高
       - keyframe_strategy:
         * "interval": 固定间隔选择，速度最快
         * "similarity": 基于相似度选择，质量较好
         * "motion": 基于运动检测选择，适合动态场景
       - keyframe_interval:
         * 5-10: 高密度采样，适合短时间段
         * 10-20: 中等密度，平衡质量和性能
         * 20-30: 低密度采样，节省内存
       - similarity_threshold:
         * 0.1-0.15: 严格选择，帧数较少
         * 0.15-0.25: 中等选择，平衡质量
         * 0.25-0.3: 宽松选择，帧数较多
       - max_keyframes:
         * 30-50: 适合短片段处理
         * 50-100: 适合中等长度片段
         * 100+: 适合长片段处理
    
    4. 去模糊参数调整:
       - defocus_method: 
         * "wiener" - 速度快，适合轻度模糊
         * "lucy_richardson" - 效果好，适合严重模糊
       - lucy_richardson_iterations: 
         * 10-15: 轻度模糊
         * 15-25: 中度模糊  
         * 25-30: 重度模糊
       - wiener_noise_ratio:
         * 0.001-0.01: 低噪声环境
         * 0.01-0.05: 中等噪声
         * 0.05-0.1: 高噪声环境
          
    5. 曝光调整参数 (NEW):
       - exposure_adjustment:
         * True: 启用曝光调整，处理过曝区域
         * False: 不进行曝光调整
       - overexposed_threshold:
         * 0.8-0.85: 保守识别，处理严重过曝区域
         * 0.85-0.9: 中等识别，平衡识别范围
         * 0.9-0.95: 敏感识别，处理轻微过曝区域
       - overexposed_area_threshold:
         * 0.01-0.03: 即使小面积过曝也进行调整
         * 0.03-0.07: 中等面积过曝才进行调整
         * 0.07-0.1: 大面积过曝才进行调整
       - shadow_boost/shadow_threshold:
         * 调整阴影区域的增强效果
       - gamma_correction:
         * 1.0-1.05: 轻微调整
         * 1.05-1.1: 中等调整
         * 1.1-1.2: 强烈调整
         
    6. 直方图均衡化参数 (NEW):
       - use_hist_equalization:
         * True: 启用直方图均衡化增强图像质量
         * False: 使用传统曝光调整
       - hist_eq_method:
         * "global": 全局直方图均衡，提高整体对比度但可能导致局部过曝
         * "adaptive": 局部自适应直方图均衡(CLAHE)，平衡局部对比度，推荐普通场景
         * "hdr": HDR风格处理，对亮区、中间区和暗区分别处理，适合高对比度场景
       - clahe_clip_limit:
         * 1.0-2.0: 轻度对比度增强
         * 2.0-3.0: 中等对比度增强
         * 3.0-4.0: 强烈对比度增强，可能引入噪点
       - clahe_grid_size:
         * 4-6: 细粒度均衡，处理小尺寸细节
         * 8-10: 平衡均衡，适合大多数场景
         * 12-16: 粗粒度均衡，处理大面积亮度变化
       - detail_enhancement_factor:
         * 0.0-0.2: 轻微细节增强
         * 0.2-0.5: 中等细节增强
         * 0.5-1.0: 强烈细节增强，可能增加噪声
    
    7. 展开参数调整:
       - circle_detection_method:
         * "adaptive": 自动适应，推荐使用
         * "hough": 需要手动调参，精度高
       - unwrap_outer_radius_ratio: 
         * 0.8-0.9: 保守设置，避免边缘失真
         * 0.9-1.0: 最大化信息保留
       - unwrap_inner_radius_ratio:
         * 0.2-0.3: 保守设置，去除中心遮挡区域
         * 0.3-0.4: 保留更多中心信息
         
       - use_auto_outer_radius:
         * True: 自动计算外环半径，使用图像边界的最近距离
         * False: 使用unwrap_outer_radius_ratio参数手动控制外环半径
         
       - outer_radius_margin:
         * 5-10: 较小边距，最大化信息保留但可能接近边缘
         * 10-15: 平衡边距，避免边缘效应
         * 15-20: 较大边距，确保远离边缘但可能丢失信息
         
       - inner_outer_radius_ratio:
         * 1.5-2.0: 内环更大，保留更多内部信息
         * 2.0-3.0: 平衡设置，适合大多数场景
         * 3.0-5.0: 内环较小，过滤掉更多中心区域
         
    8. 形态学操作参数 (NEW):
       - morph_kernel_size:
         * 3: 精细结构元素，保留细节
         * 5: 平衡设置，适合大多数场景
         * 7-9: 大尺寸结构元素，消除更多噪声但可能丢失细节
       - morph_close_iterations:
         * 1: 轻度闭操作，填充小孔洞
         * 2: 中度闭操作，填充中等孔洞
         * 3: 强烈闭操作，填充大孔洞但可能引入伪影
       - morph_open_iterations:
         * 5-8: 轻度开操作，去除小噪点
         * 9-13: 中度开操作，平衡噪声去除和形状保留
         * 14-20: 强烈开操作，去除大面积噪声但可能改变形状
         
    9. 圆心稳定性参数 (NEW):
       - initial_frames_for_center:
         * 3-4: 较少帧数，适合快速变化场景
         * 5-7: 平衡设置，适合大多数场景
         * 8-10: 较多帧数，最大化稳定性但可能滞后
    
    10. 拼接参数调整:
       - overlap: 重叠区域大小
         * 400-500: 处理速度优先
         * 600-700: 拼接质量优先
         * 700-800: 最高质量拼接
    
    11. 输出参数:
       - save_intermediate: 调试时设为True，生产时可设为False
       - output_format: PNG通用性好，TIFF质量更高
    """
    
    @classmethod
    def from_json(cls, json_path: str) -> 'Config':
        """从JSON文件加载配置"""
        with open(json_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
    
    def save_json(self, json_path: str):
        """保存配置到JSON文件"""
        config_dict = self.__dict__.copy()
        # 处理tuple类型
        for key, value in config_dict.items():
            if isinstance(value, tuple):
                config_dict[key] = list(value)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False)
    
    def get_processing_summary(self) -> str:
        """获取处理配置摘要"""
        duration = self.end_time_seconds - self.start_time_seconds
        keyframe_info = ""
        if self.enable_keyframe_selection:
            keyframe_info = f"\n关键帧选择: {self.keyframe_strategy} (间隔:{self.keyframe_interval}, 最大:{self.max_keyframes})"
        
        exposure_info = f"\n曝光调整: {'启用' if self.exposure_adjustment else '禁用'}"
        
        hist_eq_info = ""
        if hasattr(self, 'use_hist_equalization') and self.use_hist_equalization:
            hist_eq_info = f"\n直方图均衡: {self.hist_eq_method} (CLAHE限制:{self.clahe_clip_limit}, 网格:{self.clahe_grid_size})"
        
        return f"""
=== 处理配置摘要 ===
时间段: {self.start_time_seconds:.1f}s - {self.end_time_seconds:.1f}s (时长: {duration:.1f}s){keyframe_info}{exposure_info}{hist_eq_info}
去模糊方法: {self.defocus_method}
展开检测: {self.circle_detection_method}
重叠区域: {self.overlap}px
输出格式: {self.output_format}
保存中间结果: {self.save_intermediate}
==================
"""
    
    def validate(self) -> bool:
        """验证配置参数的有效性"""
        if self.start_time_seconds < 0:
            raise ValueError("开始时间不能为负数")
        if self.end_time_seconds <= self.start_time_seconds:
            raise ValueError("结束时间必须大于开始时间")
        if self.overlap < 200:
            raise ValueError("重叠区域不能小于200像素")
        if self.lucy_richardson_iterations < 1:
            raise ValueError("迭代次数必须大于0")
        if self.enable_keyframe_selection:
            if self.keyframe_strategy not in ["interval", "similarity", "motion"]:
                raise ValueError("关键帧策略必须是 'interval', 'similarity' 或 'motion'")
            if self.keyframe_interval < 1:
                raise ValueError("关键帧间隔必须大于0")
            if self.max_keyframes < 1:
                raise ValueError("最大关键帧数必须大于0")
        
        # 验证曝光调整参数
        if hasattr(self, "exposure_adjustment") and self.exposure_adjustment:
            if not (0.8 <= self.overexposed_threshold <= 0.95):
                raise ValueError("过曝区域亮度阈值必须在0.8-0.95之间")
            if not (0.01 <= self.overexposed_area_threshold <= 0.1):
                raise ValueError("过曝区域占比阈值必须在0.01-0.1之间")
            if not (1.0 <= self.gamma_correction <= 1.2):
                raise ValueError("伽马校正系数必须在1.0-1.2之间")
        
        # 验证形态学操作参数
        if hasattr(self, "morph_kernel_size"):
            if not (3 <= self.morph_kernel_size <= 9):
                raise ValueError("形态学操作结构元素大小必须在3-9之间")
            if self.morph_kernel_size % 2 == 0:
                raise ValueError("形态学操作结构元素大小必须是奇数")
            if not (1 <= self.morph_close_iterations <= 3):
                raise ValueError("闭操作迭代次数必须在1-3之间")
            if not (5 <= self.morph_open_iterations <= 20):
                raise ValueError("开操作迭代次数必须在5-20之间")
        
        # 验证圆心稳定性参数
        if hasattr(self, "initial_frames_for_center"):
            if not (3 <= self.initial_frames_for_center <= 10):
                raise ValueError("用于计算平均圆心的初始帧数必须在3-10之间")
        
        return True 