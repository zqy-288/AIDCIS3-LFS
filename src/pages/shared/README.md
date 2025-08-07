# 共享页面组件

这个目录包含所有页面共用的UI组件和基础类，避免代码重复。

## 目录结构

```
shared/
├── dialogs/          # 共享对话框
│   ├── product_selection_dialog.py  # 产品选择对话框
│   └── dxf_render_dialog.py         # DXF渲染对话框
├── widgets/          # 共享小部件  
│   ├── theme_switcher.py            # 主题切换器
│   └── style_detector.py            # 样式检测器
└── base/             # 基础组件
    └── ui_component_base.py         # UI组件基类
```

## 使用原则

1. **跨页面复用**：只有被多个页面使用的组件才放在shared中
2. **高内聚性**：相关组件放在同一个子目录中
3. **向后兼容**：迁移时保持原有API不变
4. **清晰依赖**：避免shared组件依赖特定页面的组件

## 迁移计划

### 优先级1 (立即迁移)
- [ ] `src/modules/product_selection.py` → `dialogs/product_selection_dialog.py`
- [ ] `src/modules/ui_component_base.py` → `base/ui_component_base.py`

### 优先级2 (计划内)  
- [ ] `src/modules/dxf_render_dialog.py` → `dialogs/dxf_render_dialog.py`
- [ ] `src/modules/theme_switcher.py` → `widgets/theme_switcher.py`

### 优先级3 (后续)
- [ ] 其他通用UI组件按需迁移