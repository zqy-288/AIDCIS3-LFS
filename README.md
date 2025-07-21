# AIDCIS2-AIDCIS3 管孔检测系统

## 项目简介
基于PySide6的管孔检测系统上位机软件，支持DXF文件加载、实时监控、历史数据分析和缺陷标注。

## 目录结构
```
AIDCIS2-AIDCIS3/
├── src/                    # 源代码
│   ├── main.py            # 程序入口
│   ├── main_window.py     # 主窗口
│   ├── aidcis2/           # 核心模块
│   ├── modules/           # 功能模块
│   └── hardware/          # 硬件接口
├── assets/                # 资源文件
│   ├── dxf/              # DXF设计文件
│   ├── images/           # 图像资源
│   └── archive/          # 归档数据
├── Data/                  # 数据文件
│   ├── H00001/           # 孔位H00001数据
│   ├── H00002/           # 孔位H00002数据
│   ├── cache/            # 缓存文件
│   └── detection_system.db # 检测系统数据库
├── docs/                  # 文档
│   ├── reports/          # 项目报告
│   ├── PySide6_Context/  # PySide6开发文档
│   └── *.md              # 各种说明文档
├── tests/                 # 测试文件
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── system/           # 系统测试
├── scripts/               # 脚本文件
│   ├── debug/            # 调试脚本
│   ├── tests/            # 测试脚本
│   ├── utilities/        # 实用工具
│   └── verification/     # 验证脚本
├── tools/                 # 工具和实用程序
│   ├── git_lfs/          # Git LFS相关工具
│   ├── testing/          # 测试工具
│   ├── merge/            # 合并相关工具
│   └── reference/        # 参考资料
└── config/                # 配置文件
```

## 功能特性

### 🎯 核心功能
- **DXF文件加载**: 支持管板设计图的加载和可视化
- **实时监控**: 光谱共焦传感器数据实时显示
- **内窥镜集成**: 实时图像显示和分析
- **历史数据分析**: 支持CSV数据导入和拟合圆算法
- **缺陷标注**: YOLO格式的缺陷标注和COCO导出

### 📊 界面层级
1. **一级界面**: 主检测视图，DXF加载，孔位管理
2. **二级界面**: 实时监控，数据图表，异常检测
3. **三级界面**: 历史数据查看，缺陷标注工具

### 🔍 检测功能
- 48个检测点状态管理
- 孔位搜索和导航
- 检测进度跟踪
- 异常数据监控
- 统计分析和报告

## 快速开始

### 环境要求
- Python 3.8+
- PySide6
- Git LFS
- Windows 10/11

### 安装步骤

1. **克隆仓库**：
   ```bash
   git clone https://github.com/your-username/AIDCIS2-AIDCIS3.git
   cd AIDCIS2-AIDCIS3
   ```

2. **安装Git LFS并拉取大文件**：
   ```bash
   git lfs install
   git lfs pull
   ```

3. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

4. **运行程序**：
   ```bash
   python src/main.py
   ```

### 开发环境设置
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/

# 运行特定测试
python scripts/tests/test_all_functions.py
```

## Git LFS使用

本项目使用Git LFS管理大文件，包括：
- 📐 DXF设计文件 (assets/dxf/)
- 📊 CSV测量数据 (Data/)
- 🖼️ 图像和视频文件
- 🗄️ 数据库文件

### 团队协作
团队成员请确保：
1. 安装Git LFS: https://git-lfs.github.io/
2. 克隆后执行: `git lfs pull`
3. 使用提供的工具脚本: `tools/git_lfs/`

## 开发指南

### 代码结构
- `src/main.py`: 程序入口点
- `src/main_window.py`: 主窗口实现
- `src/aidcis2/`: 核心业务逻辑
- `src/modules/`: 功能模块
- `src/hardware/`: 硬件接口

### 测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/
```

### 调试
使用 `scripts/debug/` 目录下的调试脚本：
- `debug_dxf_display.py`: DXF显示问题调试
- `debug_annotation_detection.py`: 标注检测调试
- `diagnose_ui_issues.py`: UI问题诊断

## 文档

详细文档位于 `docs/` 目录：
- [安装运行指南](docs/安装运行指南.md)
- [完整功能使用说明](docs/完整功能使用说明.md)
- [技术实现指南](docs/Technical_Implementation_Guide.md)
- [Git LFS协同工作指南](docs/Git_LFS_协同工作指南.md)

## 工具和脚本

### Git LFS工具 (`tools/git_lfs/`)
- `setup_lfs_en.bat`: LFS初始化脚本
- `team_member_setup.ps1`: 团队成员设置
- `verify_lfs.bat`: LFS状态验证

### 测试工具 (`tools/testing/`)
- `quick_test_ui.py`: 快速UI测试
- `test_realtime_ui_modifications.py`: 实时界面测试

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: [维护者信息]
- 问题反馈: [GitHub Issues](https://github.com/your-username/AIDCIS2-AIDCIS3/issues)
- 技术支持: [技术支持邮箱]

## 更新日志

### v1.0.0 (2025-07-10)
- ✅ 项目结构重组和优化
- ✅ Git LFS配置和大文件管理
- ✅ 实时监控界面优化
- ✅ 完整的文档和工具集
- ✅ 团队协作流程建立

---

**注意**: 本项目使用Git LFS管理大文件，首次克隆后请确保执行 `git lfs pull` 下载所有大文件。
