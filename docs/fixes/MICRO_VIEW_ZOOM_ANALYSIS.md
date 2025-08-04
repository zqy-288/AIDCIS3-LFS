# 微观视图初始缩放问题分析报告

## 问题描述
微观视图在初始显示时缩放过大，导致孔位显示不完整。

## 问题原因分析

### 1. 重复缩放操作
在微观视图显示扇形时，存在多次缩放操作：

1. **第一次缩放**：在 `native_main_detection_view_p1.py` 的 `_show_sector_in_view` 方法中：
   ```python
   # 适配视图到扇形区域（只调用一次）
   graphics_view.fitInView(bounding_rect, Qt.KeepAspectRatio)
   ```

2. **第二次缩放**：在 `graphics_view.py` 的 `switch_to_micro_view` 方法中：
   ```python
   # 否则放大到合适的微观视图比例
   self.set_micro_view_scale()
   ```

### 2. 缩放范围设置不当
在 `set_micro_view_scale` 方法中：
```python
# 微观视图的缩放范围
min_micro_scale = 1.2
max_micro_scale = 4.0
```

如果 `fitInView` 已经将视图适配到合适大小，再乘以 1.2-4.0 的缩放因子会导致过度放大。

### 3. 缺少缩放状态检查
`set_micro_view_scale` 方法没有检查是否已经通过 `fitInView` 设置了合适的缩放。

## 已应用的修复

### 1. 添加缩放锁检查
在 `set_micro_view_scale` 方法开始处添加了检查：
```python
# 如果正在进行 fitInView 操作，跳过额外缩放
if getattr(self, '_is_fitting', False):
    self.logger.info("跳过 set_micro_view_scale（正在进行 fitInView）")
    return
    
# 如果已经通过 fitInView 设置了合适的缩放，跳过
if getattr(self, '_fitted_to_sector', False):
    self.logger.info("跳过 set_micro_view_scale（已适配到扇形）")
    # 重置标志
    self._fitted_to_sector = False
    return
```

### 2. 调整缩放范围
降低了微观视图的缩放范围：
```python
# 微观视图的缩放范围（调整后）
min_micro_scale = 0.8  # 降低最小值，因为可能已经通过 fitInView 放大
max_micro_scale = 3.0  # 降低最大值，避免过度放大
```

### 3. 设置标志位
在 `_show_sector_in_view` 的 `fitInView` 后设置标志：
```python
# 适配视图到扇形区域（只调用一次）
graphics_view.fitInView(bounding_rect, Qt.KeepAspectRatio)

# 设置标志，告诉 set_micro_view_scale 跳过额外缩放
graphics_view._fitted_to_sector = True
```

## 缩放流程优化

### 修复前的流程：
1. 点击扇形 → `_show_sector_in_view`
2. 调用 `fitInView` 适配到扇形区域
3. 切换到微观视图 → `switch_to_micro_view`
4. 调用 `set_micro_view_scale` 再次缩放
5. 结果：双重缩放导致过度放大

### 修复后的流程：
1. 点击扇形 → `_show_sector_in_view`
2. 调用 `fitInView` 适配到扇形区域
3. 设置 `_fitted_to_sector = True` 标志
4. 切换到微观视图 → `switch_to_micro_view`
5. `set_micro_view_scale` 检测到标志，跳过额外缩放
6. 结果：只有一次合适的缩放

## 测试建议

1. **初始加载测试**：
   - 启动程序，检查微观视图的初始缩放是否正常
   - 扇形中的孔位应该完整显示，不会过度放大

2. **视图切换测试**：
   - 在宏观和微观视图之间切换
   - 确保缩放保持合理，不会累积

3. **扇形切换测试**：
   - 点击不同扇形
   - 每个扇形都应该以合适的缩放显示

4. **手动缩放测试**：
   - 使用鼠标滚轮或缩放按钮
   - 确保手动缩放功能正常

## 相关文件
- `/Users/vsiyo/Desktop/AIDCIS3-LFS/src/core_business/graphics/graphics_view.py`
- `/Users/vsiyo/Desktop/AIDCIS3-LFS/src/pages/main_detection_p1/native_main_detection_view_p1.py`