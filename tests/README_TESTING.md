# 主窗口测试指南

本文档介绍如何测试增强版主窗口的完整功能。

## 测试环境准备

### 1. 安装测试依赖

```bash
# 基础测试框架
pip install pytest pytest-qt pytest-cov

# Playwright测试（Web应用）
pip install pytest-playwright
playwright install chromium

# 性能测试
pip install psutil memory_profiler
```

### 2. 项目结构

```
tests/
├── test_main_window_desktop.py   # 桌面应用单元测试
├── playwright/
│   └── test_main_window_enhanced.py  # Playwright集成测试
├── run_main_window_tests.py      # 测试运行器
└── README_TESTING.md             # 本文档
```

## 测试类型

### 1. 单元测试

使用pytest和pytest-qt测试Qt组件：

```bash
# 运行所有单元测试
pytest tests/test_main_window_desktop.py -v

# 运行特定测试
pytest tests/test_main_window_desktop.py::TestMainWindowDesktop::test_three_column_layout -v

# 生成覆盖率报告
pytest tests/test_main_window_desktop.py --cov=src.main_window --cov-report=html
```

### 2. 集成测试

使用测试运行器进行交互式测试：

```bash
python tests/run_main_window_tests.py
# 选择选项 2 运行集成测试
```

### 3. 性能测试

```bash
python tests/run_main_window_tests.py
# 选择选项 3 运行性能测试
```

## 测试覆盖范围

### 布局测试
- ✅ 三栏布局结构（左中右面板）
- ✅ 工具栏组件
- ✅ 选项卡创建和切换
- ✅ 全景图集成
- ✅ 响应式布局

### 功能测试
- ✅ DXF文件加载
- ✅ 产品选择
- ✅ 搜索功能
- ✅ 视图过滤
- ✅ 蛇形路径控制
- ✅ 检测控制（开始/暂停/停止）
- ✅ 视图模式切换（宏观/微观）

### 组件集成测试
- ✅ InfoPanelComponent
- ✅ VisualizationPanelComponent
- ✅ OperationsPanelComponent
- ✅ ToolbarComponent
- ✅ PanoramaController
- ✅ DynamicSectorDisplay

### 数据流测试
- ✅ 视图模型绑定
- ✅ 信号连接
- ✅ 状态更新
- ✅ 错误处理

## 测试数据

测试使用以下数据文件：
- `assets/dxf/DXF Graph/东重管板.dxf` - 大型测试文件（25,270个孔位）
- `assets/dxf/DXF Graph/测试管板.dxf` - 小型测试文件

## 常见测试场景

### 场景1：完整检测流程
1. 启动应用
2. 加载DXF文件
3. 选择产品型号
4. 开始检测
5. 暂停/继续检测
6. 查看实时统计
7. 停止检测
8. 导出报告

### 场景2：视图操作
1. 切换宏观/微观视图
2. 使用搜索功能定位孔位
3. 启用蛇形路径显示
4. 切换不同扇形视图
5. 使用全景图导航

### 场景3：数据分析
1. 切换到历史数据选项卡
2. 查询历史记录
3. 分析统计数据
4. 生成报告

## 性能基准

- 窗口初始化：< 1秒
- DXF文件加载（25k孔位）：< 3秒
- 视图切换：< 100ms
- 内存使用：< 500MB

## 已知问题和限制

1. Playwright测试需要Web服务器运行（桌面应用需要特殊配置）
2. 某些Qt控件可能需要特定的测试方法
3. 性能测试结果可能因硬件而异

## 调试技巧

1. 使用 `-s` 参数查看print输出：
   ```bash
   pytest tests/test_main_window_desktop.py -v -s
   ```

2. 使用 `--pdb` 进入调试器：
   ```bash
   pytest tests/test_main_window_desktop.py --pdb
   ```

3. 查看Qt对象树：
   ```python
   window.dumpObjectTree()
   ```

## 持续集成

可以将测试集成到CI/CD流程中：

```yaml
# .github/workflows/test.yml
name: Test Main Window

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-qt pytest-cov
    - name: Run tests
      run: pytest tests/test_main_window_desktop.py -v --cov
```

## 测试报告

测试完成后，可以在以下位置找到报告：
- 覆盖率报告：`htmlcov/index.html`
- pytest报告：终端输出
- 性能报告：`tests/performance_report.txt`