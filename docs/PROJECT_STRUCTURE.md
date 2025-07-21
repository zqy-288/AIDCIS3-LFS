# 项目结构说明

## 核心目录结构

```
AIDCIS2-AIDCIS3/
├── src/                    # 源代码目录
│   ├── main.py            # 主程序入口
│   ├── main_window.py     # 主窗口
│   ├── modules/           # 功能模块
│   └── hardware/          # 硬件接口
├── Data/                  # 数据文件目录
│   ├── H00001/           # 孔位数据
│   ├── H00002/           # 孔位数据
│   └── H00003/           # 孔位数据
├── docs/                  # 文档目录
├── tests/                 # 测试目录
├── assets/               # 资源文件
├── requirements.txt      # Python依赖
└── README.md            # 项目说明
```

## 目录说明

### src/ - 源代码目录
- `main.py`: 应用程序主入口
- `main_window.py`: 主窗口界面
- `modules/`: 各功能模块
  - `history_viewer.py`: 历史数据查看器
  - `unified_history_viewer.py`: 统一历史数据查看器
  - 其他功能模块...

### Data/ - 数据目录
- 存放测量数据CSV文件
- 按孔位ID组织（H00001, H00002, H00003等）
- 包含数据库文件

### docs/ - 文档目录
- 技术文档
- 使用说明
- 开发指南

### tests/ - 测试目录
- 单元测试
- 集成测试
- 系统测试

### assets/ - 资源目录
- DXF文件
- 图片资源
- 其他静态资源

## 文件清理说明

已清理的临时文件类型：
1. 根目录下的测试脚本（test_*.py, verify_*.py等）
2. 调试脚本（debug_*.py, demo_*.py等）
3. 上传和部署脚本（*.bat, *.ps1等）
4. 临时生成的CSV文件
5. Python缓存文件（__pycache__）

这些文件已移动到 `temp_removed_files/` 目录中，如需恢复可从该目录找回。
