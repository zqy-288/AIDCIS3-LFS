# 团队成员Git LFS快速设置脚本
# 用于新加入项目的团队成员

Write-Host "团队成员Git LFS设置向导" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# 1. 检查Git LFS安装
Write-Host "`n步骤1: 检查Git LFS安装状态..." -ForegroundColor Yellow
try {
    $lfsVersion = git lfs version
    Write-Host "✅ Git LFS已安装: $lfsVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git LFS未安装" -ForegroundColor Red
    Write-Host "请按以下步骤安装:" -ForegroundColor Cyan
    Write-Host "1. 访问: https://git-lfs.github.io/" -ForegroundColor White
    Write-Host "2. 下载并安装Git LFS" -ForegroundColor White
    Write-Host "3. 重新运行此脚本" -ForegroundColor White
    
    $install = Read-Host "是否要自动安装Git LFS? (y/n)"
    if ($install -eq "y" -or $install -eq "Y") {
        Write-Host "尝试使用winget安装..." -ForegroundColor Yellow
        try {
            winget install Git.Git-LFS
            Write-Host "✅ Git LFS安装完成" -ForegroundColor Green
        } catch {
            Write-Host "❌ 自动安装失败，请手动安装" -ForegroundColor Red
            exit 1
        }
    } else {
        exit 1
    }
}

# 2. 检查是否在Git仓库中
Write-Host "`n步骤2: 检查Git仓库状态..." -ForegroundColor Yellow
try {
    $gitStatus = git status
    Write-Host "✅ 当前在Git仓库中" -ForegroundColor Green
} catch {
    Write-Host "❌ 当前不在Git仓库中" -ForegroundColor Red
    Write-Host "请先克隆项目仓库或进入项目目录" -ForegroundColor White
    exit 1
}

# 3. 初始化Git LFS
Write-Host "`n步骤3: 初始化Git LFS..." -ForegroundColor Yellow
git lfs install
Write-Host "✅ Git LFS初始化完成" -ForegroundColor Green

# 4. 检查LFS跟踪规则
Write-Host "`n步骤4: 检查LFS跟踪规则..." -ForegroundColor Yellow
if (Test-Path ".gitattributes") {
    Write-Host "✅ 发现.gitattributes文件" -ForegroundColor Green
    Write-Host "当前LFS跟踪规则:" -ForegroundColor Cyan
    git lfs track
} else {
    Write-Host "⚠️ 未发现.gitattributes文件" -ForegroundColor Yellow
    Write-Host "可能需要从远程仓库拉取最新配置" -ForegroundColor White
}

# 5. 拉取LFS文件
Write-Host "`n步骤5: 拉取LFS文件..." -ForegroundColor Yellow
Write-Host "这可能需要一些时间，取决于文件大小..." -ForegroundColor Gray

try {
    git lfs pull
    Write-Host "✅ LFS文件拉取完成" -ForegroundColor Green
} catch {
    Write-Host "⚠️ LFS文件拉取可能有问题" -ForegroundColor Yellow
    Write-Host "请检查网络连接和仓库权限" -ForegroundColor White
}

# 6. 验证LFS文件
Write-Host "`n步骤6: 验证LFS文件..." -ForegroundColor Yellow
$lfsFiles = git lfs ls-files
if ($lfsFiles) {
    Write-Host "✅ 发现以下LFS文件:" -ForegroundColor Green
    $lfsFiles | ForEach-Object { Write-Host "  📁 $_" -ForegroundColor White }
} else {
    Write-Host "ℹ️ 当前没有LFS文件" -ForegroundColor Blue
}

# 7. 检查大文件状态
Write-Host "`n步骤7: 检查重要文件状态..." -ForegroundColor Yellow

# 检查DXF文件
if (Test-Path "DXF Graph") {
    $dxfFiles = Get-ChildItem "DXF Graph" -Filter "*.dxf"
    foreach ($file in $dxfFiles) {
        if ($file.Length -gt 1KB) {
            $sizeKB = [math]::Round($file.Length / 1KB, 2)
            Write-Host "  📐 $($file.Name): ${sizeKB}KB ✅" -ForegroundColor Green
        } else {
            Write-Host "  📐 $($file.Name): 可能是LFS指针文件 ⚠️" -ForegroundColor Yellow
        }
    }
}

# 检查数据文件
if (Test-Path "Data") {
    $csvFiles = Get-ChildItem "Data" -Filter "*.csv" -Recurse
    $csvCount = $csvFiles.Count
    if ($csvCount -gt 0) {
        Write-Host "  📊 发现 $csvCount 个CSV数据文件 ✅" -ForegroundColor Green
    }
}

# 8. 性能优化配置
Write-Host "`n步骤8: 配置性能优化..." -ForegroundColor Yellow
git config lfs.concurrenttransfers 8
git config lfs.cachelimit 5G
Write-Host "✅ 性能配置完成" -ForegroundColor Green

# 9. 显示使用指南
Write-Host "`n🎉 设置完成！" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

Write-Host "`n📋 日常使用指南:" -ForegroundColor Magenta
Write-Host "1. 拉取最新更改: git pull" -ForegroundColor White
Write-Host "2. 拉取LFS文件: git lfs pull" -ForegroundColor White
Write-Host "3. 添加大文件: git add <文件名> (自动使用LFS)" -ForegroundColor White
Write-Host "4. 提交更改: git commit -m '描述'" -ForegroundColor White
Write-Host "5. 推送更改: git push" -ForegroundColor White

Write-Host "`n🔧 常用LFS命令:" -ForegroundColor Magenta
Write-Host "- 查看LFS文件: git lfs ls-files" -ForegroundColor White
Write-Host "- 查看LFS状态: git lfs status" -ForegroundColor White
Write-Host "- 查看跟踪规则: git lfs track" -ForegroundColor White
Write-Host "- 清理LFS缓存: git lfs prune" -ForegroundColor White

Write-Host "`n⚠️ 注意事项:" -ForegroundColor Red
Write-Host "- 每次开始工作前执行: git lfs pull" -ForegroundColor White
Write-Host "- 大文件修改后正常提交即可" -ForegroundColor White
Write-Host "- 如果文件显示为指针，执行: git lfs pull" -ForegroundColor White
Write-Host "- 遇到问题请联系项目管理员" -ForegroundColor White

Write-Host "`n✨ 现在您可以开始协作开发了！" -ForegroundColor Green
