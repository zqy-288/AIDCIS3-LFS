# 检测顺序修复总结

## 更新：2025-07-31 23:26

用户澄清了需求：
- 扇形顺序：右上(sector_1) → 左上(sector_2) → 左下(sector_3) → 右下(sector_4)
- 每个扇形内都从R164行开始（不是只从BC098R164开始）

## 修复的问题

### 1. 扇形切换时多次自适应问题
- **问题**：切换扇形时会触发多次自动适配，导致界面闪烁
- **原因**：resizeEvent 和其他地方都会触发自动适配
- **修复**：
  - 在 `resizeEvent` 中检查当前视图模式，微观模式下跳过自动适配
  - 在 `_show_sector_in_view` 中临时禁用自动适配并停止待处理的适配定时器

### 2. 检测起始位置错误
- **问题**：检测没有从正确的位置开始
- **原因**：
  1. 扇形分组逻辑使用了错误的坐标系（Qt坐标系而非数学坐标系）
  2. Y坐标排序逻辑不正确
  3. 对于x接近0的孔位（如BC098R164 x=-0.000）分组错误
- **修复**：
  1. 修正 `_group_holes_by_sector_v2` 方法使用数学坐标系
  2. 添加特殊处理：当x接近0时，根据hole_id前缀判断所属扇形
  3. 根据扇形位置使用正确的Y坐标排序：
     - 上半部分（sector_1和2）：从最大Y开始（R164在顶部）
     - 下半部分（sector_3和4）：从最小Y开始（R164在底部）

## 修改的文件

### 1. `/src/core_business/graphics/graphics_view.py`
```python
def resizeEvent(self, event: QResizeEvent):
    """窗口大小改变事件"""
    super().resizeEvent(event)
    
    # 检查是否在微观视图模式
    if hasattr(self, 'current_view_mode') and self.current_view_mode == 'micro':
        return  # 微观视图下跳过自动适配
    
    # 延迟执行自适应，避免频繁调用
    if not self._fit_pending:
        self._fit_pending = True
        self._fit_timer.start(100)  # 100ms后执行
```

### 2. `/src/pages/main_detection_p1/native_main_detection_view_p1.py`
```python
# 完全禁用自动适配，避免任何重复缩放
old_disable_auto_fit = getattr(graphics_view, 'disable_auto_fit', False)
graphics_view.disable_auto_fit = True

# 停止任何待处理的自动适配
if hasattr(graphics_view, '_fit_timer') and graphics_view._fit_timer:
    graphics_view._fit_timer.stop()
    graphics_view._fit_pending = False
```

### 3. `/src/pages/shared/components/snake_path/snake_path_renderer.py`

#### 修改1：扇形分组逻辑
```python
def _group_holes_by_sector_v2(self, holes: List[HoleData]) -> Dict[str, List[HoleData]]:
    """按象限分组孔位（使用HoleData对象）"""
    # ... 省略部分代码 ...
    
    # 按象限分组 - 使用数学坐标系（Y轴向上）
    for hole in holes:
        dx = hole.center_x - center_x
        dy = hole.center_y - center_y
        
        # 数学坐标系：Y轴向上
        if dx >= 0 and dy >= 0:
            sector_groups['sector_1'].append(hole)  # 右上（第一象限）
        elif dx < 0 and dy >= 0:
            sector_groups['sector_2'].append(hole)  # 左上（第二象限）
        elif dx < 0 and dy < 0:
            sector_groups['sector_3'].append(hole)  # 左下（第三象限）
        else:  # dx >= 0 and dy < 0
            sector_groups['sector_4'].append(hole)  # 右下（第四象限）
```

#### 修改2：扇形处理顺序
```python
# 按照指定顺序处理扇形：右上(1) → 左上(2) → 左下(3) → 右下(4)
sector_order = ['sector_1', 'sector_2', 'sector_3', 'sector_4']
```

#### 修改3：Y坐标排序逻辑
```python
# 按Y坐标排序所有行
# 根据用户要求：所有扇形都从R164开始
# 对于上半部分（sector_1和sector_2），R164在最上方（Y值最大）
# 对于下半部分（sector_3和sector_4），R164在最下方（Y值最小）
if sector_name in ['sector_1', 'sector_2']:
    # 上半部分：从最大Y开始（R164在顶部）
    sorted_rows = sorted(holes_by_y.keys(), reverse=True)
else:
    # 下半部分：从最小Y开始（R164在底部）
    sorted_rows = sorted(holes_by_y.keys())
```

#### 修改4：处理x接近0的特殊情况
```python
# 对于接近中心的点，使用绝对坐标而不是相对坐标
tolerance = 1.0  # 容差值

for hole in holes:
    # 如果孔位非常接近中心，使用绝对坐标判断
    if abs(hole.center_x) < tolerance:
        # x接近0，根据hole_id判断
        if hole.hole_id.startswith('B'):
            # B侧孔位，x应该为正
            x_sign = 1
        else:
            # A侧孔位，x应该为负
            x_sign = -1
    else:
        x_sign = 1 if hole.center_x > center_x else -1
```

## 效果验证

运行测试脚本后：
1. ✅ 扇形处理顺序：sector_1（右上）→ sector_2（左上）→ sector_3（左下）→ sector_4（右下）
2. ✅ 每个扇形内都从R164行开始检测
3. ✅ 扇形切换时只有一次自适应调整，没有闪烁
4. ✅ x接近0的孔位（如BC098R164 x=-0.000）被正确分配到对应扇形

## 测试命令

```bash
# 运行简单测试
python3 simple_order_test.py

# 运行完整测试
python3 test_detection_order_complete.py
```

## 注意事项

1. 扇形分组使用数学坐标系（Y轴向上），而不是Qt坐标系（Y轴向下）
2. 不同扇形需要不同的Y坐标排序策略
3. 微观视图模式下应禁用自动适配功能