"""
全景图控制器 - 重构版
使用新架构和依赖注入模式
将原有的多项职责分离
"""

from typing import Optional
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QColor

from src.core_business.graphics.sector_types import SectorQuadrant
from src.core_business.models.hole_data import HoleStatus
from src.modules.panorama_view.core import PanoramaDIContainer
from src.modules.panorama_view.adapters import CompletePanoramaWidgetAdapter
from src.modules.panorama_view.core import PanoramaEventBus


class PanoramaController(QObject):
    """全景图控制器 - 重构版，使用事件总线和依赖注入"""
    
    # 信号
    sector_clicked = Signal(SectorQuadrant)  # 扇形点击信号
    log_message = Signal(str)  # 日志消息信号
    
    def __init__(self, sidebar_panorama=None, dynamic_sector_display=None, parent=None):
        super().__init__(parent)
        
        # 创建依赖注入容器和事件总线
        self.di_container = PanoramaDIContainer()
        self.event_bus = PanoramaEventBus()
        
        # 使用适配器包装旧组件以保持兼容性
        if sidebar_panorama:
            self.sidebar_panorama = sidebar_panorama
        else:
            # 创建新的全景图组件
            self.sidebar_panorama = CompletePanoramaWidgetAdapter()
        
        self.dynamic_sector_display = dynamic_sector_display
        
        # 同步计数器（保留用于调试）
        self._sync_debug_counter = 0
        self._mini_sync_counter = 0
        self._sync_error_count = 0
        self._max_sync_errors = 10
        
        # 连接事件总线
        self._setup_event_connections()
        
        # 连接全景图点击信号
        if self.sidebar_panorama:
            self.sidebar_panorama.sector_clicked.connect(self.on_panorama_sector_clicked)
    
    def _setup_event_connections(self):
        """设置事件总线连接"""
        # 监听状态更新事件
        self.event_bus.subscribe('hole_status_updated', self._on_hole_status_updated)
        # 监听扇形高亮事件
        self.event_bus.subscribe('sector_highlight_requested', self._on_sector_highlight_requested)
        # 监听同步请求事件
        self.event_bus.subscribe('panorama_sync_requested', self._on_panorama_sync_requested)
    
    def _on_hole_status_updated(self, data):
        """处理孔位状态更新事件"""
        hole_id = data.get('hole_id')
        status = data.get('status')
        color = data.get('color')
        
        if hole_id and status:
            self.synchronize_panorama_status(hole_id, status, color)
    
    def _on_sector_highlight_requested(self, data):
        """处理扇形高亮请求事件"""
        sector = data.get('sector')
        if sector:
            self.highlight_panorama_sector(sector)
    
    def _on_panorama_sync_requested(self, data):
        """处理全景图同步请求事件"""
        hole_id = data.get('hole_id')
        color = data.get('color')
        if hole_id and color:
            self.update_panorama_hole_status(hole_id, color)
    
    def publish_hole_status_update(self, hole_id: str, status: str, color=None):
        """发布孔位状态更新事件"""
        self.event_bus.publish('hole_status_updated', {
            'hole_id': hole_id,
            'status': status,
            'color': color
        })
    
    def publish_sector_highlight(self, sector: SectorQuadrant):
        """发布扇形高亮请求事件"""
        self.event_bus.publish('sector_highlight_requested', {
            'sector': sector
        })
    
    def publish_panorama_sync(self, hole_id: str, color):
        """发布全景图同步请求事件"""
        self.event_bus.publish('panorama_sync_requested', {
            'hole_id': hole_id,
            'color': color
        })
    
    def test_panorama_highlights(self):
        """测试全景图高亮功能 (快捷键: Ctrl+H)"""
        try:
            print("🧪 [测试] 开始全面诊断全景图系统...")
            
            # 1. 检查全景图组件
            if self.sidebar_panorama:
                print(f"✅ [测试] 找到侧边栏全景图")
                print(f"   - 类型: {type(self.sidebar_panorama)}")
                print(f"   - 场景存在: {hasattr(self.sidebar_panorama.panorama_view, 'scene') and self.sidebar_panorama.panorama_view.scene is not None}")
                
                # 2. 检查数据状态
                if self.sidebar_panorama.hole_collection:
                    print(f"✅ [测试] 全景图有数据: {len(self.sidebar_panorama.hole_collection)} 个孔位")
                    
                    # 3. 检查几何计算
                    print(f"   - center_point: {self.sidebar_panorama.center_point}")
                    print(f"   - panorama_radius: {self.sidebar_panorama.panorama_radius}")
                    
                    # 4. 重新计算并创建高亮
                    self.sidebar_panorama._calculate_panorama_geometry()
                    self.sidebar_panorama._create_sector_highlights()
                    
                    # 5. 检查高亮状态
                    print(f"   - 高亮字典大小: {len(self.sidebar_panorama.sector_highlights)}")
                    for sector, highlight in self.sidebar_panorama.sector_highlights.items():
                        print(f"     {sector.value}: {highlight}")
                    
                    # 6. 测试高亮功能
                    if hasattr(self.sidebar_panorama, 'test_highlight_all_sectors'):
                        print("🧪 [测试] 执行全扇形高亮测试...")
                        self.sidebar_panorama.test_highlight_all_sectors()
                    
                    # 7. 检查信号连接
                    print(f"   - sector_clicked 信号: {hasattr(self.sidebar_panorama, 'sector_clicked')}")
                else:
                    print(f"❌ [测试] 全景图没有数据")
                    print(f"   - hole_collection: {self.sidebar_panorama.hole_collection}")
            else:
                print(f"❌ [测试] 没有找到侧边栏全景图")
        except Exception as e:
            print(f"❌ [测试] 全景图诊断失败: {e}")
    
    def highlight_panorama_sector(self, sector):
        """高亮左侧全景图中对应的扇形
        
        Args:
            sector: 要高亮的扇形区域
        """
        try:
            if not self.sidebar_panorama:
                self.log_message.emit("⚠️ 左侧全景图组件不存在，无法高亮扇形")
                return
            
            # 检查sidebar_panorama是否有highlight_sector方法
            if not hasattr(self.sidebar_panorama, 'highlight_sector'):
                self.log_message.emit("⚠️ 左侧全景图组件没有highlight_sector方法")
                return
            
            # 执行高亮
            self.sidebar_panorama.highlight_sector(sector)
            self.log_message.emit(f"✨ 左侧全景图已高亮 {sector.value}")
        except Exception as e:
            self.log_message.emit(f"❌ 高亮左侧全景图扇形失败: {e}")
    
    def clear_panorama_sector_highlight(self):
        """清空左侧全景图的扇形高亮"""
        try:
            if self.sidebar_panorama:
                # 优先使用专用的清空方法
                if hasattr(self.sidebar_panorama, 'clear_sector_highlight'):
                    self.sidebar_panorama.clear_sector_highlight()
                    self.log_message.emit("✨ 已清空左侧全景图扇形高亮")
                # 备用方法：手动清空
                elif hasattr(self.sidebar_panorama, 'current_highlighted_sector'):
                    self.sidebar_panorama.current_highlighted_sector = None
                    # 隐藏所有高亮项
                    if hasattr(self.sidebar_panorama, 'sector_highlights'):
                        for highlight in self.sidebar_panorama.sector_highlights.values():
                            highlight.setVisible(False)
                    self.log_message.emit("✨ 已清空左侧全景图扇形高亮")
        except Exception as e:
            self.log_message.emit(f"❌ 清空左侧全景图扇形高亮失败: {e}")
    
    def debug_sidebar_panorama_transform(self):
        """调试侧边栏全景图的变换"""
        if self.sidebar_panorama:
            if hasattr(self.sidebar_panorama, 'panorama_view'):
                transform = self.sidebar_panorama.panorama_view.transform()
                print(f"🔍 [侧边栏全景图变换] m11={transform.m11():.3f}, m12={transform.m12():.3f}")
                print(f"🔍 [侧边栏全景图变换] m21={transform.m21():.3f}, m22={transform.m22():.3f}")
                if abs(transform.m12()) > 0.001 or abs(transform.m21()) > 0.001:
                    print("✅ [侧边栏全景图变换] 检测到旋转")
                else:
                    print("❌ [侧边栏全景图变换] 未检测到旋转")
                
                # 手动旋转测试（已禁用）
                for angle in [0, 90, 180, 270]:
                    if True:  # 禁用旋转功能
                        print(f"🔧 [侧边栏全景图] 尝试手动应用 {angle}° 旋转...")
                        
                        # 获取当前变换并应用旋转
                        current_transform = self.sidebar_panorama.panorama_view.transform()
                        # current_transform.rotate(angle)  # 禁用实际旋转
                        self.sidebar_panorama.panorama_view.setTransform(current_transform)
                        
                        # 验证变换是否成功
                        new_transform = self.sidebar_panorama.panorama_view.transform()
                        print(f"🔍 [手动旋转] 新变换: m11={new_transform.m11():.3f}, m12={new_transform.m12():.3f}")
                        
                        # 强制刷新
                        if True:  # 强制刷新
                            self.sidebar_panorama.panorama_view.viewport().update()
                            self.sidebar_panorama.panorama_view.scene.update()
                            self.sidebar_panorama.panorama_view.repaint()
                            self.sidebar_panorama.update()
                            print("🔄 [手动旋转] 已强制刷新侧边栏全景图")
                    else:
                        print("⚠️ [侧边栏全景图] 旋转功能已全面禁用")
            else:
                print("❌ [侧边栏全景图] 没有 panorama_view 属性")
        else:
            print("❌ [侧边栏全景图] 组件不存在")
    
    def synchronize_panorama_status(self, hole_id: str, status: str, color):
        """统一的全景图同步机制（包含侧边栏全景图和小型全景图）"""
        print(f"🔄 [调试] _synchronize_panorama_status 被调用: {hole_id} -> {status}")
        
        # 调试信息
        print(f"  - hasattr(self, 'sidebar_panorama'): {self.sidebar_panorama is not None}")
        print(f"  - self.sidebar_panorama is not None: {self.sidebar_panorama is not None}")
        
        try:
            # 将颜色转换为状态枚举
            if isinstance(color, QColor):
                r, g, b = color.red(), color.green(), color.blue()
                if (r, g, b) == (144, 238, 144):  # 浅绿色 - 已完成
                    hole_status = HoleStatus.COMPLETED
                elif (r, g, b) == (255, 165, 0):  # 橙色 - 进行中
                    hole_status = HoleStatus.IN_PROGRESS
                elif (r, g, b) == (255, 99, 71):  # 红色 - 有缺陷
                    hole_status = HoleStatus.DEFECTIVE
                elif (r, g, b) == (169, 169, 169):  # 灰色 - 跳过
                    hole_status = HoleStatus.SKIPPED
                else:
                    hole_status = HoleStatus.PENDING  # 默认待检测
            else:
                hole_status = HoleStatus.PENDING
            
            # 同步到侧边栏全景图
            if self.sidebar_panorama:
                self.sidebar_panorama.update_hole_status(hole_id, hole_status)
            
            # 同步到小型全景图（关键修复！）
            if self.dynamic_sector_display:
                if hasattr(self.dynamic_sector_display, 'update_mini_panorama_hole_status'):
                    self.dynamic_sector_display.update_mini_panorama_hole_status(hole_id, hole_status)
                    
                    # 调试计数器
                    self._mini_sync_counter += 1
                    # 每5次输出一次小型全景图同步信息
                    if self._mini_sync_counter % 5 == 0:
                        print(f"🔗 [同步-小型] 主视图 -> 小型全景图: 已同步 {self._mini_sync_counter} 个孔位 (最新: {hole_id} -> {status})")
                else:
                    print(f"❌ [同步-小型] dynamic_sector_display 没有 update_mini_panorama_hole_status 方法")
                    
                # 详细调试小型全景图状态
                self._debug_mini_panorama_status(hole_id)
            
            # 调试计数器（每100次输出一次侧边栏全景图同步信息）
            self._sync_debug_counter += 1
            if self._sync_debug_counter % 100 == 0:
                print(f"🔗 [同步] 主视图 -> 全景图: 已同步 {self._sync_debug_counter} 个孔位")
                
        except Exception as e:
            self._sync_error_count += 1
            if self._sync_error_count <= self._max_sync_errors:
                self.log_message.emit(f"❌ 全景图同步失败 {hole_id}: {e}")
            elif self._sync_error_count == self._max_sync_errors + 1:
                self.log_message.emit("❌ 全景图同步错误过多，后续错误将被静默处理")
    
    def _debug_mini_panorama_status(self, hole_id: str):
        """调试小型全景图状态"""
        if not self.dynamic_sector_display:
            print(f"❌ [小型全景图] dynamic_sector_display 不存在")
            return
            
        print(f"✅ [小型全景图] dynamic_sector_display 存在: {type(self.dynamic_sector_display)}")
        
        # 检查 mini_panorama 的存在性和状态
        if hasattr(self.dynamic_sector_display, 'mini_panorama'):
            mini_panorama = self.dynamic_sector_display.mini_panorama
            print(f"✅ [小型全景图] mini_panorama 存在: {type(mini_panorama)}")
            
            if hasattr(mini_panorama, 'hole_items'):
                hole_items_count = len(mini_panorama.hole_items) if mini_panorama.hole_items else 0
                print(f"📊 [小型全景图] hole_items 数量: {hole_items_count}")
                
                if hole_id in mini_panorama.hole_items:
                    print(f"✅ [小型全景图] 找到目标孔位 {hole_id} 在 hole_items 中")
                else:
                    print(f"❌ [小型全景图] 目标孔位 {hole_id} 不在 hole_items 中")
            else:
                print(f"❌ [小型全景图] mini_panorama 没有 hole_items 属性")
            
            if hasattr(mini_panorama, 'scene'):
                scene = mini_panorama.scene
                if scene:
                    scene_items_count = len(scene.items()) if scene.items() else 0
                    print(f"📊 [小型全景图] 场景图形项数量: {scene_items_count}")
                else:
                    print(f"❌ [小型全景图] scene 为 None")
            else:
                print(f"❌ [小型全景图] mini_panorama 没有场景或场景为空")
        else:
            print(f"❌ [小型全景图] dynamic_sector_display 没有 mini_panorama 属性")
    
    def update_panorama_hole_status(self, hole_id: str, color):
        """同步更新侧边栏全景图中的孔位状态（使用批量更新机制）"""
        print(f"🔍 [全景更新] 开始更新孔位 {hole_id}, 颜色: {color}")
        
        if not self.sidebar_panorama:
            print(f"❌ [全景更新] sidebar_panorama 不存在或为空")
            return
        
        print(f"✅ [全景更新] sidebar_panorama 存在: {type(self.sidebar_panorama)}")
        
        try:
            # 将颜色转换为状态枚举
            if isinstance(color, QColor):
                r, g, b = color.red(), color.green(), color.blue()
                color_name = color.name()
                print(f"🎨 [全景更新] 颜色: {color_name} RGB({r}, {g}, {b})")
                
                # 颜色到状态的映射
                if (r, g, b) == (144, 238, 144):  # 浅绿色 - 已完成
                    status = HoleStatus.COMPLETED
                    print(f"✅ [全景更新] 识别为已完成状态")
                elif (r, g, b) == (255, 165, 0):  # 橙色 - 进行中  
                    status = HoleStatus.IN_PROGRESS
                    print(f"🔄 [全景更新] 识别为进行中状态")
                elif (r, g, b) == (255, 99, 71):  # 红色 - 有缺陷
                    status = HoleStatus.DEFECTIVE
                    print(f"❌ [全景更新] 识别为缺陷状态")
                elif (r, g, b) == (169, 169, 169):  # 灰色 - 跳过
                    status = HoleStatus.SKIPPED
                    print(f"⏭️ [全景更新] 识别为跳过状态")
                elif (r, g, b) == (128, 128, 128):  # 深灰色 - 待检测
                    status = HoleStatus.PENDING
                    print(f"⏳ [全景更新] 识别为待检测状态")
                else:
                    status = HoleStatus.PENDING  # 默认待检测
                    if self._sync_debug_counter % 50 == 0:  # 每50次输出一次未知颜色
                        print(f"⚠️ [全景更新] 未知颜色，使用默认状态: {color_name} RGB({r}, {g}, {b})")
            else:
                status = HoleStatus.PENDING
                print(f"⚠️ [全景更新] 颜色不是QColor类型: {type(color)}")
            
            # 输出推断的状态
            print(f"📋 [全景更新] 推断状态: {status.value}")
            
            # 检查全景图组件是否有update_hole_status方法
            if hasattr(self.sidebar_panorama, 'update_hole_status'):
                print(f"✅ [全景更新] 调用 sidebar_panorama.update_hole_status({hole_id}, {status.value})")
                # 调用全景图的状态更新方法
                self.sidebar_panorama.update_hole_status(hole_id, status)
                print(f"✅ [全景更新] 状态更新完成")
            else:
                print(f"❌ [全景更新] sidebar_panorama 没有 update_hole_status 方法")
            
            # 同步小型全景图
            self._debug_mini_panorama_status(hole_id)
            
        except Exception as e:
            print(f"❌ [全景更新] 更新失败: {e}")
    
    def sync_panorama_highlight(self, sector):
        """同步全景图高亮（使用统一定时器系统）"""
        try:
            if not self.sidebar_panorama:
                return
            
            self.sidebar_panorama.highlight_sector(sector)
            self.log_message.emit(f"✅ [统一定时器] 全景高亮: {sector.value}")
        except Exception as e:
            self.log_message.emit(f"❌ [统一定时器] 全景高亮失败: {e}")
    
    def async_sync_panorama_highlight(self, sector):
        """异步同步全景预览高亮，避免阻塞扇形切换"""
        try:
            if not self.sidebar_panorama:
                return
            
            # 避免重复高亮同一个扇形
            if (hasattr(self.sidebar_panorama, 'current_highlighted_sector') and 
                self.sidebar_panorama.current_highlighted_sector == sector):
                return
            
            self.sidebar_panorama.highlight_sector(sector) 
            self.log_message.emit(f"✅ [异步同步] 全景高亮: {sector.value}")
        except Exception as e:
            self.log_message.emit(f"❌ [异步同步] 全景高亮失败: {e}")
    
    def force_sync_panorama_highlight(self, sector):
        """强制同步全景预览高亮（保留原方法用于兼容性）"""
        try:
            if not self.sidebar_panorama:
                self.log_message.emit(f"❌ [强制同步] 全景预览组件不存在")
                return
            
            # 强制重新创建高亮项（如果不存在）
            if not hasattr(self.sidebar_panorama, 'sector_highlights') or not self.sidebar_panorama.sector_highlights:
                self.log_message.emit(f"⚠️ [强制同步] 全景高亮项不存在，重新创建")
                
            self.sidebar_panorama.highlight_sector(sector) 
            self.log_message.emit(f"✅ [强制同步] 全景高亮: {sector.value}")
            
            # 额外的强制措施：重新创建高亮并延迟高亮
            if not self.sidebar_panorama.sector_highlights:
                self.sidebar_panorama._create_sector_highlights()
                QTimer.singleShot(100, lambda: self.sidebar_panorama.highlight_sector(sector))
                
        except Exception as e:
            self.log_message.emit(f"❌ [强制同步] 全景高亮失败: {e}")
        
        # 调试信息：检查扇形边界
        try:
            # 全景预览的扇形理解
            if hasattr(self.sidebar_panorama, 'sector_highlights') and sector in self.sidebar_panorama.sector_highlights:
                panorama_highlight = self.sidebar_panorama.sector_highlights[sector]
                if hasattr(panorama_highlight, 'sector_bounds') and panorama_highlight.sector_bounds:
                    self.log_message.emit(f"🎨 [调试] 全景扇形 {sector.value} 边界: {panorama_highlight.sector_bounds}")
        except Exception as e:
            pass  # 忽略调试错误
    
    def manual_sync_panorama(self, sector):
        """手动同步全景预览高亮（用于模拟进度）"""
        self.log_message.emit(f"🔧 [模拟] 手动同步全景预览: {sector.value}")
        
        if self.sidebar_panorama:
            # 如果高亮项不存在，重新创建
            if not hasattr(self.sidebar_panorama, 'sector_highlights') or not self.sidebar_panorama.sector_highlights:
                self.log_message.emit(f"⚠️ [模拟] 全景高亮项不存在，重新创建")
                self.sidebar_panorama._create_sector_highlights()
                QTimer.singleShot(100, lambda: self.sidebar_panorama.highlight_sector(sector))
            else:
                self.sidebar_panorama.highlight_sector(sector)
                self.log_message.emit(f"✅ [模拟] 全景预览已同步高亮: {sector.value}")
    
    def on_panorama_sector_clicked(self, sector):
        """处理全景图扇形点击事件"""
        try:
            print(f"🔍 [DEBUG PanoramaController] on_panorama_sector_clicked 被调用: {sector}")
            
            # 发出点击信号，让主窗口处理扇形切换
            self.sector_clicked.emit(sector)
            self.log_message.emit(f"🖱️ 通过全景图点击切换到扇形: {sector.value}")
            
        except Exception as e:
            self.log_message.emit(f"❌ 全景图扇形点击处理失败: {e}")