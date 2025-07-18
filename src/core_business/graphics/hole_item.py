"""
管孔图形项
定义单个管孔的图形表示
"""

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QLabel, QWidget
from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QFont

from src.core_business.models.hole_data import HoleData, HoleStatus


class PersistentTooltip(QLabel):
    """持久化的自定义工具提示标签"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用工具提示窗口标志，而不是独立窗口
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 鼠标事件穿透
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 200, 240);
                border: 1px solid #888;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
                color: #D3D8E0;
            }
        """)
        self.hide()
    
    def showTooltip(self, text: str, pos):
        """显示工具提示"""
        self.setText(text)
        self.adjustSize()
        
        # 调整位置避免超出屏幕
        screen_rect = self.screen().availableGeometry()
        tooltip_rect = self.geometry()
        tooltip_rect.moveTopLeft(pos)
        
        # 确保工具提示在屏幕内
        if tooltip_rect.right() > screen_rect.right():
            tooltip_rect.moveRight(screen_rect.right() - 5)
        if tooltip_rect.bottom() > screen_rect.bottom():
            tooltip_rect.moveBottom(screen_rect.bottom() - 5)
        
        self.setGeometry(tooltip_rect)
        self.show()
        self.raise_()
    
    def hideTooltip(self):
        """隐藏工具提示"""
        self.hide()


class HoleGraphicsItem(QGraphicsEllipseItem):
    """管孔图形项"""
    
    # 状态颜色映射
    STATUS_COLORS = {
        HoleStatus.PENDING: QColor(200, 200, 200),          # 灰色 - 待检
        HoleStatus.PROCESSING: QColor(100, 150, 255),       # 蓝色 - 检测中
        HoleStatus.QUALIFIED: QColor(50, 200, 50),          # 绿色 - 合格
        HoleStatus.DEFECTIVE: QColor(255, 50, 50),          # 红色 - 异常
        HoleStatus.BLIND: QColor(255, 200, 50),             # 黄色 - 盲孔
        HoleStatus.TIE_ROD: QColor(100, 255, 100),         # 亮绿色 - 拉杆孔
    }
    
    def __init__(self, hole_data: HoleData, parent=None):
        """
        初始化管孔图形项
        
        Args:
            hole_data: 孔数据
            parent: 父项
        """
        # 创建以原点为中心的椭圆矩形，然后通过setPos设置实际位置
        rect = QRectF(
            -hole_data.radius,
            -hole_data.radius,
            hole_data.radius * 2,
            hole_data.radius * 2
        )
        
        super().__init__(rect, parent)
        
        # 设置图形项的实际位置到孔的中心坐标
        self.setPos(hole_data.center_x, hole_data.center_y)
        
        self.hole_data = hole_data
        self._is_highlighted = False
        self._is_selected = False
        self._is_search_highlighted = False
        
        # 自定义工具提示（已禁用，使用标准Qt工具提示）
        # self._custom_tooltip = None
        # self._tooltip_shown = False
        
        # 设置图形项属性
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)  # 禁用几何变化通知
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, False)
        self.setFlag(QGraphicsItem.ItemClipsToShape, True)  # 启用形状裁剪
        self.setAcceptHoverEvents(True)  # 启用悬停事件
        
        # 设置初始样式
        self.update_appearance()
        
        # 启用标准工具提示
        self.setToolTip(self._create_tooltip())
    
    def update_appearance(self):
        """更新外观"""
        # 获取状态颜色
        color = self.STATUS_COLORS.get(self.hole_data.status, QColor(128, 128, 128))
        
        # 设置画笔和画刷
        if self._is_search_highlighted:
            # 搜索高亮状态：紫色边框（最高优先级）
            pen = QPen(QColor(255, 0, 255), 3.0)
            brush = QBrush(QColor(255, 0, 255, 100))
        elif self._is_highlighted:
            # 高亮状态：加粗边框，亮色填充
            pen = QPen(color.darker(150), 2.0)
            brush = QBrush(color.lighter(120))
        elif self._is_selected:
            # 选中状态：特殊边框
            pen = QPen(QColor(255, 255, 255), 2.0, Qt.DashLine)
            brush = QBrush(color)
        else:
            # 正常状态
            pen = QPen(color.darker(120), 1.0)
            brush = QBrush(color)
        
        self.setPen(pen)
        self.setBrush(brush)

        # 强制重绘
        self.update()
    
    def set_highlighted(self, highlighted: bool):
        """设置高亮状态"""
        if self._is_highlighted != highlighted:
            self._is_highlighted = highlighted
            self.update_appearance()
    
    def set_selected_state(self, selected: bool):
        """设置选中状态"""
        if self._is_selected != selected:
            self._is_selected = selected
            self.update_appearance()

    def set_search_highlighted(self, highlighted: bool):
        """设置搜索高亮状态"""
        if self._is_search_highlighted != highlighted:
            self._is_search_highlighted = highlighted
            self.update_appearance()
    
    def update_status(self, new_status: HoleStatus):
        """更新孔状态"""
        if self.hole_data.status != new_status:
            self.hole_data.status = new_status
            self.update_appearance()
    
    def _create_tooltip(self) -> str:
        """创建工具提示文本"""
        # AI员工4号修改开始
        # 统一坐标格式为CXXXRXXX
        # if self.hole_data.row and self.hole_data.column:
        #     grid_pos = f"C{self.hole_data.column:03d}R{self.hole_data.row:03d}"
        # AI员工4号修改结束
        # else:
        #     grid_pos = "未分配"
        
        return (
            f"孔位置: {self.hole_data.hole_id}\n"
            # f"网格位置: {grid_pos}\n"  # 与孔位置重复，已注释
            f"坐标: ({self.hole_data.center_x:.3f}, {self.hole_data.center_y:.3f})\n"
            f"半径: {self.hole_data.radius:.3f}\n"
            f"状态: {self.hole_data.status.value}\n"
            f"图层: {self.hole_data.layer}"
        )
    
    def get_hole_data(self) -> HoleData:
        """获取孔数据"""
        return self.hole_data
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在孔内"""
        return self.hole_data.is_near(x, y, self.hole_data.radius)
    
    def paint(self, painter: QPainter, option, widget=None):
        """自定义绘制（性能优化）"""
        # 快速视口检查
        exposed = option.exposedRect
        bounds = self.boundingRect()
        if not exposed.intersects(bounds):
            return

        # 根据缩放级别调整细节
        lod = option.levelOfDetailFromTransform(painter.worldTransform())

        if lod < 0.05:
            # 极小缩放：只绘制像素点
            center = bounds.center()
            painter.fillRect(int(center.x()), int(center.y()), 1, 1, self.brush().color())
        elif lod < 0.2:
            # 小缩放：绘制简单矩形
            painter.fillRect(bounds, self.brush().color())
        elif lod < 0.8:
            # 中等缩放：简化椭圆
            painter.setBrush(self.brush())
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(bounds)
        else:
            # 高缩放：完整绘制
            super().paint(painter, option, widget)
    
    def boundingRect(self) -> QRectF:
        """返回边界矩形"""
        # 添加一些边距以容纳边框
        rect = super().boundingRect()
        margin = 2.0
        return rect.adjusted(-margin, -margin, margin, margin)
    
    def _get_custom_tooltip(self):
        """获取或创建自定义工具提示"""
        if not self._custom_tooltip:
            # 找到顶级窗口作为父级
            view = self.scene().views()[0] if self.scene() and self.scene().views() else None
            parent = view.window() if view else None
            self._custom_tooltip = PersistentTooltip(parent)
        return self._custom_tooltip
    
    def hoverEnterEvent(self, event):
        """鼠标进入事件 - 使用标准工具提示"""
        # 禁用自定义工具提示，只使用标准Qt工具提示
        # try:
        #     tooltip = self._get_custom_tooltip()
        #     tooltip_text = self._create_tooltip()
        #     
        #     # 获取鼠标在屏幕上的位置
        #     if self.scene() and self.scene().views():
        #         view = self.scene().views()[0]
        #         # 将场景坐标转换为全局坐标
        #         scene_pos = event.scenePos()
        #         view_pos = view.mapFromScene(scene_pos)
        #         global_pos = view.mapToGlobal(view_pos)
        #         
        #         # 偏移一点避免遮挡光标
        #         global_pos.setX(global_pos.x() + 15)
        #         global_pos.setY(global_pos.y() + 15)
        #         
        #         tooltip.showTooltip(tooltip_text, global_pos)
        #         self._tooltip_shown = True
        # except Exception as e:
        #     print(f"显示工具提示失败: {e}")
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """鼠标离开事件 - 使用标准工具提示"""
        # 禁用自定义工具提示，只使用标准Qt工具提示
        # try:
        #     if self._custom_tooltip and self._tooltip_shown:
        #         self._custom_tooltip.hideTooltip()
        #         self._tooltip_shown = False
        # except Exception as e:
        #     print(f"隐藏工具提示失败: {e}")
        
        super().hoverLeaveEvent(event)


class HoleItemFactory:
    """管孔图形项工厂"""
    
    @staticmethod
    def create_hole_item(hole_data: HoleData) -> HoleGraphicsItem:
        """创建管孔图形项"""
        return HoleGraphicsItem(hole_data)
    
    @staticmethod
    def create_batch_items(hole_collection) -> list[HoleGraphicsItem]:
        """批量创建管孔图形项（优化版本）"""
        items = []
        items_append = items.append  # 缓存方法引用以提升性能

        # 预分配列表大小
        hole_count = len(hole_collection)
        items = [None] * hole_count

        # 批量创建 - 使用标准构造函数确保正确初始化
        for i, hole in enumerate(hole_collection):
            # 使用标准构造函数，确保所有方法正确绑定
            item = HoleGraphicsItem(hole)
            items[i] = item

        return items
    
    @staticmethod
    def update_items_status(items: list[HoleGraphicsItem], status_updates: dict):
        """批量更新图形项状态"""
        for item in items:
            hole_id = item.hole_data.hole_id
            if hole_id in status_updates:
                new_status = status_updates[hole_id]
                item.update_status(new_status)
