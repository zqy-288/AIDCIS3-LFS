# 重构优先级列表

## 🔴 高优先级重构（急需处理）

### 1. main_window.py (5882行)
**问题**：
- 单个文件过大，包含156个方法
- 职责过多，难以维护
- 高耦合度

**建议方案**：
- 拆分为多个模块：
  - `MainWindowUI` - UI布局和初始化
  - `MenuManager` - 菜单管理
  - `ToolbarManager` - 工具栏管理
  - `EventHandler` - 事件处理
  - `StateManager` - 状态管理
  - `CoordinatorService` - 模块协调

### 2. 插件系统 (17个文件，总计约291KB)
**问题**：
- 严重过度设计
- 功能重复和重叠
- 文件过多，难以理解

**建议方案**：
- 合并为3-4个核心模块：
  - `plugin_core.py` - 核心接口和管理器
  - `plugin_loader.py` - 加载和生命周期
  - `plugin_config.py` - 配置管理
  - `plugin_utils.py` - 工具函数

### 3. history_viewer.py (2091行)
**问题**：
- 单个类承担过多职责
- UI和业务逻辑混合

**建议方案**：
- 拆分为：
  - `HistoryDataManager` - 数据管理
  - `HistoryUI` - UI组件
  - `HistoryFilter` - 过滤和搜索
  - `HistoryExporter` - 导出功能

## 🟡 中优先级重构

### 4. 错误处理系统 (5个文件，约109KB)
**问题**：
- 功能分散在多个文件
- 存在重复代码
- 缺乏统一的错误处理策略

**建议方案**：
- 统一为2个模块：
  - `error_handler.py` - 核心错误处理
  - `error_reporter.py` - 错误报告和日志

### 5. report_output_interface.py (1363行)
**问题**：
- 单文件过大
- 多种报告格式混在一起

**建议方案**：
- 按输出格式拆分：
  - `report_base.py` - 基础类
  - `pdf_reporter.py` - PDF输出
  - `excel_reporter.py` - Excel输出
  - `html_reporter.py` - HTML输出

### 6. UI组件基础类 (ui_component_base.py - 1037行)
**问题**：
- 基类过于复杂
- 包含过多功能

**建议方案**：
- 拆分为：
  - `base_widget.py` - 基础Widget
  - `ui_mixins.py` - 可复用的Mixin类
  - `ui_helpers.py` - UI辅助函数

## 🟢 低优先级重构

### 7. theme_manager.py (1139行)
**问题**：
- 主题定义和管理混合
- 代码组织不清晰

**建议方案**：
- 拆分为：
  - `theme_definitions.py` - 主题定义
  - `theme_manager.py` - 主题管理逻辑
  - `theme_utils.py` - 工具函数

### 8. Graphics相关组件
**问题**：
- 存在重复的渲染逻辑
- 文件组织混乱

**建议方案**：
- 统一图形渲染架构
- 创建共享的渲染基础设施

## 📊 重构收益评估

| 模块 | 当前行数 | 目标行数 | 复杂度降低 | 可维护性提升 |
|------|---------|---------|------------|-------------|
| main_window.py | 5882 | < 500 | 80% | ⭐⭐⭐⭐⭐ |
| 插件系统 | ~9000 | ~2000 | 75% | ⭐⭐⭐⭐⭐ |
| history_viewer.py | 2091 | < 400 | 70% | ⭐⭐⭐⭐ |
| 错误处理 | ~3000 | ~800 | 60% | ⭐⭐⭐⭐ |
| report_output_interface.py | 1363 | < 300 | 65% | ⭐⭐⭐ |

## 🚀 推荐执行顺序

1. **第一阶段**：main_window.py（影响最大，收益最高）
2. **第二阶段**：插件系统（简化架构，减少复杂度）
3. **第三阶段**：history_viewer.py（改善用户体验）
4. **第四阶段**：错误处理系统（提高稳定性）
5. **第五阶段**：其他模块逐步优化

## 💡 重构原则

1. **单一职责**：每个类/模块只负责一个功能
2. **高内聚低耦合**：相关功能聚合，减少依赖
3. **可测试性**：便于单元测试和集成测试
4. **向后兼容**：保持API稳定，平滑迁移
5. **渐进式重构**：小步快跑，持续改进