# 孔位覆盖问题修复总结

## 问题描述
用户截图显示有少量孔位（显示为灰色）没有被检测到，而大部分孔位显示为绿色（合格）或红色（异常）。

## 根本原因
模拟控制器在开始模拟时，只重置了 `self.snake_sorted_holes` 中的孔位状态，而这个列表只包含从检测单元中提取的孔位。如果有任何孔位因为某种原因没有被包含在检测单元中，它们的状态就不会被重置为 PENDING，导致它们在视图中保持原始状态。

## 修复方案

### 文件：`src/pages/main_detection_p1/components/simulation_controller.py`

修改前：
```python
# 只重置检测路径中的孔位
for i, hole in enumerate(self.snake_sorted_holes):
    if self.hole_collection and hole.hole_id in self.hole_collection.holes:
        self.hole_collection.holes[hole.hole_id].status = HoleStatus.PENDING
```

修改后：
```python
# 重置集合中的所有孔位
if self.hole_collection:
    for hole_id, hole in self.hole_collection.holes.items():
        hole.status = HoleStatus.PENDING
```

## 效果
1. 确保所有孔位在模拟开始时都被重置为待检状态（灰色）
2. 只有真正被检测到的孔位才会变成绿色（合格）或红色（异常）
3. 如果有任何孔位因为算法问题被遗漏，它们会保持灰色，便于识别

## 额外说明
虽然我们的蛇形路径算法理论上应该覆盖100%的孔位，但这个修复确保了：
- 即使算法有任何遗漏，用户也能通过灰色孔位清楚地看到
- 所有孔位的初始状态是一致的
- 避免了因为状态不一致导致的视觉混乱