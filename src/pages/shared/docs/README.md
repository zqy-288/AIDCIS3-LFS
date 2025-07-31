# 共享组件文档

本目录包含页面组件架构分析和使用指南。

## 文档列表

- `P1_COMPONENT_ANALYSIS.md` - P1页面组件使用情况详细分析报告

## 共享组件使用指南

### 通用UI组件

位于 `src/pages/shared/ui/components/` 下的组件可以在多个页面间复用：

- **InfoPanelComponent** - 标准化信息显示面板，支持MVVM数据绑定
- **OperationsPanelComponent** - 标准化操作控制面板，包含完整的功能组

### 数据模型

位于 `src/pages/shared/view_models/` 下的模型遵循MVVM架构：

- **MainViewModel** - 主视图数据模型，包含完整的UI状态管理

## 使用示例

```python
# 导入共享UI组件
from src.pages.shared.ui.components import InfoPanelComponent, OperationsPanelComponent

# 导入共享数据模型  
from src.pages.shared.view_models import MainViewModel

# 在新页面中使用
class NewPage(QWidget):
    def __init__(self):
        super().__init__()
        self.info_panel = InfoPanelComponent()
        self.operations_panel = OperationsPanelComponent()
        self.view_model = MainViewModel()
```

## 设计原则

1. **高内聚，低耦合** - 每个组件功能独立完整
2. **标准化接口** - 遵循统一的API设计规范  
3. **MVVM架构** - 数据与UI分离，便于测试和维护
4. **向后兼容** - 保持接口稳定性，支持渐进式迁移

---

*更新时间：2025-01-29*