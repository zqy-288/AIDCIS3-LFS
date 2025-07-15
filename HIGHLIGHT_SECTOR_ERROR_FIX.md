# 修复 CompletePanoramaWidget 高亮扇形错误

## 错误描述
```
AttributeError: 'CompletePanoramaWidget' object has no attribute 'sector_offset_enabled'
```

## 问题原因
在 `highlight_sector` 方法的 except 块后面，错误地包含了另一个方法的代码片段：
```python
except Exception as e:
    print(f"❌ [全景图] 高亮扇形失败: {e}")
"""强制应用偏移设置"""  # 这是另一个方法的文档字符串
if not self.sector_offset_enabled or not hasattr(self, 'graphics_view'):  # 这些代码不应该在这里
    return
```

这导致 `CompletePanoramaWidget` 试图访问不存在的 `sector_offset_enabled` 属性。

## 修复方案
1. 正确结束 `highlight_sector` 方法
2. 将错误包含的代码移到新的 `_force_apply_offset` 方法中
3. 添加适当的错误处理和恢复机制

## 修复后的代码结构
```python
def highlight_sector(self, sector: SectorQuadrant):
    """高亮显示指定的扇形区域"""
    try:
        # ... 高亮逻辑
    except Exception as e:
        print(f"❌ [全景图] 扇形高亮失败: {e}")
        import traceback
        traceback.print_exc()
        # 强制重新创建高亮系统作为恢复机制
        QTimer.singleShot(100, self._recreate_all_highlights)

def _force_apply_offset(self):
    """强制应用偏移设置"""
    if not self.sector_offset_enabled or not hasattr(self, 'graphics_view'):
        return
    # ... 偏移逻辑
```

## 效果
- 修复了 AttributeError 错误
- 扇形高亮功能正常工作
- 保持了代码的正确结构和逻辑分离