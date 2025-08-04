# 初始显示比例修复总结

## 问题描述
用户希望初始显示比例与点击"微观孔位视图"按钮后的效果完全一致。

## 根本原因
初始加载时使用了`_load_default_sector1`方法，而点击微观视图按钮时使用的是`_on_view_mode_changed`方法，虽然最终都调用`_show_sector_in_view`，但初始化时机和处理流程略有不同。

## 修复方案
将初始加载改为使用与视图切换相同的逻辑：

**文件**: src/pages/main_detection_p1/native_main_detection_view_p1.py（第1772-1774行）

```python
# 原代码：
if is_micro_view:
    self.logger.info("🔍 准备加载默认扇形sector1")
    self._load_default_sector1()

# 新代码：
if is_micro_view:
    self.logger.info("🔍 准备加载默认扇形sector1")
    # 使用与视图切换相同的逻辑
    from PySide6.QtCore import QTimer
    QTimer.singleShot(100, lambda: self._on_view_mode_changed("micro"))
```

## 逻辑流程对比

### 初始加载流程（修复后）
1. `load_hole_collection()` - 设置微观视图模式
2. 加载数据并隐藏所有项
3. QTimer延迟100ms调用`_on_view_mode_changed('micro')`
4. `_on_view_mode_changed()` -> `_show_sector_in_view()`

### 点击微观视图按钮流程
1. 按钮点击 -> `_on_view_mode_changed('micro')`
2. `_on_view_mode_changed()` -> `_show_sector_in_view()`

## 效果
- 初始加载和点击按钮使用完全相同的逻辑路径
- 通过QTimer延迟确保所有组件初始化完成
- 显示效果完全一致，包括缩放比例、边距等

## 其他相关修复
1. 扇形显示边距增加到200像素
2. `_show_sector_in_view`中的fitInView保持不变
3. `_fitted_to_sector`标志确保不会重复缩放

现在初始显示与点击"微观孔位视图"按钮的效果应该完全一致。