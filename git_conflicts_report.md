# Git 合并冲突报告

**合并分支**: `origin/zqy` → `wsy_2`  
**生成时间**: 2025-07-17  
**冲突文件总数**: 7个内容冲突 + 17个删除冲突  

## 🔥 冲突概览

### 内容冲突文件 (Content Conflicts)
| 文件路径 | 冲突类型 | 冲突数量 | 主要冲突区域 |
|---------|----------|----------|-------------|
| `src/main.py` | 内容冲突 | 1处 | 主题应用方式 |
| `src/modules/theme_manager.py` | 添加/添加冲突 | 多处 | 整个文件结构 |
| `src/modules/history_viewer.py` | 内容冲突 | 未知 | 代码逻辑差异 |
| `src/modules/realtime_chart.py` | 内容冲突 | 未知 | 实时图表功能 |
| `src/modules/report_output_interface.py` | 内容冲突 | 未知 | 报告输出接口 |
| `src/modules/unified_history_viewer.py` | 内容冲突 | 未知 | 统一历史查看器 |
| `reports/report_history.json` | 内容冲突 | 1处 | JSON数据结构 |

### 删除冲突文件 (Rename/Delete Conflicts)
| 文件路径 | 冲突类型 | 本地状态 | 远程状态 |
|---------|----------|----------|----------|
| `Data/R001C001/BISDM/result/*.png` | 重命名/删除 | 已删除 | 从H00001重命名 |
| `Data/R001C001/BISDM/result/2-7.0.txt` | 重命名/删除 | 已删除 | 从H00001重命名 |
| `Data/R001C001/CCIDM/*.csv` | 重命名/删除 | 已删除 | 从H00001重命名 |
| `Data/R001C002/BISDM/result/*.png` | 重命名/删除 | 已删除 | 从H00002重命名 |
| `Data/R001C002/BISDM/result2/*.png` | 重命名/删除 | 已删除 | 从H00002重命名 |
| `Data/R001C002/CCIDM/*.csv` | 重命名/删除 | 已删除 | 从H00002重命名 |
| `Data/R001C003/CCIDM/*.csv` | 重命名/删除 | 已删除 | 从H00003重命名 |

## 📋 详细冲突分析

### 1. src/main.py - 主题应用冲突

**冲突位置**: 第113-158行  
**冲突类型**: 主题管理方式差异

#### 本地版本 (HEAD/wsy_2):
```python
# 应用现代科技蓝深色主题作为默认主题 - 强制模式
try:
    from modules.theme_manager import theme_manager
    
    # 1. 首先设置全局强制深色样式表
    colors = theme_manager.COLORS
    global_dark_style = f"""
    * {{
        background-color: {colors['background_primary']} !important;
        color: {colors['text_primary']} !important;
    }}
    QMainWindow {{
        background-color: {colors['background_primary']} !important;
    }}
    QLabel {{
        color: {colors['text_primary']} !important;
    }}
    QPushButton {{
        background-color: {colors['background_tertiary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border_normal']} !important;
    }}
    QTabWidget::pane {{
        background-color: {colors['background_secondary']} !important;
    }}
    QTabBar::tab {{
        background-color: {colors['background_tertiary']} !important;
        color: {colors['text_primary']} !important;
    }}
    QTabBar::tab:selected {{
        background-color: {colors['accent_primary']} !important;
        color: white !important;
    }}
    """
    app.setStyleSheet(global_dark_style)
    
    # 2. 然后应用主题管理器的深色主题
    theme_manager.apply_dark_theme(app)
    print("🎨 强制深色主题已应用（全局!important样式）")
```

#### 远程版本 (origin/zqy):
```python
# 应用现代科技蓝主题
try:
    from modules.theme_manager import theme_manager
    theme_manager.apply_theme(app)
    print("✅ 现代科技蓝主题已应用")
```

**差异说明**: 
- 本地版本使用强制深色主题，包含详细的CSS样式覆盖
- 远程版本使用简化的主题应用方式

### 2. src/modules/theme_manager.py - 添加/添加冲突

**冲突类型**: 两个分支都添加了同名文件，但内容不同  
**冲突数量**: 多处冲突标记

**说明**: 这是最复杂的冲突，两个分支都独立实现了主题管理器，需要仔细比较功能差异。

### 3. reports/report_history.json - JSON数据冲突

**冲突位置**: 第3-29行  
**冲突类型**: JSON数据结构差异

**说明**: 报告历史记录的数据结构在两个分支中有不同的更新。

### 4. 数据文件删除冲突

**问题描述**: 远程分支将孔位数据从 `H00001/H00002/H00003` 格式重命名为 `R001C001/R001C002/R001C003` 格式，但本地分支已删除这些文件。

**涉及文件**:
- 6个PNG图像文件 (BISDM结果)
- 8个PNG图像文件 (BISDM result2)
- 1个TXT文件 (BISDM结果)
- 3个CSV测量数据文件 (CCIDM)

## 🚨 冲突解决建议

### 优先级处理顺序:

1. **高优先级**: 
   - `src/main.py` - 决定主题应用策略
   - `src/modules/theme_manager.py` - 核心主题管理功能

2. **中优先级**:
   - 其他Python模块的功能冲突
   - `reports/report_history.json` - 数据完整性

3. **低优先级**:
   - 数据文件的重命名/删除冲突

### 推荐解决策略:

1. **主题管理**: 建议保留本地版本的强制深色主题功能，因为这是用户明确需要的功能
2. **数据文件**: 建议接受远程版本的重命名方案，恢复数据文件
3. **其他模块**: 需要逐一分析功能差异，选择最优实现

## ⚠️ 注意事项

- **不要自动合并**: 等待用户审查后再决定解决方案
- **备份重要更改**: 当前本地修改已使用 `git stash` 保存
- **测试验证**: 解决冲突后需要完整测试所有功能

## 📊 统计信息

- **总冲突数**: 24个
- **内容冲突**: 7个文件
- **删除冲突**: 17个文件
- **新增文件**: 30个文档文件
- **修改文件**: 6个代码文件

---
*报告生成时间: 2025-07-17*  
*Git操作: merge origin/zqy into wsy_2*