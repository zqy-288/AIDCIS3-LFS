# 团队成员快速上手指南

## 🚀 欢迎加入AIDCIS3项目团队！

这份指南将帮助您快速设置开发环境并开始协作。

## 📋 前置要求

### 必需软件
- [ ] **Git**: https://git-scm.com/
- [ ] **Git LFS**: https://git-lfs.github.io/
- [ ] **Python 3.8+**: https://python.org/
- [ ] **代码编辑器**: VS Code, PyCharm等

### GitHub账户
- [ ] 拥有GitHub账户
- [ ] 已接受仓库邀请

## 🔧 环境设置

### 1. 安装Git LFS
```bash
# Windows (使用Git for Windows)
# Git LFS通常已包含在Git for Windows中

# 验证安装
git lfs version
```

### 2. 克隆项目
```bash
# 克隆仓库
git clone https://github.com/zqy-288/AIDCIS3-LFS.git
cd AIDCIS3-LFS

# 拉取LFS文件
git lfs pull
```

### 3. 设置Python环境
```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 验证设置
```bash
# 检查LFS文件
git lfs ls-files

# 运行程序
python src/main.py
```

## 📁 项目结构

```
AIDCIS3-LFS/
├── src/                    # 源代码
│   ├── main.py            # 程序入口
│   ├── main_window.py     # 主窗口
│   ├── aidcis2/           # 核心模块
│   ├── modules/           # 功能模块
│   └── hardware/          # 硬件接口
├── assets/                # 资源文件
│   ├── dxf/              # DXF设计文件
│   └── archive/          # 归档数据
├── Data/                  # 数据文件
│   ├── H00001/           # 孔位数据
│   └── H00002/           # 孔位数据
├── docs/                  # 文档
├── tools/                 # 工具和脚本
└── README.md             # 项目说明
```

## 🔄 日常工作流程

### 开始工作前
```bash
# 拉取最新代码
git pull origin main

# 拉取最新LFS文件
git lfs pull
```

### 开发过程中
```bash
# 创建功能分支
git checkout -b feature/your-feature-name

# 进行开发...

# 添加更改
git add .

# 提交更改
git commit -m "描述您的更改"

# 推送分支
git push origin feature/your-feature-name
```

### 完成功能后
1. 在GitHub上创建Pull Request
2. 请求代码审查
3. 合并到main分支

## 🎯 开发规范

### 代码规范
- 使用Python PEP 8编码规范
- 添加适当的注释和文档字符串
- 编写单元测试

### 提交规范
```bash
# 提交信息格式
git commit -m "类型(范围): 简短描述

详细描述（可选）"

# 示例
git commit -m "feat(ui): 添加实时监控界面优化

- 增大字体大小提高可读性
- 优化面板布局和边框样式
- 修复标准直径显示问题"
```

### 分支命名
- `feature/功能名称` - 新功能
- `bugfix/问题描述` - 错误修复
- `hotfix/紧急修复` - 紧急修复
- `docs/文档更新` - 文档更新

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_specific.py

# 运行UI测试
python tools/testing/quick_test_ui.py
```

### 添加测试
- 为新功能编写单元测试
- 确保测试覆盖率
- 测试文件放在`tests/`目录

## 🔍 调试

### 调试工具
```bash
# 使用调试脚本
python scripts/debug/debug_dxf_display.py
python scripts/debug/debug_annotation_detection.py
```

### 常见问题
1. **LFS文件显示为指针**: 运行 `git lfs pull`
2. **依赖缺失**: 运行 `pip install -r requirements.txt`
3. **权限问题**: 检查GitHub仓库访问权限

## 📞 获取帮助

### 文档资源
- [项目README](README.md)
- [技术实现指南](docs/Technical_Implementation_Guide.md)
- [Git LFS协作指南](docs/Git_LFS_协同工作指南.md)

### 联系方式
- **项目维护者**: [维护者信息]
- **技术支持**: [技术支持联系方式]
- **问题反馈**: GitHub Issues

### 有用链接
- [GitHub仓库](https://github.com/zqy-288/AIDCIS3-LFS)
- [Git LFS文档](https://git-lfs.github.io/)
- [PySide6文档](https://doc.qt.io/qtforpython/)

## ✅ 检查清单

完成以下检查确保环境设置正确：

- [ ] Git和Git LFS已安装
- [ ] 项目已克隆到本地
- [ ] LFS文件已下载（检查DXF和图像文件）
- [ ] Python依赖已安装
- [ ] 程序可以正常运行
- [ ] 可以看到完整的项目结构
- [ ] 了解基本的Git工作流程

## 🎉 开始贡献

现在您已经准备好开始为AIDCIS3项目做贡献了！

记住：
- 经常拉取最新代码
- 遵循代码规范
- 编写清晰的提交信息
- 积极参与代码审查
- 有问题及时沟通

欢迎加入我们的团队！🚀
