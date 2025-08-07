"""
双探头路径规划系统
适配C/R反转的编号系统：
- C方向 = 垂直方向（列）
- R方向 = 水平方向（行）
- 双探头在水平方向(R方向)固定间距4个孔位
"""

import time
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import random


class HoleStatus(Enum):
    """孔位检测状态"""
    UNDETECTED = "未检测"  # 灰色
    DETECTING = "检测中"   # 蓝色
    QUALIFIED = "合格"     # 绿色
    DEFECTIVE = "缺陷"     # 红色


@dataclass
class Hole:
    """孔位数据结构"""
    hole_id: str         # 如 C001R001
    c_index: int         # C编号（垂直位置）
    r_index: int         # R编号（水平位置）
    x_coord: float       # 物理X坐标
    y_coord: float       # 物理Y坐标
    status: HoleStatus = HoleStatus.UNDETECTED
    detection_start_time: Optional[float] = None
    

@dataclass
class DetectionStep:
    """检测步骤"""
    column: int          # 当前列号(C)
    probe1_hole: str     # 探头1检测的孔
    probe2_hole: Optional[str]  # 探头2检测的孔（单探头模式为None）
    is_dual_mode: bool   # 是否双探头模式
    direction: str       # 'down' 或 'up'


class DualProbePathPlanner:
    """双探头路径规划器"""
    
    def __init__(self, probe_distance: int = 4, detection_time_ms: int = 9500):
        """
        初始化
        
        Args:
            probe_distance: 两探头在R方向的固定间距
            detection_time_ms: 检测时间（毫秒）
        """
        self.probe_distance = probe_distance
        self.detection_time_ms = detection_time_ms
        self.qualified_probability = 0.99  # 99%合格率
        
        # 存储所有孔位
        self.holes: Dict[str, Hole] = {}
        
    def load_hole_layout(self, max_c: int, max_r_per_c: Dict[int, int]):
        """
        加载孔位布局
        
        Args:
            max_c: 最大列数(C方向)
            max_r_per_c: 每列的最大行数(R方向) {c_index: max_r}
        """
        self.holes.clear()
        
        for c in range(1, max_c + 1):
            max_r = max_r_per_c.get(c, 0)
            for r in range(1, max_r + 1):
                hole_id = f"C{c:03d}R{r:03d}"
                hole = Hole(
                    hole_id=hole_id,
                    c_index=c,
                    r_index=r,
                    x_coord=r * 10.0,  # 简化的坐标计算
                    y_coord=c * 10.0
                )
                self.holes[hole_id] = hole
                
        print(f"✅ 加载了 {len(self.holes)} 个孔位")
        
    def generate_dual_probe_path(self) -> List[DetectionStep]:
        """
        生成双探头检测路径
        
        Returns:
            检测步骤列表
        """
        path = []
        
        # 获取所有列号并排序
        columns = sorted(set(hole.c_index for hole in self.holes.values()))
        
        for col_idx, c in enumerate(columns):
            # 获取该列的所有孔位
            column_holes = sorted(
                [h for h in self.holes.values() if h.c_index == c],
                key=lambda h: h.r_index
            )
            
            if not column_holes:
                continue
                
            # 奇数列从上往下（R小到大），偶数列从下往上（R大到小）
            is_odd_column = (col_idx % 2 == 0)  # 0-indexed
            direction = 'down' if is_odd_column else 'up'
            
            # 生成双探头扫描步骤
            dual_steps = self._generate_dual_probe_steps(column_holes, direction)
            path.extend(dual_steps)
            
            # 生成单探头补充步骤
            single_steps = self._generate_single_probe_steps(column_holes, dual_steps)
            path.extend(single_steps)
            
        return path
    
    def _generate_dual_probe_steps(self, column_holes: List[Hole], 
                                  direction: str) -> List[DetectionStep]:
        """生成双探头扫描步骤"""
        steps = []
        
        if direction == 'down':
            # 从R小到大扫描
            for i in range(len(column_holes) - self.probe_distance):
                probe1 = column_holes[i]
                probe2 = column_holes[i + self.probe_distance]
                
                step = DetectionStep(
                    column=probe1.c_index,
                    probe1_hole=probe1.hole_id,
                    probe2_hole=probe2.hole_id,
                    is_dual_mode=True,
                    direction=direction
                )
                steps.append(step)
        else:
            # 从R大到小扫描
            for i in range(len(column_holes) - 1, self.probe_distance - 1, -1):
                probe1 = column_holes[i - self.probe_distance]
                probe2 = column_holes[i]
                
                step = DetectionStep(
                    column=probe1.c_index,
                    probe1_hole=probe1.hole_id,
                    probe2_hole=probe2.hole_id,
                    is_dual_mode=True,
                    direction=direction
                )
                steps.append(step)
                
        return steps
    
    def _generate_single_probe_steps(self, column_holes: List[Hole], 
                                   dual_steps: List[DetectionStep]) -> List[DetectionStep]:
        """生成单探头补充步骤"""
        # 收集已检测的孔
        detected_holes = set()
        for step in dual_steps:
            detected_holes.add(step.probe1_hole)
            if step.probe2_hole:
                detected_holes.add(step.probe2_hole)
        
        # 找出未检测的孔
        undetected = []
        for hole in column_holes:
            if hole.hole_id not in detected_holes:
                undetected.append(hole)
        
        # 生成单探头步骤
        steps = []
        for hole in undetected:
            step = DetectionStep(
                column=hole.c_index,
                probe1_hole=hole.hole_id,
                probe2_hole=None,
                is_dual_mode=False,
                direction='single'
            )
            steps.append(step)
            
        return steps
    
    def simulate_detection(self, step: DetectionStep):
        """
        模拟检测过程
        
        Args:
            step: 检测步骤
        """
        # 开始检测 - 设置为蓝色
        holes_to_detect = [step.probe1_hole]
        if step.probe2_hole:
            holes_to_detect.append(step.probe2_hole)
            
        for hole_id in holes_to_detect:
            if hole_id in self.holes:
                self.holes[hole_id].status = HoleStatus.DETECTING
                self.holes[hole_id].detection_start_time = time.time()
                
        # 模拟9500ms检测时间
        time.sleep(self.detection_time_ms / 1000.0)
        
        # 检测完成 - 99%绿色，1%红色
        for hole_id in holes_to_detect:
            if hole_id in self.holes:
                if random.random() < self.qualified_probability:
                    self.holes[hole_id].status = HoleStatus.QUALIFIED
                else:
                    self.holes[hole_id].status = HoleStatus.DEFECTIVE
                    
    def get_path_statistics(self, path: List[DetectionStep]) -> Dict:
        """获取路径统计信息"""
        total_steps = len(path)
        dual_steps = sum(1 for step in path if step.is_dual_mode)
        single_steps = total_steps - dual_steps
        
        # 计算总检测时间
        total_time_ms = total_steps * self.detection_time_ms
        
        # 计算效率提升
        if_all_single = len(self.holes) * self.detection_time_ms
        time_saved_ms = if_all_single - total_time_ms
        efficiency_gain = (time_saved_ms / if_all_single) * 100 if if_all_single > 0 else 0
        
        return {
            "total_holes": len(self.holes),
            "total_steps": total_steps,
            "dual_probe_steps": dual_steps,
            "single_probe_steps": single_steps,
            "total_time_seconds": total_time_ms / 1000,
            "efficiency_gain_percent": efficiency_gain,
            "holes_per_dual_step": 2,
            "effective_throughput": len(self.holes) / (total_time_ms / 1000) if total_time_ms > 0 else 0
        }
    
    def visualize_current_status(self) -> str:
        """生成当前状态的可视化字符串"""
        # 获取所有C和R的范围
        all_c = sorted(set(h.c_index for h in self.holes.values()))
        all_r = sorted(set(h.r_index for h in self.holes.values()))
        
        if not all_c or not all_r:
            return "无孔位数据"
        
        # 构建可视化矩阵
        status_symbols = {
            HoleStatus.UNDETECTED: '○',
            HoleStatus.DETECTING: '●',  # 蓝色
            HoleStatus.QUALIFIED: '✓',   # 绿色
            HoleStatus.DEFECTIVE: '✗'    # 红色
        }
        
        visualization = []
        
        # 标题行
        header = "   R" + "".join(f"{r:03d} " for r in all_r[:10])  # 只显示前10个R
        visualization.append(header)
        
        # 数据行
        for c in all_c[:10]:  # 只显示前10个C
            row = f"C{c:03d} "
            for r in all_r[:10]:
                hole_id = f"C{c:03d}R{r:03d}"
                if hole_id in self.holes:
                    status = self.holes[hole_id].status
                    row += f" {status_symbols[status]}  "
                else:
                    row += "    "
            visualization.append(row)
            
        return "\n".join(visualization)


# 使用示例
if __name__ == "__main__":
    print("🚀 双探头路径规划系统测试")
    print("=" * 60)
    
    # 创建规划器
    planner = DualProbePathPlanner(probe_distance=4, detection_time_ms=9500)
    
    # 定义布局 - 模拟您图片中的布局
    max_r_per_c = {
        1: 9,   # C001有9个孔(R001-R009)
        2: 9,   # C002有9个孔
        3: 9,   # C003有9个孔
        4: 8,   # C004有8个孔
        5: 7,   # C005有7个孔
    }
    
    planner.load_hole_layout(max_c=5, max_r_per_c=max_r_per_c)
    
    # 生成路径
    path = planner.generate_dual_probe_path()
    
    # 显示统计
    stats = planner.get_path_statistics(path)
    print("\n📊 路径统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 显示前几个步骤
    print("\n🔍 前10个检测步骤:")
    for i, step in enumerate(path[:10]):
        mode = "双探头" if step.is_dual_mode else "单探头"
        holes = f"{step.probe1_hole}"
        if step.probe2_hole:
            holes += f" + {step.probe2_hole}"
        print(f"  步骤{i+1}: {mode} - {holes} (方向: {step.direction})")
    
    # 模拟检测过程
    print("\n🔄 模拟检测过程...")
    print("\n初始状态:")
    print(planner.visualize_current_status())
    
    # 执行前3个步骤
    for i, step in enumerate(path[:3]):
        print(f"\n执行步骤 {i+1}...")
        planner.simulate_detection(step)
        print(planner.visualize_current_status())
        
    print("\n✅ 测试完成！")