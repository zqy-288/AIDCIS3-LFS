# Git LFS 协同工作完整指南

## 什么是 Git LFS

Git LFS (Large File Storage) 是 Git 的扩展，专门用于处理大文件。它将大文件存储在单独的服务器上，在 Git 仓库中只保存指针文件。

### 优势
- 🚀 加快克隆和拉取速度
- 💾 减少仓库大小
- 🔄 支持版本控制大文件
- 👥 团队协作友好

## 第一步：安装和初始化

### 1.1 安装 Git LFS

#### Windows
```bash
# 方法1：使用 Git for Windows（推荐）
# Git LFS 通常已包含在 Git for Windows 中

# 方法2：单独下载
# 从 https://git-lfs.github.io/ 下载安装

# 方法3：使用包管理器
winget install Git.Git-LFS
# 或
choco install git-lfs
```

#### macOS
```bash
brew install git-lfs
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt install git-lfs

# CentOS/RHEL
sudo yum install git-lfs
```

### 1.2 验证安装
```bash
git lfs version
# 应该显示版本信息，如：git-lfs/3.4.0
```

### 1.3 初始化 LFS（仓库管理员操作）
```bash
# 在项目根目录执行
git lfs install
```

## 第二步：配置要跟踪的文件类型

### 2.1 设置跟踪规则（仓库管理员操作）
```bash
# 跟踪所有 DXF 文件
git lfs track "*.dxf"

# 跟踪特定目录下的大文件
git lfs track "DXF Graph/*.dxf"

# 跟踪大型 CSV 文件（超过10MB的）
git lfs track "Data/**/*.csv"

# 跟踪数据库文件
git lfs track "*.db"
git lfs track "*.sqlite"

# 跟踪图像文件
git lfs track "*.png"
git lfs track "*.jpg"
git lfs track "*.jpeg"

# 跟踪视频文件
git lfs track "*.mp4"
git lfs track "*.avi"

# 查看当前跟踪的文件类型
git lfs track
```

### 2.2 检查生成的 .gitattributes 文件
```bash
cat .gitattributes
```

应该看到类似内容：
```
*.dxf filter=lfs diff=lfs merge=lfs -text
DXF Graph/*.dxf filter=lfs diff=lfs merge=lfs -text
Data/**/*.csv filter=lfs diff=lfs merge=lfs -text
*.db filter=lfs diff=lfs merge=lfs -text
```

## 第三步：添加和提交大文件

### 3.1 添加 .gitattributes 文件
```bash
git add .gitattributes
git commit -m "配置Git LFS跟踪规则"
```

### 3.2 添加大文件
```bash
# 添加大型DXF文件
git add "DXF Graph/东重管板.dxf"

# 添加其他大文件
git add "Data/"

# 提交
git commit -m "使用Git LFS添加大型数据文件"
```

### 3.3 推送到远程仓库
```bash
git push origin main
```

## 第四步：团队成员协同工作流程

### 4.1 新团队成员加入项目

#### 步骤1：安装Git LFS
```bash
# 按照第一步的安装指南安装Git LFS
git lfs version  # 验证安装
```

#### 步骤2：克隆项目
```bash
# 克隆仓库（会自动下载LFS文件）
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 如果克隆时没有自动下载LFS文件，手动拉取
git lfs pull
```

#### 步骤3：验证LFS设置
```bash
# 检查LFS跟踪状态
git lfs track

# 检查LFS文件状态
git lfs ls-files

# 验证大文件是否正确下载
ls -la "DXF Graph/"
```

### 4.2 日常协作工作流

#### 拉取最新更改
```bash
# 拉取代码和LFS文件
git pull origin main

# 如果只想拉取LFS文件
git lfs pull
```

#### 添加新的大文件
```bash
# 添加新文件（如果匹配LFS规则会自动使用LFS）
git add "新的大文件.dxf"
git commit -m "添加新的设计文件"
git push origin main
```

#### 修改现有大文件
```bash
# 修改大文件后正常提交
git add "DXF Graph/东重管板.dxf"
git commit -m "更新管板设计"
git push origin main
```

## 第五步：高级协作功能

### 5.1 选择性下载（节省带宽）
```bash
# 克隆时不下载LFS文件
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/your-username/your-repo.git

# 只下载特定文件
git lfs pull --include="*.dxf"
git lfs pull --include="DXF Graph/*"

# 排除某些文件
git lfs pull --exclude="*.mp4"
```

### 5.2 检查LFS使用情况
```bash
# 查看LFS文件列表
git lfs ls-files

# 查看LFS存储使用情况
git lfs env

# 查看LFS文件的历史
git lfs logs last
```

### 5.3 分支协作
```bash
# 创建新分支
git checkout -b feature/new-design

# 添加大文件到分支
git add "新设计.dxf"
git commit -m "添加新设计方案"
git push origin feature/new-design

# 合并时LFS文件会自动处理
git checkout main
git merge feature/new-design
```

## 第六步：故障排除

### 6.1 常见问题

#### 问题1：LFS文件显示为指针文件
```bash
# 症状：文件内容显示类似
# version https://git-lfs.github.com/spec/v1
# oid sha256:abc123...
# size 12345

# 解决方案：
git lfs pull
```

#### 问题2：推送失败
```bash
# 检查LFS配置
git lfs env

# 重新推送LFS文件
git lfs push origin main --all
```

#### 问题3：文件没有使用LFS
```bash
# 检查文件是否匹配跟踪规则
git lfs track

# 手动迁移现有文件到LFS
git lfs migrate import --include="*.dxf"
```

### 6.2 清理和维护
```bash
# 清理本地LFS缓存
git lfs prune

# 检查仓库完整性
git lfs fsck

# 查看LFS存储统计
git lfs env
```

## 第七步：最佳实践

### 7.1 文件组织建议
```
项目根目录/
├── .gitattributes          # LFS配置文件
├── 源代码/                  # 普通Git管理
├── DXF Graph/              # 大型设计文件（LFS）
├── Data/                   # 测量数据（LFS）
├── Assets/                 # 图片、视频（LFS）
└── docs/                   # 文档（普通Git）
```

### 7.2 团队协作规范

1. **统一LFS配置**：确保所有团队成员使用相同的.gitattributes
2. **定期同步**：每天开始工作前执行`git lfs pull`
3. **文件命名**：使用有意义的文件名，避免中文和特殊字符
4. **版本说明**：大文件更新时写清楚变更说明
5. **存储管理**：定期清理不需要的LFS文件版本

### 7.3 性能优化
```bash
# 设置并发下载数
git config lfs.concurrenttransfers 8

# 设置LFS缓存大小（GB）
git config lfs.cachelimit 10G

# 启用增量下载
git config lfs.standalonetransferagent true
```

## 第八步：GitHub/GitLab配置

### GitHub
- 免费账户：1GB LFS存储，1GB/月带宽
- 付费账户：可购买额外存储和带宽
- 企业账户：更大的配额

### GitLab
- 免费账户：10GB LFS存储
- 付费账户：更大配额

### 自建Git服务器
可以配置自己的LFS服务器，完全控制存储。

现在您的团队就可以高效地协作处理大文件了！
