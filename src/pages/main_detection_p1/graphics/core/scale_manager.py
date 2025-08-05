#!/usr/bin/env python3
"""
统一缩放管理器
独立的缩放管理系统，用于解决多重缩放冲突问题
"""

from typing import Dict, Optional, Tuple, Any
from PySide6.QtCore import QRectF, QPointF, QTimer, QObject, Signal
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QTransform

from src.shared.models.hole_data import HoleCollection


# ============================================================================
# 配置定义
# ============================================================================

SCALE_CONFIGS = {
    "panorama_overview": {
        "description": "全景图概览模式 - 显示完整管板",
        "margin_ratio": 0.02,  # 减少边距到2%，让孔位区域更充分利用空间
        "min_scale": 0.02,     # 降低最小缩放，支持超大型管板（如25K孔位）
        "max_scale": 1.2,      # 增大最大缩放到120%，让孔位区域在圆形背景中更大
        "priority": "fit_all", # 优先显示全部内容
        "center_mode": "data_center"  # 以数据中心为准
    },
    "sidebar_panorama_overview": {
        "description": "侧边栏全景图概览模式 - 考虑info_label空间",
        "margin_ratio": 0.03,  # 减少边距到3%，为孔位区域留更多显示空间
        "min_scale": 0.02,     # 支持超大型管板
        "max_scale": 1.0,      # 增大最大缩放到100%，让矩形区域更充分利用圆形空间
        "priority": "fit_all_with_info",
        "center_mode": "data_center"
    },
    "mini_panorama_overview": {
        "description": "小型全景图概览模式 - 紧凑显示",
        "margin_ratio": 0.03,  # 3%边距，最大化显示空间
        "min_scale": 0.02,     # 支持超大型管板
        "max_scale": 0.90,     # 更高的最大缩放，充分利用空间
        "priority": "fit_all_compact",
        "center_mode": "data_center"
    },
    "massive_dataset_panorama": {
        "description": "超大数据集全景图模式 - 针对20K+孔位优化",
        "margin_ratio": 0.02,  # 2%边距，确保完整显示
        "min_scale": 0.030,    # 3%缩放，在概览性和可见性间平衡
        "max_scale": 0.080,    # 适当提高最大缩放
        "priority": "balanced_overview",
        "center_mode": "data_center"
    },
    "mini_massive_dataset_panorama": {
        "description": "小型全景图超大数据集模式 - 增强可见性",
        "margin_ratio": 0.05,  # 5%边距
        "min_scale": 0.10,     # 10%最小缩放，确保孔位可见
        "max_scale": 0.30,     # 30%最大缩放
        "priority": "visibility_first",
        "center_mode": "data_center"
    },
    "panorama_sector": {
        "description": "全景图扇形模式 - 突出显示扇形区域",
        "margin_ratio": 0.12,
        "min_scale": 0.3,
        "max_scale": 1.5,
        "priority": "sector_focus",
        "center_mode": "sector_center"
    },
    "main_macro": {
        "description": "主视图宏观模式 - 管板概览",
        "margin_ratio": 0.02,
        "min_scale": 0.5,
        "max_scale": 2.0,
        "priority": "macro_overview",
        "center_mode": "scene_center"
    },
    "main_micro": {
        "description": "主视图微观模式 - 孔位细节",
        "margin_ratio": 0.1,
        "min_scale": 1.2,
        "max_scale": 4.0,
        "priority": "detail_view",
        "center_mode": "selection_center"
    }
}


# ============================================================================
# 核心计算函数
# ============================================================================

def calculate_fit_scale(content_rect: QRectF, view_rect: QRectF, margin_ratio: float = 0.05) -> float:
    """
    计算适配缩放比例
    
    Args:
        content_rect: 内容边界矩形
        view_rect: 视图矩形  
        margin_ratio: 边距比例 (0.0-0.5)
    
    Returns:
        适配的缩放比例
    """
    if content_rect.isEmpty() or view_rect.isEmpty():
        return 1.0
    
    if content_rect.width() <= 0 or content_rect.height() <= 0:
        return 1.0
    
    # 计算考虑边距后的有效视图区域
    margin_ratio = max(0.0, min(0.4, margin_ratio))  # 限制边距范围
    effective_width = view_rect.width() * (1 - 2 * margin_ratio)
    effective_height = view_rect.height() * (1 - 2 * margin_ratio)
    
    # 计算两个方向的缩放比例，取较小值确保完全适配
    scale_x = effective_width / content_rect.width()
    scale_y = effective_height / content_rect.height()
    
    return min(scale_x, scale_y)


def clamp_scale(scale: float, min_scale: float, max_scale: float) -> float:
    """
    限制缩放比例在指定范围内
    
    Args:
        scale: 原始缩放比例
        min_scale: 最小缩放比例
        max_scale: 最大缩放比例
    
    Returns:
        限制后的缩放比例
    """
    return max(min_scale, min(scale, max_scale))


def calculate_optimal_scene_rect(content_rect: QRectF, scale: float, view_rect: QRectF, 
                               mode: str = "panorama_overview") -> QRectF:
    """
    计算最优的场景矩形
    
    Args:
        content_rect: 内容边界
        scale: 缩放比例
        view_rect: 视图矩形
        mode: 缩放模式
        
    Returns:
        最优的场景矩形
    """
    # 以内容中心为基准
    content_center = content_rect.center()
    
    # 计算场景所需的最小尺寸
    min_scene_width = max(content_rect.width(), view_rect.width() / scale)
    min_scene_height = max(content_rect.height(), view_rect.height() / scale)
    
    # 根据模式和数据规模调整余量策略
    max_dimension = max(min_scene_width, min_scene_height)
    
    if mode == "massive_dataset_panorama":
        # 超大数据集：极小缩放，只留数据本身大小
        scene_width = content_rect.width() * 1.01   # 只留1%余量
        scene_height = content_rect.height() * 1.01
    elif mode == "mini_massive_dataset_panorama":
        # 小型全景图+超大数据集：适度缩放以保证可见性
        scene_width = content_rect.width() * 1.05   # 5%余量
        scene_height = content_rect.height() * 1.05
    elif max_dimension > 5000:
        # 大型管板：减少余量
        scene_width = min_scene_width * 1.05  # 从1.1改为1.05
        scene_height = min_scene_height * 1.05
    else:
        # 普通管板：标准余量
        scene_width = min_scene_width * 1.2
        scene_height = min_scene_height * 1.2
    
    # 限制场景矩形的最大尺寸以避免性能问题
    if mode == "massive_dataset_panorama":
        max_scene_size = 5000  # 超大数据集极小缩放时的限制
    elif mode == "mini_massive_dataset_panorama":
        max_scene_size = 3000  # 小型全景图需要更严格的限制
    else:
        max_scene_size = 8000  # 标准限制
        
    if scene_width > max_scene_size:
        scene_width = max_scene_size
    if scene_height > max_scene_size:
        scene_height = max_scene_size
    
    # 创建以内容中心为中心的场景矩形
    scene_rect = QRectF(
        content_center.x() - scene_width / 2,
        content_center.y() - scene_height / 2,
        scene_width,
        scene_height
    )
    
    return scene_rect


# ============================================================================
# 缩放参数计算
# ============================================================================

def calculate_scale_config(mode: str, content_rect: QRectF, view_rect: QRectF, 
                          custom_params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    计算指定模式的缩放配置
    
    Args:
        mode: 缩放模式 ("panorama_overview", "panorama_sector", etc.)
        content_rect: 内容边界矩形
        view_rect: 视图矩形
        custom_params: 自定义参数，会覆盖默认配置
    
    Returns:
        缩放配置字典
    """
    # 获取基础配置
    if mode not in SCALE_CONFIGS:
        raise ValueError(f"未知的缩放模式: {mode}")
    
    base_config = SCALE_CONFIGS[mode].copy()
    
    # 应用自定义参数
    if custom_params:
        base_config.update(custom_params)
    
    # 计算基础缩放比例
    base_scale = calculate_fit_scale(
        content_rect, 
        view_rect, 
        base_config["margin_ratio"]
    )
    
    # 应用缩放限制
    final_scale = clamp_scale(
        base_scale,
        base_config["min_scale"],
        base_config["max_scale"]
    )
    
    # 计算最优场景矩形
    optimal_scene_rect = calculate_optimal_scene_rect(content_rect, final_scale, view_rect, mode)
    
    # 确定中心点
    if base_config["center_mode"] == "data_center":
        center_point = content_rect.center()
    elif base_config["center_mode"] == "scene_center":
        center_point = optimal_scene_rect.center()
    else:
        center_point = content_rect.center()  # 默认使用数据中心
    
    return {
        "mode": mode,
        "scale": final_scale,
        "center": center_point,
        "scene_rect": optimal_scene_rect,
        "content_rect": content_rect,
        "view_rect": view_rect,
        "config": base_config,
        "debug_info": {
            "base_scale": base_scale,
            "scale_clamped": final_scale != base_scale,
            "margin_ratio": base_config["margin_ratio"]
        }
    }


# ============================================================================
# 安全缩放执行函数
# ============================================================================

def apply_scale_safely(view: QGraphicsView, scale_config: Dict[str, Any], 
                      debug: bool = True) -> bool:
    """
    安全地应用缩放配置到视图
    
    Args:
        view: 目标图形视图
        scale_config: 缩放配置（由calculate_scale_config生成）
        debug: 是否输出调试信息
    
    Returns:
        是否成功应用缩放
    """
    try:
        # 检查缩放锁
        if getattr(view, '_scaling_in_progress', False):
            if debug:
                print(f"⚠️ [缩放管理] 缩放操作正在进行中，跳过新的缩放请求")
            return False
        
        # 设置缩放锁
        view._scaling_in_progress = True
        
        if debug:
            print(f"🎯 [缩放管理] 开始应用缩放配置: {scale_config['mode']}")
            print(f"📐 [缩放管理] 缩放比例: {scale_config['scale']:.3f}")
            print(f"📍 [缩放管理] 中心点: ({scale_config['center'].x():.1f}, {scale_config['center'].y():.1f})")
        
        # 1. 设置场景矩形（不重置变换，避免清除旋转）
        if view.scene:
            view.scene.setSceneRect(scale_config["scene_rect"])
            if debug:
                sr = scale_config["scene_rect"]
                print(f"🎬 [缩放管理] 场景矩形: ({sr.x():.1f}, {sr.y():.1f}) {sr.width():.1f}x{sr.height():.1f}")
        
        # 2. 创建变换：仅缩放（旋转功能已禁用）
        # 旋转功能已全面禁用，注释掉相关代码
        # # from src.pages.main_detection_p1.graphics.core.rotation_stub import get_rotation_manager  # 旋转功能已禁用
        # # rotation_manager = get_rotation_manager()  # 旋转功能已禁用
        
        scale = scale_config["scale"]
        transform = QTransform()
        transform.scale(scale, scale)
        
        # 旋转功能已禁用，直接设置为False
        scale_manager_enabled = False
        scale_manager_angle = 0.0
        
        if debug:
            print(f"🔄 [缩放管理-调试] 旋转配置检查:")
            print(f"   启用状态: {'❌' if not scale_manager_enabled else '✅'} (已全面禁用)")
            print(f"   旋转角度: {scale_manager_angle}°")
        
        # 旋转功能已禁用，跳过旋转应用
        if False:  # scale_manager_enabled:
            old_transform_m11 = transform.m11()
            old_transform_m12 = transform.m12()
            
            transform.rotate(scale_manager_angle)
            
            new_transform_m11 = transform.m11()
            new_transform_m12 = transform.m12()
            
            if debug:
                print(f"🔄 [缩放管理] 应用全局旋转: {scale_manager_angle}°")
                print(f"   旋转前矩阵: m11={old_transform_m11:.3f}, m12={old_transform_m12:.3f}")
                print(f"   旋转后矩阵: m11={new_transform_m11:.3f}, m12={new_transform_m12:.3f}")
        else:
            if debug:
                print(f"⏭️ [缩放管理] 跳过旋转：scale_manager组件已禁用")
        
        # 记录应用前的视图变换
        old_view_transform = view.transform()
        view.setTransform(transform)
        new_view_transform = view.transform()
        
        if debug:
            print(f"📐 [缩放管理] 视图变换更新:")
            print(f"   应用前: m11={old_view_transform.m11():.3f}, m12={old_view_transform.m12():.3f}")
            print(f"   应用后: m11={new_view_transform.m11():.3f}, m12={new_view_transform.m12():.3f}")
            
            # 检查是否真正应用了旋转
            rotation_applied = abs(new_view_transform.m12()) > 0.1  # m12应该非零表示有旋转
            print(f"   旋转验证: {'✅ 已应用' if rotation_applied else '❌ 未检测到旋转'}")
            
            # 检查变换是否为零
            if abs(new_view_transform.m11()) < 0.001 and abs(new_view_transform.m22()) < 0.001:
                print(f"⚠️ [缩放管理] 警告：变换矩阵为零！视图将不可见")
                print(f"   缩放配置: scale={scale:.3f}")
                print(f"   变换对象: {transform}")
                print(f"   视图类型: {type(view).__name__}")
        
        # 4. 居中
        view.centerOn(scale_config["center"])
        
        if debug:
            print(f"✅ [缩放管理] 缩放应用完成")
            
        return True
        
    except Exception as e:
        if debug:
            print(f"❌ [缩放管理] 缩放应用失败: {e}")
        return False
        
    finally:
        # 释放缩放锁
        view._scaling_in_progress = False


# ============================================================================
# 数据加载与缩放一体化函数
# ============================================================================

def load_and_scale_panorama(view: QGraphicsView, hole_collection: HoleCollection,
                           mode: str = "panorama_overview", 
                           custom_params: Optional[Dict] = None,
                           debug: bool = True) -> bool:
    """
    加载数据并应用全景图缩放的一体化函数
    
    Args:
        view: 目标图形视图
        hole_collection: 孔位数据集合
        mode: 缩放模式
        custom_params: 自定义缩放参数
        debug: 是否输出调试信息
    
    Returns:
        是否成功完成加载和缩放
    """
    try:
        if debug:
            print(f"🚀 [全景缩放] 开始加载并缩放: {len(hole_collection)} 个孔位")
        
        # 1. 禁用自动缩放
        disable_auto_scaling(view)
        
        # 2. 加载数据（不触发自动缩放）
        # DEBUG: 小型全景图渲染调试
        print(f"🔍 [DEBUG] 开始调用 view.load_holes")
        print(f"🔍 [DEBUG] view类型: {type(view)}")
        print(f"🔍 [DEBUG] view是否有load_holes方法: {hasattr(view, 'load_holes')}")
        print(f"🔍 [DEBUG] hole_collection类型: {type(hole_collection)}")
        print(f"🔍 [DEBUG] hole_collection大小: {len(hole_collection)}")
        
        view.load_holes(hole_collection)
        
        # 检查数据加载后的场景状态
        if hasattr(view, 'scene'):
            scene = view.scene
            if scene:
                items = scene.items()
                print(f"🔍 [DEBUG] 场景中的图形项数量: {len(items)}")
                print(f"🔍 [DEBUG] 场景边界: {scene.sceneRect()}")
                
                # 检查前几个图形项的类型
                for i, item in enumerate(items[:5]):
                    print(f"🔍 [DEBUG] 图形项 {i}: {type(item)}")
            else:
                print(f"❌ [DEBUG] view没有scene!")
        else:
            print(f"❌ [DEBUG] view没有scene属性!")
        
        if debug:
            print(f"📊 [全景缩放] 数据加载完成")
        
        # 3. 计算数据边界
        data_bounds = hole_collection.get_bounds()
        content_rect = QRectF(
            data_bounds[0], data_bounds[1],
            data_bounds[2] - data_bounds[0], 
            data_bounds[3] - data_bounds[1]
        )
        
        # 4. 获取视图尺寸 - 动态容器大小检测
        view_rect = _get_dynamic_container_size_for_scale_manager(view, mode, debug)
        
        if debug:
            print(f"📏 [全景缩放] 数据边界: {data_bounds}")
            print(f"📺 [全景缩放] 视图尺寸: {view_rect.width()}x{view_rect.height()}")
        
        # 5. 智能选择缩放配置模式
        smart_mode = _select_smart_scaling_mode(view, mode, debug)
        
        # 6. 计算缩放配置
        scale_config = calculate_scale_config(smart_mode, content_rect, view_rect, custom_params)
        
        # 6. 应用缩放
        success = apply_scale_safely(view, scale_config, debug)
        
        if debug:
            if success:
                print(f"🎉 [全景缩放] 全景图缩放完成!")
            else:
                print(f"❌ [全景缩放] 全景图缩放失败!")
        
        return success
        
    except Exception as e:
        if debug:
            print(f"❌ [全景缩放] 加载和缩放过程出错: {e}")
            import traceback
            traceback.print_exc()
        return False


# ============================================================================
# 辅助函数
# ============================================================================

def disable_auto_scaling(view: QGraphicsView):
    """禁用视图的自动缩放功能"""
    view.disable_auto_fit = True
    view.disable_auto_center = True
    
    # 临时禁用可能触发自动缩放的方法
    if hasattr(view, 'fit_to_window_width'):
        view._original_fit_to_window_width = view.fit_to_window_width
        view.fit_to_window_width = lambda: None
    
    if hasattr(view, 'fit_in_view_with_margin'):
        view._original_fit_in_view_with_margin = view.fit_in_view_with_margin
        view.fit_in_view_with_margin = lambda *args, **kwargs: None


def restore_auto_scaling(view: QGraphicsView):
    """恢复视图的自动缩放功能"""
    view.disable_auto_fit = False
    view.disable_auto_center = False
    
    # 恢复原始方法
    if hasattr(view, '_original_fit_to_window_width'):
        view.fit_to_window_width = view._original_fit_to_window_width
        del view._original_fit_to_window_width
    
    if hasattr(view, '_original_fit_in_view_with_margin'):
        view.fit_in_view_with_margin = view._original_fit_in_view_with_margin
        del view._original_fit_in_view_with_margin


def get_view_debug_info(view: QGraphicsView) -> Dict[str, Any]:
    """获取视图的调试信息"""
    transform = view.transform()
    scene_rect = view.scene.sceneRect() if view.scene else QRectF()
    viewport_rect = view.viewport().rect()
    
    return {
        "transform_scale": transform.m11(),
        "scene_rect": {
            "x": scene_rect.x(), "y": scene_rect.y(),
            "width": scene_rect.width(), "height": scene_rect.height()
        },
        "viewport_size": {
            "width": viewport_rect.width(), "height": viewport_rect.height()
        },
        "scene_items_count": len(view.scene.items()) if view.scene else 0,
        "auto_scaling_disabled": getattr(view, 'disable_auto_fit', False),
        "scaling_in_progress": getattr(view, '_scaling_in_progress', False)
    }


# ============================================================================
# 快捷调用函数
# ============================================================================

def apply_panorama_overview_scale(view: QGraphicsView, hole_collection: HoleCollection) -> bool:
    """快捷函数：应用全景图概览缩放"""
    return load_and_scale_panorama(view, hole_collection, "panorama_overview")


def apply_sidebar_panorama_scale(view: QGraphicsView, hole_collection: HoleCollection) -> bool:
    """快捷函数：应用侧边栏全景图缩放 - 针对侧边栏显示优化"""
    return load_and_scale_panorama(view, hole_collection, "sidebar_panorama_overview")


def apply_panorama_sector_scale(view: QGraphicsView, hole_collection: HoleCollection, 
                               sector_center: Optional[QPointF] = None) -> bool:
    """快捷函数：应用全景图扇形缩放"""
    custom_params = {}
    if sector_center:
        custom_params["center_mode"] = "custom"
        custom_params["custom_center"] = sector_center
    
    return load_and_scale_panorama(view, hole_collection, "panorama_sector", custom_params)


def apply_main_macro_scale(view: QGraphicsView, hole_collection: HoleCollection) -> bool:
    """快捷函数：应用主视图宏观缩放"""
    return load_and_scale_panorama(view, hole_collection, "main_macro")


def fix_over_scaled_view(view: QGraphicsView, hole_collection: HoleCollection) -> bool:
    """修复过度缩放的视图"""
    print("🔧 [缩放修复] 检测到过度缩放，正在修复...")
    
    # 强制使用概览模式，确保显示完整内容
    custom_params = {
        "margin_ratio": 0.1,  # 增大边距
        "max_scale": 0.6,     # 降低最大缩放
        "priority": "fix_over_scale"
    }
    
    return load_and_scale_panorama(view, hole_collection, "panorama_overview", custom_params)


# ============================================================================
# 调试和诊断函数
# ============================================================================

def diagnose_scale_issues(view: QGraphicsView, hole_collection: HoleCollection) -> Dict[str, Any]:
    """诊断缩放相关问题"""
    diagnosis = {
        "issues": [],
        "recommendations": [],
        "view_info": get_view_debug_info(view),
        "data_info": {}
    }
    
    # 数据信息
    if hole_collection:
        bounds = hole_collection.get_bounds()
        diagnosis["data_info"] = {
            "hole_count": len(hole_collection),
            "bounds": bounds,
            "data_size": (bounds[2] - bounds[0], bounds[3] - bounds[1])
        }
    
    # 检查常见问题
    transform_scale = diagnosis["view_info"]["transform_scale"]
    scene_rect = diagnosis["view_info"]["scene_rect"]
    viewport_size = diagnosis["view_info"]["viewport_size"]
    
    # 过度缩放检查
    if transform_scale > 3.0:
        diagnosis["issues"].append(f"过度放大：当前缩放比例 {transform_scale:.2f} > 3.0")
        diagnosis["recommendations"].append("使用 fix_over_scaled_view() 函数修复")
    
    # 过小缩放检查 - 针对大型管板调整阈值
    hole_count = diagnosis["data_info"].get("hole_count", 0)
    min_scale_threshold = 0.02 if hole_count > 10000 else 0.1
    if transform_scale < min_scale_threshold:
        diagnosis["issues"].append(f"过度缩小：当前缩放比例 {transform_scale:.2f} < {min_scale_threshold}")
        diagnosis["recommendations"].append("使用 apply_panorama_overview_scale() 重新缩放")
    
    # 场景尺寸检查 - 针对大型管板调整阈值
    max_scene_ratio = 25 if hole_count > 10000 else 10
    if scene_rect["width"] > viewport_size["width"] * max_scene_ratio:
        diagnosis["issues"].append("场景矩形过大，可能导致性能问题")
        diagnosis["recommendations"].append("重新计算场景矩形尺寸")
    
    return diagnosis


# ============================================================================
# 动态容器大小检测（统一缩放管理器版本）
# ============================================================================

def _get_dynamic_container_size_for_scale_manager(view: QGraphicsView, mode: str, debug: bool = False) -> QRectF:
    """
    动态检测容器大小（用于统一缩放管理器）
    
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
        container_context = _detect_container_context_for_scale_manager(view, debug)
        
        # 3. 计算有效显示区域
        effective_rect = _calculate_effective_display_area_for_scale_manager(
            actual_width, actual_height, container_context, mode, debug
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


def _detect_container_context_for_scale_manager(view: QGraphicsView, debug: bool = False) -> Dict[str, Any]:
    """
    检测容器上下文（统一缩放管理器版本）
    
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
        "available_space_ratio": 1.0,
        "container_size": (350, 350)  # 默认尺寸
    }
    
    try:
        # 向上查找父组件来判断上下文
        parent = view.parent()
        while parent:
            parent_class = parent.__class__.__name__
            
            if parent_class == "CompletePanoramaWidget":
                # 获取容器实际尺寸
                container_width = parent.width() if parent.width() > 0 else 350
                container_height = parent.height() if parent.height() > 0 else 350
                context["container_size"] = (container_width, container_height)
                
                # 检查是否是侧边栏全景图（有info_label）
                if hasattr(parent, 'info_label'):
                    context["type"] = "sidebar_panorama"
                    context["has_info_label"] = True
                    context["container_widget"] = parent
                    
                    # 计算info_label占用的空间
                    info_label_height = parent.info_label.height() if parent.info_label.height() > 0 else 25
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
            print(f"   - 容器尺寸: {context['container_size'][0]}x{context['container_size'][1]}")
            if context["has_info_label"]:
                print(f"   - 有info_label，可用空间比例: {context['available_space_ratio']:.2f}")
                
    except Exception as e:
        if debug:
            print(f"⚠️ [容器上下文] 检测失败: {e}")
            
    return context


def _calculate_effective_display_area_for_scale_manager(width: int, height: int, context: Dict[str, Any], 
                                                       mode: str, debug: bool = False) -> QRectF:
    """
    计算有效显示区域（统一缩放管理器版本）
    
    Args:
        width: 视图宽度
        height: 视图高度
        context: 容器上下文
        mode: 缩放模式
        debug: 调试输出
    
    Returns:
        有效显示区域矩形
    """
    try:
        # 默认使用实际尺寸
        effective_width = width
        effective_height = height
        
        # 根据容器类型和模式调整
        if context["type"] == "sidebar_panorama":
            # 侧边栏全景图：考虑info_label的空间占用
            if context["has_info_label"]:
                # 为info_label预留空间（通常在底部）
                info_label_reserved_height = 30  # 预留高度
                effective_height = max(height - info_label_reserved_height, height * 0.8)
                
                # 对于全景图模式，使用容器尺寸进行更精确的计算
                if mode.startswith("panorama"):
                    container_width, container_height = context["container_size"]
                    # 使用容器尺寸，但考虑info_label
                    effective_width = min(container_width, effective_width)
                    effective_height = min(container_height - info_label_reserved_height, effective_height)
                
        elif context["type"] == "mini_panorama":
            # mini_panorama：可以使用全部空间
            if mode.startswith("panorama"):
                container_width, container_height = context["container_size"]
                # mini_panorama通常没有额外的UI元素，可以使用全部空间
                effective_width = min(container_width, effective_width)
                effective_height = min(container_height, effective_height)
            
        # 确保最小尺寸
        effective_width = max(effective_width, 200)
        effective_height = max(effective_height, 200)
        
        # 保持正方形比例（全景图通常是正方形）
        if mode.startswith("panorama"):
            effective_size = min(effective_width, effective_height)
            return QRectF(0, 0, effective_size, effective_size)
        else:
            return QRectF(0, 0, effective_width, effective_height)
        
    except Exception as e:
        if debug:
            print(f"⚠️ [有效区域] 计算失败: {e}")
        return QRectF(0, 0, min(width, height), min(width, height))


def _select_smart_scaling_mode(view: QGraphicsView, requested_mode: str, debug: bool = False) -> str:
    """
    智能选择缩放配置模式
    
    Args:
        view: 图形视图
        requested_mode: 请求的缩放模式
        debug: 调试输出
    
    Returns:
        智能选择的缩放模式
    """
    try:
        # 如果不是全景图模式，直接返回原模式
        if not requested_mode.startswith("panorama"):
            return requested_mode
            
        # 检测容器上下文
        container_context = _detect_container_context_for_scale_manager(view, debug)
        
        # 检测数据规模（通过场景项数量）
        data_scale = _detect_data_scale(view, debug)
        
        # 智能选择模式
        if data_scale == "massive":
            # 超大数据集需要特殊处理
            if container_context["type"] == "mini_panorama" or (
                container_context["type"] == "sidebar_panorama" and 
                container_context.get("container_width", 400) <= 300
            ):
                # 小型全景图+超大数据集 = 使用特殊配置
                smart_mode = "mini_massive_dataset_panorama"
                if debug:
                    print(f"🧠 [智能模式] 检测到小型全景图+超大数据集，使用: {smart_mode}")
            else:
                # 常规全景图+超大数据集
                smart_mode = "massive_dataset_panorama"
                if debug:
                    print(f"🧠 [智能模式] 检测到超大数据集，使用: {smart_mode}")
                    
        elif container_context["type"] == "sidebar_panorama":
            smart_mode = "sidebar_panorama_overview"
            if debug:
                print(f"🧠 [智能模式] 检测到侧边栏全景图，使用: {smart_mode}")
                
        elif container_context["type"] == "mini_panorama":
            smart_mode = "mini_panorama_overview"
            if debug:
                print(f"🧠 [智能模式] 检测到小型全景图，使用: {smart_mode}")
                
        else:
            # 未知类型，使用原始模式
            smart_mode = requested_mode
            if debug:
                print(f"🧠 [智能模式] 未知容器类型，使用原始模式: {smart_mode}")
                
        return smart_mode
        
    except Exception as e:
        if debug:
            print(f"⚠️ [智能模式] 选择失败，使用原始模式: {e}")
        return requested_mode


def _detect_data_scale(view: QGraphicsView, debug: bool = False) -> str:
    """
    检测数据规模
    
    Args:
        view: 图形视图
        debug: 调试输出
    
    Returns:
        数据规模类型: "small", "medium", "large", "massive"
    """
    try:
        # 通过场景项数量检测数据规模
        if hasattr(view, 'scene') and view.scene:
            item_count = len(view.scene.items())
        else:
            item_count = 0
            
        # 或者通过hole_items检测
        if hasattr(view, 'hole_items') and view.hole_items:
            hole_count = len(view.hole_items)
        else:
            hole_count = 0
            
        # 使用较大的数量作为参考
        data_count = max(item_count, hole_count)
        
        if data_count >= 20000:
            scale_type = "massive"
        elif data_count >= 5000:
            scale_type = "large" 
        elif data_count >= 1000:
            scale_type = "medium"
        else:
            scale_type = "small"
            
        if debug:
            print(f"📊 [数据规模] 检测: {data_count} 项 -> {scale_type}")
            
        return scale_type
        
    except Exception as e:
        if debug:
            print(f"⚠️ [数据规模] 检测失败: {e}")
        return "medium"