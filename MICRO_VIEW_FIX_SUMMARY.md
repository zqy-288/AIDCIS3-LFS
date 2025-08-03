# 微观视图默认显示修复总结

## 问题描述
用户报告微观视图按钮虽然默认选中，但中间视图仍显示整个圆形管板而不是放大的扇形。

## 问题原因
在 `load_hole_collection` 方法中，无论是宏观还是微观视图模式，都会调用 `graphics_view.load_holes()` 来加载并显示所有孔位数据。这导致即使在微观视图模式下，也会先显示所有孔位。

## 修复方案
修改了 `native_main_detection_view_p1.py` 的数据加载逻辑：

### 1. 区分视图模式加载
```python
# 检查当前视图模式
is_micro_view = (self.center_panel and 
               hasattr(self.center_panel, 'micro_view_btn') and 
               self.center_panel.micro_view_btn.isChecked())

if is_micro_view:
    # 微观视图：加载数据但隐藏所有项
    graphics_view.load_holes(self.current_hole_collection)
    for item in scene.items():
        item.setVisible(False)
    # 然后加载默认扇形
    self._load_default_sector1()
else:
    # 宏观视图：正常加载并显示
    graphics_view.load_holes(self.current_hole_collection)
    graphics_view.fit_in_view_with_margin()
```

## 效果
1. **微观视图模式**：
   - 数据加载到场景但初始隐藏
   - 自动调用 `_load_default_sector1` 显示sector1
   - 只显示选中扇形的孔位

2. **宏观视图模式**：
   - 正常加载并显示所有孔位
   - 自动调整视图以适应所有内容

## 相关修复
- 坐标系统一（数学坐标系）
- 防止多次自适应缩放
- 确保扇形选择和显示一致性

## 验证方法
1. 启动应用并加载DXF文件
2. 检查中间视图是否只显示sector1的放大内容
3. 切换到宏观视图，确认显示完整圆形
4. 切换回微观视图，确认恢复扇形显示