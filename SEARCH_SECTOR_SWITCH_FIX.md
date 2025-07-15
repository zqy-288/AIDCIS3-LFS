# 搜索功能扇形自动切换修复

## 问题描述
搜索孔位时，如果该孔位不在当前显示的扇形中，虽然搜索功能找到了孔位，但用户看不到高亮效果，因为 DynamicSectorDisplayWidget 只显示当前扇形的内容。

## 重要发现
管板的中心点不在原点(0,0)，而是在管板所有孔位的几何中心。对于东重管板.dxf文件，中心点在 (1.54, -1.69)。扇形划分是基于这个几何中心进行的。

## 解决方案

### 1. 创建扇形切换函数
在 `main_window.py` 中添加了 `_switch_to_hole_sector()` 方法：

```python
def _switch_to_hole_sector(self, hole):
    """切换到包含指定孔位的扇形
    
    Args:
        hole: HoleData对象
        
    Returns:
        bool: 是否成功切换到对应扇形
    """
```

该方法：
- 计算孔位相对于中心的角度
- 确定孔位属于哪个扇形（SECTOR_1-4）
- 如果不在当前扇形，自动切换到目标扇形
- 等待切换完成后返回

### 2. 集成到搜索功能
修改 `perform_search()` 方法，在高亮之前先切换扇形：

```python
if matched_holes:
    # 如果只有一个匹配结果，自动切换到该孔位所在的扇形
    if len(matched_holes) == 1:
        self._switch_to_hole_sector(matched_holes[0])
    # 如果有多个结果，检查是否有精确匹配
    elif len(matched_holes) > 1:
        exact_match = None
        for hole in matched_holes:
            if hole.hole_id.upper() == search_text_upper:
                exact_match = hole
                break
        if exact_match:
            self._switch_to_hole_sector(exact_match)
    
    # 高亮匹配的孔位
    if hasattr(self, 'graphics_view'):
        self.graphics_view.highlight_holes(matched_holes, search_highlight=True)
```

## 工作流程

1. 用户输入搜索关键字（如 C001R004）
2. 系统找到匹配的孔位
3. 计算孔位所在的扇形
4. 如果不在当前扇形，自动切换到正确的扇形
5. 在新扇形中高亮显示搜索结果（紫色高亮）

## 测试验证

创建了 `test_search_sector_switch.py` 测试脚本：
- 测试不同扇形的孔位搜索
- 验证自动切换功能
- 检查高亮状态

## 效果

- ✅ 搜索时自动切换到包含目标孔位的扇形
- ✅ 用户能够看到搜索结果的紫色高亮
- ✅ 提升了搜索功能的用户体验
- ✅ 保持了扇形专注显示的设计理念