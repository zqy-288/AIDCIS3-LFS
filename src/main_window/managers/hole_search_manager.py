"""孔位搜索管理器"""
import logging
from typing import Optional, List
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QCompleter, QApplication
from PySide6.QtCore import QStringListModel

from aidcis2.models.hole_data import HoleData, HoleCollection


class HoleSearchManager(QObject):
    """
    孔位搜索管理器
    负责搜索功能和自动完成
    """
    
    # 信号定义
    search_completed = Signal(list)  # 搜索结果列表
    hole_selected = Signal(object)  # 选中的孔位
    log_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 数据
        self.hole_collection: Optional[HoleCollection] = None
        self.selected_hole: Optional[HoleData] = None
        
        # 自动完成
        self.completer = None
        self.completer_model = QStringListModel()
        
        # UI组件引用
        self.search_input = None
        self.graphics_view = None
        
    def set_components(self, search_input, graphics_view):
        """设置UI组件引用"""
        self.search_input = search_input
        self.graphics_view = graphics_view
        
        # 设置自动完成
        if self.search_input:
            self._setup_completer()
            
    def set_hole_collection(self, hole_collection: HoleCollection):
        """设置孔位集合"""
        self.hole_collection = hole_collection
        self.update_completer_data()
        
    def _setup_completer(self):
        """设置搜索自动完成器"""
        self.completer = QCompleter()
        self.completer.setModel(self.completer_model)
        
        # 配置补全器
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setMaxVisibleItems(10)
        
        # 设置到搜索框
        if self.search_input:
            self.search_input.setCompleter(self.completer)
            
        # 连接信号
        self.completer.activated.connect(self._on_completer_activated)
        
    def update_completer_data(self):
        """更新自动完成数据"""
        if not self.hole_collection:
            self.completer_model.setStringList([])
            return
            
        # 获取所有孔位ID
        hole_ids = [hole.hole_id for hole in self.hole_collection.holes.values()]
        hole_ids.sort()  # 按字母顺序排序
        
        # 更新补全数据
        self.completer_model.setStringList(hole_ids)
        self.logger.debug(f"更新自动补全数据: {len(hole_ids)} 个孔位")
        
    def _on_completer_activated(self, text):
        """处理自动完成选择"""
        if self.search_input:
            self.search_input.setText(text)
        self.perform_search(text)
        
    def perform_search(self, search_text: str = None):
        """执行搜索"""
        if search_text is None and self.search_input:
            search_text = self.search_input.text().strip()
            
        if not search_text:
            # 清空搜索
            if self.graphics_view:
                self.graphics_view.clear_search_highlight()
            self.log_message.emit("清空搜索")
            self.search_completed.emit([])
            return
            
        if not self.hole_collection:
            self.log_message.emit("没有加载孔位数据")
            self.search_completed.emit([])
            return
            
        # 模糊搜索匹配的孔位
        search_text_upper = search_text.upper()
        matched_holes = []
        
        for hole in self.hole_collection.holes.values():
            if search_text_upper in hole.hole_id.upper():
                matched_holes.append(hole)
                
        if matched_holes:
            # 高亮匹配的孔位
            if self.graphics_view:
                self.graphics_view.highlight_holes(matched_holes, search_highlight=True)
                
            self.log_message.emit(f"搜索 '{search_text}' 找到 {len(matched_holes)} 个孔位")
            
            # 处理搜索结果
            if len(matched_holes) == 1:
                # 只有一个结果，直接选中
                self._select_hole(matched_holes[0])
            else:
                # 查找精确匹配
                exact_match = self._find_exact_match(matched_holes, search_text_upper)
                if exact_match:
                    self._select_hole(exact_match)
                else:
                    # 列出所有匹配
                    hole_ids = [hole.hole_id for hole in matched_holes]
                    self.log_message.emit(f"匹配的孔位: {', '.join(hole_ids)}")
                    
            self.search_completed.emit(matched_holes)
        else:
            self.log_message.emit(f"搜索 '{search_text}' 没有找到匹配的孔位")
            self.search_completed.emit([])
            
    def _find_exact_match(self, holes: List[HoleData], search_text: str) -> Optional[HoleData]:
        """查找精确匹配的孔位"""
        for hole in holes:
            if hole.hole_id.upper() == search_text:
                return hole
        return None
        
    def _select_hole(self, hole: HoleData):
        """选中孔位"""
        self.selected_hole = hole
        self.log_message.emit(f"🎯 选中孔位: {hole.hole_id}")
        
        # 显示详细信息
        self.log_message.emit(f"  📍 位置: ({hole.center_x:.1f}, {hole.center_y:.1f})")
        self.log_message.emit(f"  📊 状态: {hole.status.value}")
        self.log_message.emit(f"  📏 半径: {hole.radius:.3f}mm")
        
        # 发送选中信号
        self.hole_selected.emit(hole)
        
    def get_selected_hole(self) -> Optional[HoleData]:
        """获取当前选中的孔位"""
        return self.selected_hole
        
    def clear_search(self):
        """清空搜索"""
        if self.search_input:
            self.search_input.clear()
        if self.graphics_view:
            self.graphics_view.clear_search_highlight()
        self.selected_hole = None
        self.log_message.emit("搜索已清空")