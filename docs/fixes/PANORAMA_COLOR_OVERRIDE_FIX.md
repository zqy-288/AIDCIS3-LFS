# 全景图组件颜色覆盖支持修复

## 问题描述
用户报告在运行模拟检测时出现错误：
```
update_hole_status() takes 3 positional arguments but 4 were given
```

## 问题原因
`src/core_business/graphics/complete_panorama_widget.py` 中的 `CompletePanoramaWidget` 类的 `update_hole_status` 方法不支持 `color_override` 参数，而 `simulation_controller.py` 在调用时传递了这个参数。

## 修复内容

### 1. 更新 `update_hole_status` 方法签名
```python
# 原来：
def update_hole_status(self, hole_id: str, status: HoleStatus):

# 修改为：
def update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None):
```

### 2. 更新 `_update_hole_immediately` 方法
添加了对 `color_override` 参数的支持：
- 如果提供了 `color_override`，调用 `set_color_override` 方法
- 如果 `color_override` 为 None，调用 `clear_color_override` 方法清除覆盖

### 3. 更新批量更新逻辑
修改了 `_execute_batch_update` 方法以处理元组格式的状态数据：
- 支持 `(status, color_override)` 元组格式
- 向后兼容单独的 `status` 值

## 影响范围
此修复确保了全景图组件与其他组件（如 `graphics_view` 和 `simulation_controller`）的接口一致性。

## 测试建议
1. 重新运行模拟检测功能
2. 验证孔位在检测时正确显示蓝色
3. 验证检测完成后颜色正确恢复为状态颜色（绿色/红色）
4. 确认左侧全景图与中间视图的颜色同步

## 相关文件
- `src/core_business/graphics/complete_panorama_widget.py` - 已修复
- `src/pages/main_detection_p1/components/simulation_controller.py` - 调用方
- `src/core_business/graphics/graphics_view.py` - 参考实现