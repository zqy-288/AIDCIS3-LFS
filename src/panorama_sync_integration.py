"""
全景图同步集成方案
用于将数据库驱动的全景图更新机制集成到主窗口
"""

from modules.models import DatabaseManager
from aidcis2.data_management.panorama_sync_manager import PanoramaSyncManager


class PanoramaSyncIntegration:
    """全景图同步集成助手类 - 适配新的模块化架构"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.db_manager = None
        self.sync_manager = None
        self.panorama_widget = None
        
    def setup(self):
        """设置全景图同步系统"""
        print("🔧 设置全景图同步系统（新架构）...")
        
        # 1. 初始化数据库管理器
        if not hasattr(self.main_window, 'db_manager'):
            self.main_window.db_manager = DatabaseManager()
            self.main_window.db_manager.create_tables()
            print("✅ 数据库管理器已初始化")
        
        self.db_manager = self.main_window.db_manager
        
        # 2. 创建或获取全景图组件
        self.panorama_widget = self._setup_panorama_widget()
        if not self.panorama_widget:
            print("❌ 无法创建全景图组件")
            return False
        
        # 3. 创建同步管理器
        self.sync_manager = PanoramaSyncManager(
            self.db_manager, 
            self.panorama_widget
        )
        print("✅ 同步管理器已创建")
        
        # 4. 关联组件
        if hasattr(self.panorama_widget, 'set_panorama_sync_manager'):
            self.panorama_widget.set_panorama_sync_manager(self.sync_manager)
            print("✅ 全景图与同步管理器已关联")
        
        # 5. 修改更新方法以使用数据库
        self._patch_update_methods()
        
        # 6. 启动自动同步
        self.sync_manager.start_sync(1000)  # 1秒间隔
        if hasattr(self.panorama_widget, 'enable_db_sync'):
            self.panorama_widget.enable_db_sync(True)
        print("✅ 自动同步已启动（1秒间隔）")
        
        return True
    
    def _setup_panorama_widget(self):
        """设置全景图组件到新架构中"""
        try:
            from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
            
            # 检查是否已存在全景图组件
            if hasattr(self.main_window, 'panorama_widget'):
                print("✅ 使用现有全景图组件")
                return self.main_window.panorama_widget
            
            # 创建新的全景图组件
            panorama_widget = CompletePanoramaWidget()
            print("✅ 创建新全景图组件")
            
            # 将全景图添加到信息面板
            if hasattr(self.main_window, 'info_panel'):
                self._add_panorama_to_info_panel(panorama_widget)
                
            # 保存引用
            self.main_window.panorama_widget = panorama_widget
            
            return panorama_widget
            
        except Exception as e:
            print(f"❌ 创建全景图组件失败: {e}")
            return None
    
    def _add_panorama_to_info_panel(self, panorama_widget):
        """将全景图添加到信息面板"""
        try:
            from PySide6.QtWidgets import QGroupBox, QVBoxLayout
            
            # 创建全景图分组
            panorama_group = QGroupBox("全景图")
            panorama_layout = QVBoxLayout(panorama_group)
            panorama_layout.addWidget(panorama_widget)
            
            # 添加到信息面板
            info_panel_layout = self.main_window.info_panel.layout()
            info_panel_layout.insertWidget(2, panorama_group)  # 在统计信息后插入
            
            print("✅ 全景图已添加到信息面板")
            
        except Exception as e:
            print(f"❌ 添加全景图到信息面板失败: {e}")
    
    def _patch_update_methods(self):
        """修改更新方法以使用数据库"""
        # 保存原始方法
        original_update = self.main_window._update_panorama_hole_status
        
        def new_update_panorama_hole_status(hole_id, color):
            """新的更新方法：使用数据库"""
            # 从颜色推断状态
            color_name = color.name() if hasattr(color, 'name') else str(color)
            
            # 状态映射
            status_map = {
                "#00FF00": "qualified",    # 绿色
                "#4CAF50": "qualified",    # 另一种绿色
                "#FF0000": "defective",    # 红色
                "#F44336": "defective",    # 另一种红色
                "#0000FF": "processing",   # 蓝色
                "#2196F3": "processing",   # 另一种蓝色
                "#FFA500": "blind",        # 橙色
                "#FF9800": "blind",        # 另一种橙色
                "#800080": "tie_rod",      # 紫色
                "#9C27B0": "tie_rod",      # 另一种紫色
            }
            
            status = status_map.get(color_name.upper(), "pending")
            
            # 更新到数据库
            success = self.db_manager.update_hole_status(
                hole_id=hole_id,
                new_status=status,
                update_source="simulation",
                operator_id="system"
            )
            
            if success:
                self.main_window.log_message(f"💾 状态已保存到数据库: {hole_id} -> {status}")
            
            # 仍然调用原始方法以保持兼容性
            original_update(hole_id, color)
        
        # 替换方法
        self.main_window._update_panorama_hole_status = new_update_panorama_hole_status
        print("✅ 更新方法已修改为使用数据库")
    
    def get_sync_status(self):
        """获取同步状态"""
        if not self.sync_manager:
            return None
        
        return self.sync_manager.get_sync_stats()
    
    def force_sync_all(self):
        """强制同步所有孔位状态到全景图"""
        if not self.db_manager or not self.main_window.hole_collection:
            print("❌ 无法执行全量同步：缺少必要组件")
            return
        
        print("🔄 开始全量同步所有孔位到全景图...")
        
        # 获取所有孔位
        all_holes = self.main_window.hole_collection.holes
        batch_size = 50
        updated_count = 0
        
        # 分批更新
        hole_items = list(all_holes.items())
        for i in range(0, len(hole_items), batch_size):
            batch = hole_items[i:i+batch_size]
            
            for hole_id, hole in batch:
                # 获取当前状态（从界面或默认值）
                status = hole.status.value if hasattr(hole.status, 'value') else 'pending'
                
                # 更新到数据库
                self.db_manager.update_hole_status(
                    hole_id=hole_id,
                    new_status=status,
                    update_source="sync_all",
                    operator_id="system",
                    batch_id=f"sync_all_{i//batch_size}"
                )
                updated_count += 1
            
            # 触发同步
            self.sync_manager.force_sync()
            print(f"   已同步 {updated_count}/{len(all_holes)} 个孔位...")
        
        print(f"✅ 全量同步完成：{updated_count} 个孔位")


def integrate_panorama_sync(main_window):
    """便捷函数：集成全景图同步到主窗口"""
    integration = PanoramaSyncIntegration(main_window)
    success = integration.setup()
    
    if success:
        # 添加到主窗口以便后续使用
        main_window.panorama_sync_integration = integration
        
        # 添加菜单项或按钮（可选）
        # main_window.add_sync_menu_items()
        
    return success


# 使用示例：
# 在main_window.py的__init__方法末尾添加：
# from panorama_sync_integration import integrate_panorama_sync
# integrate_panorama_sync(self)