#!/usr/bin/env python3
"""
修复时序同步问题的方案
"""

def get_timing_fix_code():
    """
    返回修复时序同步的代码
    
    核心思路：
    1. 使用单一定时器控制整个流程
    2. 在每个10秒周期内，通过状态机管理不同阶段
    3. 确保严格的时序：0秒开始 -> 9.5秒变色 -> 10秒下一个
    """
    
    return '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # ... 其他初始化代码 ...
        
        # 使用单一主定时器，更短的间隔来精确控制
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self._tick)
        self.main_timer.setInterval(100)  # 100ms检查一次
        
        # 时序控制
        self.cycle_start_time = 0  # 当前周期开始时间
        self.elapsed_time = 0      # 已经过时间
        self.phase = "IDLE"        # IDLE, DETECTING, FINALIZING
        
    def _tick(self):
        """主定时器tick，精确控制时序"""
        if not self.is_running:
            return
            
        # 计算经过时间
        self.elapsed_time += 0.1  # 100ms
        
        if self.phase == "IDLE":
            # 开始新的检测周期
            self._start_new_cycle()
            
        elif self.phase == "DETECTING":
            # 检测中，等待9.5秒
            if self.elapsed_time >= 9.5:
                self._finalize_detection()
                
        elif self.phase == "FINALIZING":
            # 等待到10秒开始下一个
            if self.elapsed_time >= 10.0:
                self.elapsed_time = 0
                self.phase = "IDLE"
                
    def _start_new_cycle(self):
        """开始新的检测周期"""
        if self.current_index >= len(self.detection_units):
            self._complete_simulation()
            return
            
        # 开始检测
        current_unit = self.detection_units[self.current_index]
        self._start_pair_detection(current_unit)
        
        self.phase = "DETECTING"
        self.cycle_start_time = time.time()
        self.current_index += 1
        
    def _finalize_detection(self):
        """完成当前检测（9.5秒时）"""
        if self.current_detecting_pair:
            # 更新状态
            for hole in self.current_detecting_pair.holes:
                final_status = self._simulate_detection_result()
                self._update_hole_status(hole.hole_id, final_status, color_override=None)
                
            self.current_detecting_pair = None
            
        self.phase = "FINALIZING"
    '''

def create_better_solution():
    """
    创建更好的解决方案
    """
    
    solution = """
# 更简单的方案：使用状态机确保时序

class SimulationStateMachine:
    '''模拟状态机，确保严格的时序'''
    
    def __init__(self):
        self.state = "WAITING"  # WAITING -> DETECTING -> FINALIZING -> WAITING
        self.cycle_count = 0
        self.start_time = None
        
    def should_start_detection(self, elapsed_ms):
        '''是否应该开始检测'''
        # 每10秒的0ms时刻
        return (elapsed_ms % 10000) < 100 and self.state == "WAITING"
        
    def should_finalize(self, elapsed_ms):
        '''是否应该完成检测'''
        # 每10秒的9500ms时刻
        cycle_ms = elapsed_ms % 10000
        return cycle_ms >= 9500 and cycle_ms < 9600 and self.state == "DETECTING"
        
    def transition(self, new_state):
        '''状态转换'''
        self.state = new_state
        if new_state == "DETECTING":
            self.cycle_count += 1

# 在SimulationController中使用：
def _process_with_state_machine(self):
    '''使用状态机处理，确保时序'''
    if not self.state_machine:
        self.state_machine = SimulationStateMachine()
        self.start_time = QElapsedTimer()
        self.start_time.start()
        
    elapsed = self.start_time.elapsed()
    
    if self.state_machine.should_start_detection(elapsed):
        # 开始新检测
        if self.current_index < len(self.detection_units):
            self._start_pair_detection(self.detection_units[self.current_index])
            self.current_index += 1
            self.state_machine.transition("DETECTING")
            
    elif self.state_machine.should_finalize(elapsed):
        # 完成检测
        self._finalize_current_pair_status()
        self.state_machine.transition("FINALIZING")
        
    # 自动回到WAITING状态
    if self.state_machine.state == "FINALIZING":
        cycle_ms = elapsed % 10000
        if cycle_ms < 100:  # 新周期开始
            self.state_machine.transition("WAITING")
"""
    
    return solution

# 打印解决方案
print("=== 时序同步问题分析 ===\n")
print("问题根源：")
print("1. 两个独立定时器难以精确同步")
print("2. 启动时的时序混乱")
print("3. 事件循环可能导致的延迟")
print("\n解决方案：")
print(create_better_solution())