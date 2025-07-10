# AIDCIS3 项目文件组织结构

## 📁 目录结构说明

### 🏗️ 核心项目文件
```
AIDCIS3/
├── main.py                    # 主程序入口
├── main_window.py            # 主窗口实现
├── requirements.txt          # 项目依赖
├── requirements-dev.txt      # 开发依赖
└── README.md                # 项目说明
```

### 📦 核心模块 (modules/)
```
modules/
├── __init__.py
├── defect_annotation_tool.py     # 缺陷标注工具
├── annotation_graphics_view.py   # 标注图形视图
├── defect_annotation_model.py    # 标注数据模型
├── defect_category_manager.py    # 缺陷类别管理
├── archive_manager.py            # 归档管理
├── image_scanner.py              # 图像扫描器
├── yolo_file_manager.py          # YOLO文件管理
├── endoscope_view.py             # 内窥镜视图
├── history_viewer.py             # 历史查看器
├── main_detection_view.py        # 主检测视图
├── matplotlib_chart.py          # 图表组件
├── realtime_chart.py            # 实时图表
├── workpiece_diagram.py         # 工件图表
├── models.py                     # 数据模型
├── worker_thread.py             # 工作线程
└── font_config.py               # 字体配置
```

### 🧪 测试文件 (scripts/tests/)
```
scripts/tests/
├── test_annotation_*.py         # 标注功能测试
├── test_archive_*.py            # 归档功能测试
├── test_defect_*.py             # 缺陷检测测试
├── test_graphics_*.py           # 图形界面测试
├── test_history_*.py            # 历史功能测试
├── test_image_*.py              # 图像处理测试
├── test_integration_*.py        # 集成测试
├── test_ui_*.py                 # UI测试
├── test_yolo_*.py               # YOLO相关测试
└── test_*.py                    # 其他测试文件
```

### 🔧 调试工具 (scripts/debug/)
```
scripts/debug/
├── debug_annotation_detection.py  # 标注检测调试
├── debug_dxf_*.py                 # DXF相关调试
├── debug_hole_*.py                # 孔位相关调试
├── debug_search_*.py              # 搜索功能调试
├── debug_simulation_*.py          # 仿真调试
└── debug_*.py                     # 其他调试工具
```

### ✅ 验证脚本 (scripts/verification/)
```
scripts/verification/
├── automated_test_verification.py  # 自动化测试验证
├── comprehensive_diagnosis.py      # 综合诊断
├── final_verification.py          # 最终验证
├── final_test_verification.py     # 最终测试验证
├── verify_*.py                    # 各种验证脚本
└── *_verification.py              # 验证相关文件
```

### 🛠️ 实用工具 (scripts/utilities/)
```
scripts/utilities/
├── quick_*.py                     # 快速测试工具
├── simple_*.py                    # 简单工具
├── minimal_*.py                   # 最小化工具
├── fix_*.py                       # 修复工具
├── panel_*.py                     # 面板相关工具
├── priority*.py                   # 优先级相关
├── stability_*.py                 # 稳定性测试
├── ui_*.py                       # UI相关工具
├── endoscope_*.py                # 内窥镜相关
├── realtime_*.py                 # 实时相关
└── run_*.py                      # 运行脚本
```

### 📚 文档 (docs/)
```
docs/
├── guides/                       # 使用指南
│   ├── Quick_Start_Guide.md
│   ├── Technical_Implementation_Guide.md
│   └── 安装运行指南.md
├── reports/                      # 报告文档
│   ├── PROJECT_COMPLETION_REPORT.md
│   ├── TEST_REPORT.md
│   ├── WARNING_FIXES_REPORT.md
│   ├── dependency_analysis_report.md
│   └── *.md                     # 各种报告
└── README.md                    # 文档说明
```

### 🗄️ 备份文件 (backup/)
```
backup/
├── old_versions/                 # 旧版本文件
│   ├── *backup*.py
│   ├── *old*.py
│   └── 历史版本文件
└── 副本/                        # 项目副本
```

### 📊 数据目录
```
Data/                            # 原始数据
├── H00001/                     # 孔位数据
├── H00002/                     # 孔位数据
└── ...

Archive/                         # 归档数据
├── H00001/                     # 归档的孔位数据
├── archive_index.json          # 归档索引
└── ...

cache/                          # 缓存文件
├── *.csv                       # 测量数据缓存
├── *.json                      # JSON缓存
├── *.db                        # 数据库文件
└── ...

"DXF Graph"/                    # DXF文件
├── 东重管板.dxf
├── 测试管板.dxf
└── *.dxf
```

### 🔧 硬件模块 (hardware/)
```
hardware/
├── __init__.py
├── CR1500_controller.py        # CR1500控制器
└── ...
```

### 🏛️ AIDCIS2集成 (aidcis2/)
```
aidcis2/
├── __init__.py
├── config/                     # 配置文件
├── data_management/            # 数据管理
├── graphics/                   # 图形组件
├── integration/                # 集成模块
├── log_system/                 # 日志系统
├── models/                     # 数据模型
├── performance/                # 性能模块
├── search/                     # 搜索功能
├── ui/                        # 用户界面
├── data_adapter.py            # 数据适配器
└── dxf_parser.py              # DXF解析器
```

### 🧪 测试框架 (tests/)
```
tests/
├── __init__.py
├── unit/                      # 单元测试
├── integration/               # 集成测试
├── system/                    # 系统测试
├── ui_interaction/            # UI交互测试
├── performance/               # 性能测试
└── run_*.py                   # 测试运行脚本
```

### 📋 其他目录
```
merge/                         # 合并相关文档
├── integration_checklist.md
├── integration_tests.md
└── ...

reference/                     # 参考文件
├── matlab.txt
└── ...

PySide6_Project_Shared_Context/ # 项目共享上下文
├── 01_mandate.md
├── 02_blueprint.md
└── ...
```

## 🚀 使用说明

### 运行主程序
```bash
python main.py
```

### 运行测试
```bash
# 运行所有测试
python scripts/tests/test_all_functions.py

# 运行特定功能测试
python scripts/tests/test_annotation_labels.py
```

### 调试工具
```bash
# 调试标注检测
python scripts/debug/debug_annotation_detection.py

# 调试DXF显示
python scripts/debug/debug_dxf_display.py
```

### 验证脚本
```bash
# 综合验证
python scripts/verification/comprehensive_diagnosis.py

# 最终验证
python scripts/verification/final_verification.py
```

## 📝 文件整理完成

✅ **已完成的整理工作：**
- 测试文件移动到 `scripts/tests/`
- 调试文件移动到 `scripts/debug/`
- 验证文件移动到 `scripts/verification/`
- 实用工具移动到 `scripts/utilities/`
- 文档文件移动到 `docs/reports/`
- 备份文件移动到 `backup/`
- 数据文件整理到对应目录

✅ **保持原位置的重要文件：**
- `main.py` - 主程序入口
- `main_window.py` - 主窗口
- `modules/` - 核心模块目录
- `requirements.txt` - 依赖文件
- `Data/` - 数据目录
- `Archive/` - 归档目录

这样的组织结构使项目更加清晰，便于维护和开发。
