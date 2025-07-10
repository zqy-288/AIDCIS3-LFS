# 手动GitHub设置指南

## 当前状态
✅ 项目已整理完成  
✅ Git LFS已配置  
✅ 所有文件已提交到本地Git  
⏳ 需要推送到GitHub  

## 步骤1：创建GitHub仓库

1. 访问 https://github.com
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `AIDCIS2-AIDCIS3`
   - **Description**: `管孔检测系统上位机软件`
   - **Visibility**: 选择 Public 或 Private
   - **⚠️ 重要**: 不要勾选 "Add a README file"（我们已经有了）
   - **⚠️ 重要**: 不要勾选 "Add .gitignore"（我们已经有了）
4. 点击 "Create repository"

## 步骤2：获取仓库URL

创建完成后，GitHub会显示一个页面，包含仓库URL，类似：
```
https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git
```
复制这个URL。

## 步骤3：连接本地仓库到GitHub

打开PowerShell或命令提示符，在项目目录中执行：

```bash
# 添加远程仓库（替换YOUR-USERNAME为您的GitHub用户名）
git remote add origin https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git

# 推送到GitHub
git push -u origin main
```

## 步骤4：处理可能的认证问题

如果推送时要求认证，您有几个选择：

### 选项A：使用Personal Access Token（推荐）
1. 访问 GitHub Settings > Developer settings > Personal access tokens
2. 生成新的token，勾选 "repo" 权限
3. 使用token作为密码进行认证

### 选项B：使用GitHub Desktop
1. 下载并安装 GitHub Desktop
2. 登录您的GitHub账户
3. 在GitHub Desktop中打开您的本地仓库
4. 点击 "Publish repository"

### 选项C：使用SSH密钥
1. 生成SSH密钥：`ssh-keygen -t rsa -b 4096 -C "your.email@example.com"`
2. 将公钥添加到GitHub账户
3. 使用SSH URL：`git@github.com:YOUR-USERNAME/AIDCIS2-AIDCIS3.git`

## 快速命令参考

```bash
# 检查当前状态
git status

# 检查远程仓库
git remote -v

# 添加远程仓库
git remote add origin https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git

# 推送到GitHub
git push -u origin main

# 检查LFS文件
git lfs ls-files

# 如果需要重新设置远程URL
git remote set-url origin https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git
```

## 验证成功

推送成功后，您应该能在GitHub上看到：
- ✅ 所有源代码文件
- ✅ 完整的目录结构
- ✅ README.md显示项目说明
- ✅ Git LFS文件正确显示

## 团队协作

推送成功后，团队成员可以：

1. **克隆仓库**：
   ```bash
   git clone https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git
   ```

2. **安装Git LFS**：
   - 访问 https://git-lfs.github.io/
   - 下载并安装

3. **拉取LFS文件**：
   ```bash
   git lfs pull
   ```

4. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

5. **运行程序**：
   ```bash
   python src/main.py
   ```

## 故障排除

### 问题1：推送被拒绝
```bash
git pull origin main --allow-unrelated-histories
git push origin main
```

### 问题2：LFS文件太大
- 检查GitHub LFS配额（免费账户1GB）
- 考虑移除一些大文件或使用付费账户

### 问题3：认证失败
- 使用Personal Access Token
- 或使用GitHub Desktop
- 或配置SSH密钥

## 需要帮助？

如果遇到问题，可以：
1. 运行 PowerShell 脚本：`powershell -ExecutionPolicy Bypass -File github_setup.ps1`
2. 查看Git错误信息
3. 检查GitHub仓库设置
4. 验证网络连接
