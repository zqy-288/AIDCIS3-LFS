"""导航服务模块"""
import logging
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QTabWidget


class NavigationService(QObject):
    """
    导航服务
    负责在不同视图间切换和导航
    """
    
    # 信号定义
    navigate_to_realtime = Signal(str)  # 导航到实时监控，传递孔位ID
    navigate_to_history = Signal(str)   # 导航到历史数据，传递孔位ID
    log_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # UI组件引用
        self.tab_widget: Optional[QTabWidget] = None
        self.main_window = None
        
    def set_components(self, tab_widget: QTabWidget, main_window):
        """设置组件引用"""
        self.tab_widget = tab_widget
        self.main_window = main_window
        
    def goto_realtime(self, hole_id: str):
        """导航到实时监控界面"""
        try:
            self.log_message.emit(f"🔄 导航到实时监控: {hole_id}")
            
            # 检查是否支持该孔位
            if hole_id not in ["H00001", "H00002"]:
                QMessageBox.information(
                    self.main_window,
                    "提示",
                    f"{hole_id} 暂无实时监控数据\n当前仅支持 H00001 和 H00002"
                )
                return
                
            # 切换到实时监控标签
            if self.tab_widget:
                realtime_index = self._find_tab_index("实时监控")
                if realtime_index >= 0:
                    self.tab_widget.setCurrentIndex(realtime_index)
                    
                    # 获取实时监控标签页
                    realtime_widget = self.tab_widget.widget(realtime_index)
                    if hasattr(realtime_widget, 'load_hole_data'):
                        # 加载指定孔位的数据
                        realtime_widget.load_hole_data(hole_id)
                        self.log_message.emit(f"✅ 已加载 {hole_id} 的实时监控数据")
                    
            # 发送导航信号
            self.navigate_to_realtime.emit(hole_id)
            
        except Exception as e:
            self.logger.error(f"导航到实时监控失败: {str(e)}", exc_info=True)
            self.log_message.emit(f"❌ 导航失败: {str(e)}")
            
    def goto_history(self, hole_id: str):
        """导航到历史数据界面"""
        try:
            self.log_message.emit(f"📊 导航到历史数据: {hole_id}")
            
            # 检查是否支持该孔位
            if hole_id not in ["H00001", "H00002"]:
                QMessageBox.information(
                    self.main_window,
                    "提示", 
                    f"{hole_id} 暂无历史数据\n当前仅支持 H00001 和 H00002"
                )
                return
                
            # 切换到历史数据标签
            if self.tab_widget:
                history_index = self._find_tab_index("历史数据")
                if history_index >= 0:
                    self.tab_widget.setCurrentIndex(history_index)
                    
                    # 获取历史数据标签页
                    history_widget = self.tab_widget.widget(history_index)
                    if hasattr(history_widget, 'load_hole_data'):
                        # 加载指定孔位的数据
                        history_widget.load_hole_data(hole_id)
                        self.log_message.emit(f"✅ 已加载 {hole_id} 的历史数据")
                        
            # 发送导航信号
            self.navigate_to_history.emit(hole_id)
            
        except Exception as e:
            self.logger.error(f"导航到历史数据失败: {str(e)}", exc_info=True)
            self.log_message.emit(f"❌ 导航失败: {str(e)}")
            
    def navigate_to_tab(self, tab_name: str):
        """导航到指定标签页"""
        if not self.tab_widget:
            return
            
        index = self._find_tab_index(tab_name)
        if index >= 0:
            self.tab_widget.setCurrentIndex(index)
            self.log_message.emit(f"切换到标签页: {tab_name}")
            
    def _find_tab_index(self, tab_name: str) -> int:
        """查找标签页索引"""
        if not self.tab_widget:
            return -1
            
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_name:
                return i
        return -1
        
    def get_current_tab_name(self) -> str:
        """获取当前标签页名称"""
        if not self.tab_widget:
            return ""
            
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            return self.tab_widget.tabText(current_index)
        return ""