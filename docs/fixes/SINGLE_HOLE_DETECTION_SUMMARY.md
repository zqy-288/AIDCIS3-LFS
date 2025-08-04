# 检测进度显示优化总结

## 改动说明

保持间隔4列的双孔检测逻辑，仅修改进度显示方式，使其显示孔位数而不是检测单元数。

## 主要修改

### 1. SimulationController 修改
文件：`src/pages/main_detection_p1/components/simulation_controller.py`

#### 新增变量：
- `total_holes_processed`: 跟踪已处理的孔位总数

#### 修改的逻辑：
- 保持使用HolePair检测单元（间隔4列配对）
- 进度信号改为发送孔位数：
  ```python
  # 计算已处理的孔位数
  self.total_holes_processed += len(current_unit.holes)
  
  # 发射进度信号（发送孔位数而不是检测单元数）
  total_holes = len(self.snake_sorted_holes)
  self.simulation_progress.emit(self.total_holes_processed, total_holes)
  ```

### 2. 检测逻辑保持不变
- 依然使用间隔4列的配对检测
- 每10秒检测1个单元（1-2个孔位）
- 按象限顺序：1->2->3->4

### 3. 进度显示优化
- 显示：已检测孔位数/总孔位数
- 例如：2/25270, 4/25270, 5/25270...
- 百分比基于孔位数计算

## 效果

- 检测逻辑不变：间隔4列配对检测
- 显示更直观：基于孔位数而非检测单元数
- 约13000个检测单元，覆盖25270个孔位