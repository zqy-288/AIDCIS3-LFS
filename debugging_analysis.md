# AIDCIS 渲染问题深入分析

## 当前问题总结

1. **中间列扇形偏移不工作**
   - 偏移计算已正确实现
   - 使用了 QTransform 而非 fitInView
   - 但视觉上扇形仍然居中显示

2. **小型全景图不实时更新**
   - 左侧栏可以实时显示绿点
   - 小型浮动全景图在模拟过程中不更新
   - 只有停止后才显示状态

3. **_synchronize_panorama_status 未被调用**
   - 日志显示该函数从未执行
   - 信号连接可能有问题

## 问题根本原因分析

### 1. 中间列偏移问题

**可能原因：**
- QTransform 被其他地方的代码覆盖
- 视图的 resizeEvent 或 paintEvent 重新居中
- QTimer 延迟调用的 centerOn 仍在执行
- 扇形高亮项的边界计算影响了视图定位

**验证方法：**
```python
# 在 display_current_sector 后添加验证
QTimer.singleShot(500, lambda: self._check_actual_center())
```

### 2. 小型全景图更新问题

**可能原因：**
- mini_panorama 是 OptimizedGraphicsView 实例，不是 CompletePanoramaWidget
- 缺少正确的 hole_items 字典
- 场景没有正确初始化
- 更新调用链断裂

**验证方法：**
```python
# 检查 mini_panorama 的实际类型和属性
print(f"mini_panorama 类型: {type(mini_panorama)}")
print(f"有 hole_items: {hasattr(mini_panorama, 'hole_items')}")
print(f"有 update_hole_status: {hasattr(mini_panorama, 'update_hole_status')}")
```

### 3. 信号连接问题

**可能原因：**
- status_updated 信号未正确发射
- 信号在错误的时机连接
- 接收器函数参数不匹配

**验证方法：**
```python
# 检查信号连接
print(f"status_updated 信号接收器数量: {self.receivers(self.status_updated)}")
```

## 解决方案

### 方案 1：修复偏移显示
1. 完全禁用所有自动居中机制
2. 使用 setSceneRect 限制视图区域
3. 重写 resizeEvent 防止重新居中

### 方案 2：修复小型全景图
1. 将 mini_panorama 改为 CompletePanoramaWidget 实例
2. 或者为 OptimizedGraphicsView 添加 hole_items 字典
3. 确保场景正确共享或同步

### 方案 3：修复信号链
1. 在模拟更新时直接调用同步函数
2. 添加信号监听器调试输出
3. 确保参数类型匹配

## 调试代码位置

需要在以下位置添加调试代码：

1. **main_window.py**
   - `_update_simulation_progress()` - 添加直接同步调用
   - `__init__()` - 添加信号连接验证
   - `_on_status_updated()` - 添加接收确认

2. **dynamic_sector_view.py**
   - `display_current_sector()` - 添加变换验证
   - `_update_panorama_hole_status()` - 添加调用追踪
   - `update_mini_panorama_hole_status()` - 添加参数验证

3. **graphics_view.py**
   - `resizeEvent()` - 检查是否触发重新居中
   - `fit_in_view_with_margin()` - 确认 disable_auto_center 生效