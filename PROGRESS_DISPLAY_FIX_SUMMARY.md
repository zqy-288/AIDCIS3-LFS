# 进度显示修复总结

## 问题描述
用户要求显示检测进度时使用孔位数量，而不是检测单元数量。

## 修复内容

### 1. 修改了SimulationController
文件：`src/pages/main_detection_p1/components/simulation_controller.py`

- 添加了 `total_holes_processed` 变量跟踪已处理的孔位总数
- 修改了进度信号发送逻辑：
  ```python
  # 原来：发送检测单元数
  self.simulation_progress.emit(self.current_index + 1, len(self.detection_units))
  
  # 现在：发送孔位数
  self.total_holes_processed += len(current_unit.holes)
  self.simulation_progress.emit(self.total_holes_processed, total_holes)
  ```

### 2. 修改了日志输出
文件：`src/pages/main_detection_p1/native_main_detection_view_p1.py`

- 更新了进度日志显示：
  ```python
  self.logger.info(f"模拟进度: {current}/{total} 个孔位 ({progress}%)")
  ```

## 效果

- 进度条现在显示的是孔位数量（0-25270）而不是检测单元数量（0-13000）
- "已完成" 显示已检测的孔位数
- "待完成" 显示剩余的孔位数
- 百分比基于孔位数计算

## 示例
- 第一个检测单元包含2个孔位：进度显示 2/25270
- 第二个检测单元包含2个孔位：进度显示 4/25270
- 单个孔位的检测单元：进度增加1
- 配对孔位的检测单元：进度增加2