#!/usr/bin/env python3
"""
自适应缩放管理器
使用数学函数实现连续性缩放处理，替代离散的分类场景
"""

import math
from typing import Dict, Optional, Tuple, Any
from PySide6.QtCore import QRectF, QPointF
from PySide6.QtWidgets import QGraphicsView

from aidcis2.models.hole_data import HoleCollection


# ============================================================================
# 数学函数定义
# ============================================================================

def sigmoid(x: float, midpoint: float = 0.5, steepness: float = 10) -> float:
    """
    Sigmoid函数：平滑的S型曲线过渡
    
    Args:
        x: 输入值 (0-1)
        midpoint: 中点位置 (0-1)
        steepness: 陡峭程度
    
    Returns:
        输出值 (0-1)
    """
    return 1 / (1 + math.exp(-steepness * (x - midpoint)))


def log_scale_function(value: float, min_val: float, max_val: float, 
                      base: float = 10) -> float:
    """
    对数缩放函数：处理大范围数值的平滑过渡
    
    Args:
        value: 输入值
        min_val: 最小值
        max_val: 最大值
        base: 对数底数
    
    Returns:
        标准化后的值 (0-1)
    """
    if value <= min_val:
        return 0.0
    if value >= max_val:
        return 1.0
    
    # 对数映射
    log_value = math.log(value, base)
    log_min = math.log(min_val, base)
    log_max = math.log(max_val, base)
    
    return (log_value - log_min) / (log_max - log_min)


def smooth_clamp(value: float, min_val: float, max_val: float, 
                smoothness: float = 0.1) -> float:
    """
    平滑限制函数：避免硬性截断，提供平滑过渡
    
    Args:
        value: 输入值
        min_val: 最小值
        max_val: 最大值
        smoothness: 平滑度 (0-1)
    
    Returns:
        平滑限制后的值
    """
    range_val = max_val - min_val
    smooth_zone = range_val * smoothness
    
    if value < min_val + smooth_zone:
        # 下端平滑过渡
        t = (value - min_val) / smooth_zone
        return min_val + smooth_zone * sigmoid(t, 0.5, 5)
    elif value > max_val - smooth_zone:
        # 上端平滑过渡
        t = (value - (max_val - smooth_zone)) / smooth_zone
        return max_val - smooth_zone * (1 - sigmoid(t, 0.5, 5))
    else:
        return value


# ============================================================================
# 连续性参数计算
# ============================================================================

class ContinuousScaleCalculator:
    """连续性缩放计算器"""
    
    def __init__(self):
        # 数据规模分类点（用于连续函数）
        self.hole_count_ranges = {
            'tiny': (1, 100),           # 微型：测试数据
            'small': (100, 1000),       # 小型：简单管板
            'medium': (1000, 5000),     # 中型：标准管板
            'large': (5000, 15000),     # 大型：复杂管板
            'huge': (15000, 50000),     # 巨型：工业级管板
        }
        
        # 数据尺寸分类点
        self.size_ranges = {
            'tiny': (0, 500),           # 0-500像素
            'small': (500, 1500),       # 500-1500像素
            'medium': (1500, 3000),     # 1.5k-3k像素
            'large': (3000, 6000),      # 3k-6k像素
            'huge': (6000, 10000),      # 6k-10k像素
        }
    
    def calculate_data_complexity(self, hole_collection: HoleCollection, 
                                 data_bounds: Tuple[float, float, float, float]) -> float:
        """
        计算数据复杂度 (0-1)
        综合考虑孔位数量、数据尺寸、分布密度
        """
        hole_count = len(hole_collection)
        data_width = data_bounds[2] - data_bounds[0]
        data_height = data_bounds[3] - data_bounds[1]
        data_area = data_width * data_height
        
        # 1. 孔位数量复杂度 (0-1)
        count_complexity = log_scale_function(hole_count, 10, 50000, 10)
        
        # 2. 数据尺寸复杂度 (0-1)
        max_dimension = max(data_width, data_height)
        size_complexity = log_scale_function(max_dimension, 100, 10000, 10)
        
        # 3. 密度复杂度 (0-1)
        if data_area > 0:
            density = hole_count / data_area
            density_complexity = log_scale_function(density, 0.001, 10, 10)
        else:
            density_complexity = 0.5
        
        # 加权组合
        complexity = (
            count_complexity * 0.4 +    # 孔位数量权重40%
            size_complexity * 0.4 +     # 数据尺寸权重40%
            density_complexity * 0.2    # 密度权重20%
        )
        
        return min(1.0, max(0.0, complexity))
    
    def calculate_adaptive_margin(self, complexity: float, view_size: float) -> float:
        """
        计算自适应边距比例
        复杂度越高，边距越小（为了显示更多内容）
        """
        base_margin = 0.12      # 基础边距12%
        min_margin = 0.02       # 最小边距2%
        
        # 使用反向sigmoid函数：复杂度高时边距小
        margin_factor = 1 - sigmoid(complexity, 0.6, 8)
        adaptive_margin = base_margin * margin_factor + min_margin * (1 - margin_factor)
        
        return adaptive_margin
    
    def calculate_adaptive_scale_range(self, complexity: float, 
                                     view_size: float) -> Tuple[float, float]:
        """
        计算自适应缩放范围
        根据复杂度动态调整最小/最大缩放比例
        """
        # 基础缩放范围
        base_min = 0.1
        base_max = 0.9
        
        # 根据复杂度调整
        if complexity < 0.3:
            # 简单数据：允许较大缩放
            min_scale = base_min
            max_scale = base_max
        elif complexity < 0.7:
            # 中等复杂：平滑过渡
            t = (complexity - 0.3) / 0.4  # 标准化到0-1
            min_scale = base_min * (1 - 0.8 * sigmoid(t, 0.5, 6))  # 最小可降到0.02
            max_scale = base_max * (1 - 0.1 * sigmoid(t, 0.5, 6))  # 最大略降
        else:
            # 高复杂度：需要很小的缩放显示全貌
            t = (complexity - 0.7) / 0.3
            min_scale = 0.02 + 0.08 * (1 - sigmoid(t, 0.5, 8))
            max_scale = 0.8 * (1 - 0.3 * sigmoid(t, 0.5, 8))
        
        return (min_scale, max_scale)
    
    def calculate_adaptive_scene_ratio(self, complexity: float, scale: float) -> float:
        """
        计算自适应场景尺寸比例
        复杂度和缩放比例越小，场景控制越严格
        """
        base_ratio = 1.2  # 基础比例120%
        min_ratio = 1.05  # 最小比例105%
        max_ratio = 1.5   # 最大比例150%
        
        # 复杂度影响：高复杂度需要更严格的场景控制
        complexity_factor = 1 - 0.3 * sigmoid(complexity, 0.6, 8)
        
        # 缩放影响：小缩放需要更严格的场景控制
        scale_factor = 1 - 0.2 * sigmoid(1/scale if scale > 0 else 10, 10, 5)
        
        ratio = base_ratio * complexity_factor * scale_factor
        return smooth_clamp(ratio, min_ratio, max_ratio, 0.1)


# ============================================================================
# 连续性缩放管理器
# ============================================================================

class AdaptiveScaleManager:
    """自适应缩放管理器"""
    
    def __init__(self):
        self.calculator = ContinuousScaleCalculator()
    
    def calculate_optimal_scale_config(self, hole_collection: HoleCollection,
                                     view_rect: QRectF,
                                     mode: str = "panorama") -> Dict[str, Any]:
        """
        计算最优缩放配置（连续性方法）
        
        Args:
            hole_collection: 孔位数据
            view_rect: 视图矩形
            mode: 模式（panorama/main等）
        
        Returns:
            完整的缩放配置
        """
        # 1. 获取数据特征
        data_bounds = hole_collection.get_bounds()
        content_rect = QRectF(
            data_bounds[0], data_bounds[1],
            data_bounds[2] - data_bounds[0],
            data_bounds[3] - data_bounds[1]
        )
        
        # 2. 计算数据复杂度
        complexity = self.calculator.calculate_data_complexity(hole_collection, data_bounds)
        
        # 3. 计算自适应参数
        margin_ratio = self.calculator.calculate_adaptive_margin(complexity, view_rect.width())
        min_scale, max_scale = self.calculator.calculate_adaptive_scale_range(complexity, view_rect.width())
        
        # 4. 计算基础缩放
        effective_width = view_rect.width() * (1 - 2 * margin_ratio)
        effective_height = view_rect.height() * (1 - 2 * margin_ratio)
        
        scale_x = effective_width / content_rect.width() if content_rect.width() > 0 else 1.0
        scale_y = effective_height / content_rect.height() if content_rect.height() > 0 else 1.0
        base_scale = min(scale_x, scale_y)
        
        # 5. 应用平滑限制
        final_scale = smooth_clamp(base_scale, min_scale, max_scale, 0.1)
        
        # 6. 计算场景配置
        scene_ratio = self.calculator.calculate_adaptive_scene_ratio(complexity, final_scale)
        scene_rect = self._calculate_adaptive_scene_rect(content_rect, final_scale, 
                                                       view_rect, scene_ratio)
        
        # 7. 返回完整配置
        return {
            "mode": mode,
            "scale": final_scale,
            "center": content_rect.center(),
            "scene_rect": scene_rect,
            "content_rect": content_rect,
            "view_rect": view_rect,
            "adaptive_params": {
                "complexity": complexity,
                "margin_ratio": margin_ratio,
                "scale_range": (min_scale, max_scale),
                "scene_ratio": scene_ratio,
                "base_scale": base_scale,
                "scale_adjustment": final_scale / base_scale if base_scale > 0 else 1.0
            },
            "debug_info": {
                "hole_count": len(hole_collection),
                "data_size": (content_rect.width(), content_rect.height()),
                "complexity_level": self._get_complexity_level(complexity),
                "margin_adaptive": f"{margin_ratio*100:.1f}%",
                "scale_adaptive": f"{min_scale:.3f}-{max_scale:.3f}"
            }
        }
    
    def _calculate_adaptive_scene_rect(self, content_rect: QRectF, scale: float,
                                     view_rect: QRectF, ratio: float) -> QRectF:
        """计算自适应场景矩形"""
        content_center = content_rect.center()
        
        # 基于内容和视图计算场景尺寸
        content_size = max(content_rect.width(), content_rect.height())
        view_size = max(view_rect.width(), view_rect.height())
        required_size = max(content_size, view_size / scale) if scale > 0 else content_size
        
        # 应用自适应比例
        scene_size = required_size * ratio
        
        # 限制最大场景尺寸（性能考虑）
        max_scene_size = 8000
        if scene_size > max_scene_size:
            scene_size = max_scene_size
        
        return QRectF(
            content_center.x() - scene_size / 2,
            content_center.y() - scene_size / 2,
            scene_size,
            scene_size
        )
    
    def _get_complexity_level(self, complexity: float) -> str:
        """获取复杂度等级描述"""
        if complexity < 0.2:
            return "简单"
        elif complexity < 0.4:
            return "中等"
        elif complexity < 0.6:
            return "复杂"
        elif complexity < 0.8:
            return "高复杂"
        else:
            return "极复杂"


# ============================================================================
# 统一接口函数
# ============================================================================

def apply_adaptive_scale(view: QGraphicsView, hole_collection: HoleCollection,
                        mode: str = "panorama", debug: bool = True) -> bool:
    """
    应用自适应缩放（统一接口）
    
    Args:
        view: 图形视图
        hole_collection: 孔位数据
        mode: 缩放模式
        debug: 调试输出
    
    Returns:
        是否成功
    """
    try:
        if debug:
            print(f"🧠 [自适应缩放] 开始智能分析: {len(hole_collection)} 个孔位")
        
        # 1. 禁用自动缩放
        view.disable_auto_fit = True
        view.disable_auto_center = True
        
        # 2. 加载数据
        view.load_holes(hole_collection)
        
        # 3. 获取视图尺寸（动态容器大小检测）
        view_rect = _get_dynamic_container_size(view, mode, debug)
        
        # 4. 计算自适应配置
        manager = AdaptiveScaleManager()
        config = manager.calculate_optimal_scale_config(hole_collection, view_rect, mode)
        
        if debug:
            print(f"🧮 [自适应缩放] 分析结果:")
            print(f"   - 复杂度: {config['debug_info']['complexity_level']} "
                  f"({config['adaptive_params']['complexity']:.3f})")
            print(f"   - 自适应边距: {config['debug_info']['margin_adaptive']}")
            print(f"   - 自适应缩放范围: {config['debug_info']['scale_adaptive']}")
            print(f"   - 最终缩放: {config['scale']:.4f}")
            print(f"   - 缩放调整系数: {config['adaptive_params']['scale_adjustment']:.3f}")
        
        # 5. 应用缩放
        return _apply_adaptive_config(view, config, debug)
        
    except Exception as e:
        if debug:
            print(f"❌ [自适应缩放] 失败: {e}")
        return False


def _apply_adaptive_config(view: QGraphicsView, config: Dict[str, Any], debug: bool) -> bool:
    """应用自适应缩放配置"""
    try:
        # 检查缩放锁
        if getattr(view, '_scaling_in_progress', False):
            return False
        
        view._scaling_in_progress = True
        
        if debug:
            print(f"🎯 [自适应缩放] 应用配置...")
        
        # 1. 重置变换
        view.resetTransform()
        
        # 2. 设置场景
        if view.scene:
            view.scene.setSceneRect(config["scene_rect"])
        
        # 3. 应用缩放和居中
        view.scale(config["scale"], config["scale"])
        view.centerOn(config["center"])
        
        if debug:
            print(f"✅ [自适应缩放] 应用完成")
        
        return True
        
    except Exception as e:
        if debug:
            print(f"❌ [自适应缩放] 应用失败: {e}")
        return False
    finally:
        view._scaling_in_progress = False


# ============================================================================
# 快捷函数
# ============================================================================

def apply_adaptive_panorama_scale(view: QGraphicsView, hole_collection: HoleCollection) -> bool:
    """自适应全景图缩放（快捷函数）"""
    return apply_adaptive_scale(view, hole_collection, "panorama")


def apply_adaptive_main_scale(view: QGraphicsView, hole_collection: HoleCollection) -> bool:
    """自适应主视图缩放（快捷函数）"""
    return apply_adaptive_scale(view, hole_collection, "main")


def analyze_data_characteristics(hole_collection: HoleCollection) -> Dict[str, Any]:
    """分析数据特征（诊断函数）"""
    calculator = ContinuousScaleCalculator()
    bounds = hole_collection.get_bounds()
    complexity = calculator.calculate_data_complexity(hole_collection, bounds)
    
    return {
        "hole_count": len(hole_collection),
        "data_bounds": bounds,
        "data_size": (bounds[2] - bounds[0], bounds[3] - bounds[1]),
        "complexity": complexity,
        "complexity_level": AdaptiveScaleManager()._get_complexity_level(complexity),
        "recommended_margin": calculator.calculate_adaptive_margin(complexity, 350),
        "recommended_scale_range": calculator.calculate_adaptive_scale_range(complexity, 350)
    }


# ============================================================================
# 动态容器大小检测
# ============================================================================

def _get_dynamic_container_size(view: QGraphicsView, mode: str, debug: bool = False) -> QRectF:
    """
    动态检测容器大小，替代硬编码的350x350
    
    Args:
        view: 图形视图
        mode: 缩放模式
        debug: 调试输出
    
    Returns:
        实际可用的视图矩形
    """
    try:
        # 1. 获取视图的实际尺寸
        viewport_rect = view.viewport().rect()
        actual_width = viewport_rect.width()
        actual_height = viewport_rect.height()
        
        # 2. 检测容器上下文
        container_context = _detect_container_context(view, debug)
        
        # 3. 计算有效显示区域
        effective_rect = _calculate_effective_display_area(
            actual_width, actual_height, container_context, debug
        )
        
        if debug:
            print(f"📺 [动态容器] 检测结果:")
            print(f"   - 原始视图尺寸: {actual_width}x{actual_height}")
            print(f"   - 容器上下文: {container_context['type']}")
            print(f"   - 有效显示区域: {effective_rect.width():.0f}x{effective_rect.height():.0f}")
            
        return effective_rect
        
    except Exception as e:
        if debug:
            print(f"⚠️ [动态容器] 检测失败，使用默认尺寸: {e}")
        
        # 发生错误时回退到默认尺寸
        return QRectF(0, 0, 350, 350)


def _detect_container_context(view: QGraphicsView, debug: bool = False) -> Dict[str, Any]:
    """
    检测容器上下文（侧边栏全景图 vs mini_panorama）
    
    Args:
        view: 图形视图
        debug: 调试输出
    
    Returns:
        容器上下文信息
    """
    context = {
        "type": "unknown",
        "has_info_label": False,
        "container_widget": None,
        "available_space_ratio": 1.0
    }
    
    try:
        # 向上查找父组件来判断上下文
        parent = view.parent()
        while parent:
            parent_class = parent.__class__.__name__
            
            if parent_class == "CompletePanoramaWidget":
                # 检查是否是侧边栏全景图（有info_label）
                if hasattr(parent, 'info_label'):
                    context["type"] = "sidebar_panorama"
                    context["has_info_label"] = True
                    context["container_widget"] = parent
                    
                    # 计算info_label占用的空间
                    if hasattr(parent, 'info_label'):
                        info_label_height = parent.info_label.height() if parent.info_label.height() > 0 else 25
                        container_height = parent.height() if parent.height() > 0 else 350
                        context["available_space_ratio"] = (container_height - info_label_height) / container_height
                    
                    break
                else:
                    # 没有info_label，可能是mini_panorama
                    context["type"] = "mini_panorama"
                    context["container_widget"] = parent
                    break
                    
            parent = parent.parent()
            
        if debug:
            print(f"🔍 [容器上下文] 检测到: {context['type']}")
            if context["has_info_label"]:
                print(f"   - 有info_label，可用空间比例: {context['available_space_ratio']:.2f}")
                
    except Exception as e:
        if debug:
            print(f"⚠️ [容器上下文] 检测失败: {e}")
            
    return context


def _calculate_effective_display_area(width: int, height: int, context: Dict[str, Any], 
                                    debug: bool = False) -> QRectF:
    """
    计算有效显示区域
    
    Args:
        width: 视图宽度
        height: 视图高度
        context: 容器上下文
        debug: 调试输出
    
    Returns:
        有效显示区域矩形
    """
    try:
        # 默认使用实际尺寸
        effective_width = width
        effective_height = height
        
        # 根据容器类型调整
        if context["type"] == "sidebar_panorama":
            # 侧边栏全景图：考虑info_label的空间占用
            if context["has_info_label"]:
                # 为info_label预留空间（通常在底部）
                info_label_reserved_height = 30  # 预留高度
                effective_height = max(height - info_label_reserved_height, height * 0.8)
                
        elif context["type"] == "mini_panorama":
            # mini_panorama：可以使用全部空间
            effective_width = width
            effective_height = height
            
        # 确保最小尺寸
        effective_width = max(effective_width, 200)
        effective_height = max(effective_height, 200)
        
        # 保持正方形比例（全景图通常是正方形）
        effective_size = min(effective_width, effective_height)
        
        if debug:
            print(f"📐 [有效区域] 计算: {width}x{height} -> {effective_size}x{effective_size}")
            
        return QRectF(0, 0, effective_size, effective_size)
        
    except Exception as e:
        if debug:
            print(f"⚠️ [有效区域] 计算失败: {e}")
        return QRectF(0, 0, min(width, height), min(width, height))