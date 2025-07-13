"""模拟进度管理器"""
import logging
import random
from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox

from aidcis2.models.hole_data import HoleStatus, HoleCollection, HoleData


class SimulationManager(QObject):
    """
    模拟检测进度管理器
    支持普通模拟和扇形顺序模拟
    """
    
    # 信号定义
    simulation_started = Signal()
    simulation_stopped = Signal()
    simulation_step_completed = Signal(str, str)  # hole_id, status
    sector_changed = Signal(str)  # sector_name
    log_message = Signal(str)
    status_updated = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 基础模拟状态
        self.simulation_running = False
        self.pending_holes: List[HoleData] = []
        self.simulation_hole_index = 0
        
        # V2扇形模拟状态
        self.simulation_running_v2 = False
        self.simulation_index_v2 = 0
        self.holes_list_v2: List[HoleData] = []
        self.sector_holes: Dict[Any, List[HoleData]] = {}
        self.sector_stats: Dict[Any, Dict[str, int]] = {}
        self.hole_to_sector_map: Dict[str, Any] = {}
        self.current_displayed_sector = None
        
        # 统计数据
        self.v2_stats = {
            "合格": 0,
            "异常": 0,
            "盲孔": 0,
            "拉杆孔": 0
        }
        
        # 定时器
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._update_simulation_progress)
        
        self.simulation_timer_v2 = QTimer()
        self.simulation_timer_v2.timeout.connect(self._update_simulation_v2)
        
        # 外部组件引用
        self.hole_collection: Optional[HoleCollection] = None
        self.graphics_view = None
        self.simulate_btn = None
        self.sector_manager = None
        
    def set_components(self, hole_collection, graphics_view, simulate_btn, sector_manager=None):
        """设置外部组件引用"""
        self.hole_collection = hole_collection
        self.graphics_view = graphics_view
        self.simulate_btn = simulate_btn
        self.sector_manager = sector_manager
        
    def start_simulation(self, version=1):
        """开始模拟，version=1为普通模拟，version=2为扇形模拟"""
        if not self.hole_collection:
            QMessageBox.warning(None, "警告", "请先加载DXF文件")
            return
            
        if version == 1:
            self._start_simulation_v1()
        else:
            self._start_simulation_v2()
            
    def stop_simulation(self):
        """停止所有模拟"""
        if self.simulation_running:
            self.simulation_timer.stop()
            self.simulation_running = False
            
        if self.simulation_running_v2:
            self.simulation_timer_v2.stop()
            self.simulation_running_v2 = False
            
        if self.simulate_btn:
            self.simulate_btn.setText("使用模拟进度")
            
        self.log_message.emit("⏹️ 停止模拟进度")
        self.simulation_stopped.emit()
        
    def _start_simulation_v1(self):
        """开始普通模拟"""
        if self.simulation_running:
            self.stop_simulation()
            return
            
        # 创建待处理孔位列表 - 按从上到下排序
        self.pending_holes = list(self.hole_collection.holes.values())
        self.pending_holes.sort(key=lambda hole: (hole.center_y, hole.center_x))
        self.simulation_hole_index = 0
        
        self.log_message.emit(f"🎯 准备模拟 {len(self.pending_holes)} 个孔位")
        
        # 检查图形视图
        if self.graphics_view:
            graphics_hole_count = len(self.graphics_view.hole_items) if hasattr(self.graphics_view, 'hole_items') else 0
            self.log_message.emit(f"🖼️ 图形视图中的孔位数量: {graphics_hole_count}")
            
        # 启动定时器
        self.simulation_timer.start(1000)  # 每秒处理一个
        self.simulation_running = True
        
        if self.simulate_btn:
            self.simulate_btn.setText("停止模拟")
            
        self.log_message.emit("🚀 开始模拟进度")
        self.simulation_started.emit()
        
    def _start_simulation_v2(self):
        """开始扇形顺序模拟"""
        if self.simulation_running_v2:
            self.stop_simulation()
            return
            
        # 初始化V2模拟
        self.simulation_running_v2 = True
        self.simulation_index_v2 = 0
        
        # 初始化扇形数据
        self._initialize_sector_simulation()
        
        # 重置统计
        self.v2_stats = {
            "合格": 0,
            "异常": 0,
            "盲孔": 0,
            "拉杆孔": 0
        }
        
        total_holes = len(self.holes_list_v2)
        self.log_message.emit(f"🚀 开始模拟进度 V2 - 扇形顺序模式")
        self.log_message.emit(f"🎯 将处理 {total_holes} 个孔位")
        
        # 启动连续模拟
        self._start_continuous_simulation()
        
        if self.simulate_btn:
            self.simulate_btn.setText("停止模拟")
            
        self.simulation_started.emit()
        
    def _update_simulation_progress(self):
        """更新普通模拟进度"""
        if not self.pending_holes or self.simulation_hole_index >= len(self.pending_holes):
            self.simulation_timer.stop()
            self.simulation_running = False
            if self.simulate_btn:
                self.simulate_btn.setText("使用模拟进度")
            self.log_message.emit("✅ 模拟进度完成")
            self.simulation_stopped.emit()
            return
            
        # 获取当前孔位
        current_hole = self.pending_holes[self.simulation_hole_index]
        
        # 先设置检测中状态
        current_hole.status = HoleStatus.PROCESSING
        if self.graphics_view and hasattr(self.graphics_view, 'hole_items'):
            if current_hole.hole_id in self.graphics_view.hole_items:
                hole_item = self.graphics_view.hole_items[current_hole.hole_id]
                hole_item.update_status(current_hole.status)
                
        self.status_updated.emit()
        
        # 延迟设置最终状态
        def update_final_status():
            # 随机分配最终状态
            rand_value = random.random()
            if rand_value < 0.995:
                final_status = HoleStatus.QUALIFIED
            elif rand_value < 0.9999:
                final_status = HoleStatus.DEFECTIVE
            else:
                other_statuses = [HoleStatus.BLIND, HoleStatus.TIE_ROD]
                final_status = random.choice(other_statuses)
                
            current_hole.status = final_status
            
            if self.graphics_view and hasattr(self.graphics_view, 'hole_items'):
                if current_hole.hole_id in self.graphics_view.hole_items:
                    hole_item = self.graphics_view.hole_items[current_hole.hole_id]
                    hole_item.update_status(final_status)
                    
            self.simulation_step_completed.emit(current_hole.hole_id, final_status.value)
            self.status_updated.emit()
            
            # 移动到下一个
            self.simulation_hole_index += 1
            
        QTimer.singleShot(500, update_final_status)
        
    def _initialize_sector_simulation(self):
        """初始化扇形模拟数据"""
        if not self.sector_manager:
            self.log_message.emit("⚠️ 扇形管理器不存在")
            return
            
        from aidcis2.graphics.sector_manager import SectorQuadrant
        
        # 扇形顺序
        self.sector_order = [
            SectorQuadrant.SECTOR_1,
            SectorQuadrant.SECTOR_2,
            SectorQuadrant.SECTOR_3,
            SectorQuadrant.SECTOR_4
        ]
        
        # 获取所有孔位并按从上到下整体排序（忽略扇形边界）
        all_holes = list(self.hole_collection.holes.values())
        self.holes_list_v2 = self._create_spiral_detection_path(all_holes)
        
        # 重新映射到扇形（用于显示和统计）
        self.sector_holes = {}
        self.sector_stats = {}
        self.hole_to_sector_map = {}
        
        for sector in self.sector_order:
            self.sector_holes[sector] = []
            self.sector_stats[sector] = {"completed": 0, "total": 0}
        
        # 为每个孔位分配扇形（保持原有的分配逻辑用于显示）
        for hole in self.holes_list_v2:
            # 使用扇形管理器确定孔位所属扇形
            sector = None
            for s in self.sector_order:
                sector_holes = self.sector_manager.get_sector_holes(s)
                if any(sh.hole_id == hole.hole_id for sh in sector_holes):
                    sector = s
                    break
            
            # 如果找不到对应扇形，分配到第一个扇形
            if sector is None:
                sector = self.sector_order[0]
            
            self.hole_to_sector_map[hole.hole_id] = sector
            self.sector_holes[sector].append(hole)
            self.sector_stats[sector]["total"] += 1
        
        # 输出扇形统计
        for sector in self.sector_order:
            count = len(self.sector_holes[sector])
            self.log_message.emit(f"📋 {sector.value}: {count} 个孔位")
        
        self.log_message.emit(f"🔄 整体排序：从上到下处理 {len(self.holes_list_v2)} 个孔位")
        
        # 验证检测列表完整性
        self._validate_detection_list_completeness()
            
        self.simulation_index_v2 = 0
        self.current_displayed_sector = None
        
    def _validate_detection_list_completeness(self):
        """验证检测列表完整性 - 确保所有孔位都被包含"""
        if not self.hole_collection:
            return
            
        # 获取所有孔位
        all_hole_ids = set(self.hole_collection.holes.keys())
        list_hole_ids = set(h.hole_id for h in self.holes_list_v2)
        missing_holes = all_hole_ids - list_hole_ids
        
        if missing_holes:
            self.log_message.emit(f"⚠️ 发现 {len(missing_holes)} 个缺失的孔位")
            self.log_message.emit(f"缺失孔位示例: {list(missing_holes)[:5]}")
            
            # 自动添加缺失的孔位到检测列表
            added_count = 0
            for hole_id in missing_holes:
                if hole_id in self.hole_collection.holes:
                    missing_hole = self.hole_collection.holes[hole_id]
                    self.holes_list_v2.append(missing_hole)
                    
                    # 分配到最后一个扇形
                    if self.sector_order:
                        last_sector = self.sector_order[-1]
                        self.hole_to_sector_map[hole_id] = last_sector
                        if last_sector not in self.sector_holes:
                            self.sector_holes[last_sector] = []
                        self.sector_holes[last_sector].append(missing_hole)
                        
                        # 更新统计
                        if last_sector in self.sector_stats:
                            self.sector_stats[last_sector]["total"] += 1
                        
                    added_count += 1
            
            if added_count > 0:
                self.log_message.emit(f"✅ 已自动添加 {added_count} 个缺失孔位到检测列表")
                self.log_message.emit(f"检测列表现包含 {len(self.holes_list_v2)} 个孔位")
        else:
            self.log_message.emit(f"✅ 检测列表完整：{len(self.holes_list_v2)} 个孔位")

    def _create_spiral_detection_path(self, holes):
        """创建优化的检测路径 - 从上到下排序"""
        if not holes:
            return holes
            
        # 修正：严格按Y坐标从上到下排序（Y值小的在上方）
        # 次要排序使用X坐标从左到右
        return sorted(holes, key=lambda h: (h.center_y, h.center_x))
        
    def _start_continuous_simulation(self):
        """开始连续模拟"""
        if not self.holes_list_v2:
            self.log_message.emit("⚠️ 没有孔位可供模拟")
            return
            
        # 启动快速定时器
        self.simulation_timer_v2.start(100)  # 100ms每个孔位
        
    def _update_simulation_v2(self):
        """更新V2模拟"""
        if self.simulation_index_v2 >= len(self.holes_list_v2):
            self._complete_all_sectors_simulation()
            return
            
        # 获取当前孔位
        current_hole = self.holes_list_v2[self.simulation_index_v2]
        current_sector = self.hole_to_sector_map.get(current_hole.hole_id)
        
        # 检查是否切换到新扇形
        if current_sector != self.current_displayed_sector:
            self.current_displayed_sector = current_sector
            self.sector_changed.emit(current_sector.value if current_sector else "")
            
        # 设置检测中状态
        current_hole.status = HoleStatus.PROCESSING
        self._update_hole_visual(current_hole)
        
        # 延迟设置最终状态
        def set_final_color():
            # 随机分配状态
            rand_value = random.random()
            if rand_value < 0.995:
                final_status = HoleStatus.QUALIFIED
                self.v2_stats["合格"] += 1
            elif rand_value < 0.9999:
                final_status = HoleStatus.DEFECTIVE
                self.v2_stats["异常"] += 1
            else:
                other_statuses = [HoleStatus.BLIND, HoleStatus.TIE_ROD]
                final_status = random.choice(other_statuses)
                if final_status == HoleStatus.BLIND:
                    self.v2_stats["盲孔"] += 1
                else:
                    self.v2_stats["拉杆孔"] += 1
                    
            current_hole.status = final_status
            self._update_hole_visual(current_hole)
            
            # 更新扇形统计
            if current_sector and current_sector in self.sector_stats:
                self.sector_stats[current_sector]["completed"] += 1
                
            self.simulation_step_completed.emit(current_hole.hole_id, final_status.value)
            self.status_updated.emit()
            
            # 移动到下一个
            self.simulation_index_v2 += 1
            
        QTimer.singleShot(50, set_final_color)
        
    def _update_hole_visual(self, hole: HoleData):
        """更新孔位视觉效果"""
        if not self.graphics_view or not hasattr(self.graphics_view, 'hole_items'):
            return
            
        if hole.hole_id in self.graphics_view.hole_items:
            hole_item = self.graphics_view.hole_items[hole.hole_id]
            hole_item.update_status(hole.status)
            hole_item.update()
            
    def _complete_all_sectors_simulation(self):
        """完成所有扇形模拟"""
        self.simulation_timer_v2.stop()
        self.simulation_running_v2 = False
        
        if self.simulate_btn:
            self.simulate_btn.setText("使用模拟进度")
            
        # 输出统计
        total = sum(self.v2_stats.values())
        self.log_message.emit(f"✅ V2模拟完成！处理了 {total} 个孔位")
        self.log_message.emit(f"📊 最终统计:")
        for status, count in self.v2_stats.items():
            percentage = (count / total * 100) if total > 0 else 0
            self.log_message.emit(f"  {status}: {count} ({percentage:.2f}%)")
            
        self.simulation_stopped.emit()