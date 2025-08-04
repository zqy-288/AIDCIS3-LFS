# 扇形统计表格显示修复总结

## 问题描述
扇形统计表格显示异常：
1. 待检数量（25268）大于扇形总数（6356）
2. 显示的是整体统计而不是扇形统计
3. 表格样式不够美观

## 问题原因
`update_progress_display` 方法错误地调用了 `update_sector_stats`，导致整体统计数据被写入扇形统计表格。

## 修复内容

### 1. 移除错误的更新调用
在 `native_main_detection_view_p1.py` 第421行：
```python
# 删除了这行：
# self.update_sector_stats(data)
```

### 2. 加载文件后正确更新扇形统计
在 `load_hole_collection` 方法中添加：
```python
# 如果有当前扇形，更新扇形统计
if self.coordinator and self.coordinator.current_sector:
    sector_holes = self.coordinator.get_current_sector_holes()
    if sector_holes:
        sector_stats = self.coordinator._calculate_sector_stats(sector_holes)
        if hasattr(self.left_panel, 'update_sector_stats'):
            self.left_panel.update_sector_stats(sector_stats)
```

### 3. 表格样式优化（已完成）
- 列宽增加：状态列60px，数量列65px
- 字体增大到11px
- 单元格内边距增加到4px
- 添加表头样式

## 数据逻辑
- **状态统计**：显示整个管板的孔位统计（总数25270）
- **扇形统计**：只显示当前选中扇形的孔位统计
  - sector_1: 6356个孔位
  - sector_2: 6279个孔位
  - sector_3: 6279个孔位
  - sector_4: 6356个孔位

## 预期效果
1. 扇形统计表格只显示当前扇形的数据
2. 待检数量 ≤ 扇形总计
3. 切换扇形时表格自动更新
4. 模拟过程中实时更新当前扇形的状态

## 测试验证
运行 `test_sector_stats_display.py` 验证：
1. 加载DXF文件后表格显示正确
2. 点击不同扇形时数据更新
3. 数据逻辑合理（无异常大的数字）