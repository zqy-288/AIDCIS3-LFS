# Git LFS 项目配置脚本
# 为AIDCIS2-AIDCIS3项目配置Git LFS

Write-Host "开始配置Git LFS..." -ForegroundColor Green

# 1. 检查Git LFS是否已安装
Write-Host "检查Git LFS安装状态..." -ForegroundColor Yellow
try {
    $lfsVersion = git lfs version
    Write-Host "✅ Git LFS已安装: $lfsVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git LFS未安装，请先安装Git LFS" -ForegroundColor Red
    Write-Host "下载地址: https://git-lfs.github.io/" -ForegroundColor Cyan
    exit 1
}

# 2. 初始化Git LFS
Write-Host "初始化Git LFS..." -ForegroundColor Yellow
git lfs install

# 3. 配置跟踪规则
Write-Host "配置文件跟踪规则..." -ForegroundColor Yellow

# DXF文件（设计图纸）
git lfs track "*.dxf"
git lfs track "DXF Graph/*.dxf"

# 大型CSV数据文件
git lfs track "Data/**/*.csv"

# 数据库文件
git lfs track "*.db"
git lfs track "*.sqlite"
git lfs track "*.sqlite3"

# 图像文件
git lfs track "*.png"
git lfs track "*.jpg"
git lfs track "*.jpeg"
git lfs track "*.bmp"
git lfs track "*.tiff"
git lfs track "*.tif"

# 视频文件
git lfs track "*.mp4"
git lfs track "*.avi"
git lfs track "*.mov"
git lfs track "*.mkv"

# 压缩文件
git lfs track "*.zip"
git lfs track "*.rar"
git lfs track "*.7z"

# 其他大文件
git lfs track "*.bin"
git lfs track "*.exe"
git lfs track "*.msi"

# 4. 显示当前跟踪规则
Write-Host "当前LFS跟踪规则:" -ForegroundColor Cyan
git lfs track

# 5. 添加.gitattributes文件
Write-Host "添加.gitattributes文件到Git..." -ForegroundColor Yellow
git add .gitattributes

# 6. 检查现有大文件
Write-Host "检查现有大文件..." -ForegroundColor Yellow
$largeFiles = @()

# 检查DXF文件
if (Test-Path "DXF Graph") {
    $dxfFiles = Get-ChildItem "DXF Graph" -Filter "*.dxf" -Recurse
    foreach ($file in $dxfFiles) {
        $sizeKB = [math]::Round($file.Length / 1KB, 2)
        Write-Host "  📐 $($file.Name): ${sizeKB}KB" -ForegroundColor White
        $largeFiles += $file.FullName
    }
}

# 检查数据库文件
$dbFiles = Get-ChildItem . -Filter "*.db" -Recurse
foreach ($file in $dbFiles) {
    $sizeKB = [math]::Round($file.Length / 1KB, 2)
    Write-Host "  🗄️ $($file.Name): ${sizeKB}KB" -ForegroundColor White
    $largeFiles += $file.FullName
}

# 检查大型CSV文件（>1MB）
if (Test-Path "Data") {
    $csvFiles = Get-ChildItem "Data" -Filter "*.csv" -Recurse | Where-Object { $_.Length -gt 1MB }
    foreach ($file in $csvFiles) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Host "  📊 $($file.Name): ${sizeMB}MB" -ForegroundColor White
        $largeFiles += $file.FullName
    }
}

# 7. 添加大文件到LFS
if ($largeFiles.Count -gt 0) {
    Write-Host "添加大文件到Git LFS..." -ForegroundColor Yellow
    foreach ($file in $largeFiles) {
        $relativePath = Resolve-Path $file -Relative
        Write-Host "  添加: $relativePath" -ForegroundColor Gray
        git add $relativePath
    }
} else {
    Write-Host "没有发现需要LFS管理的大文件" -ForegroundColor Green
}

# 8. 提交LFS配置
Write-Host "提交LFS配置..." -ForegroundColor Yellow
git commit -m "配置Git LFS支持大文件管理

- 添加.gitattributes配置文件
- 跟踪DXF、CSV、数据库等大文件类型
- 迁移现有大文件到LFS管理
- 优化仓库大小和克隆速度"

# 9. 显示LFS状态
Write-Host "Git LFS状态:" -ForegroundColor Cyan
git lfs ls-files

# 10. 性能优化配置
Write-Host "配置性能优化..." -ForegroundColor Yellow
git config lfs.concurrenttransfers 8
git config lfs.cachelimit 5G

Write-Host "✅ Git LFS配置完成！" -ForegroundColor Green

Write-Host "`n📋 下一步操作:" -ForegroundColor Magenta
Write-Host "1. 推送到远程仓库: git push origin main" -ForegroundColor White
Write-Host "2. 通知团队成员安装Git LFS" -ForegroundColor White
Write-Host "3. 团队成员重新克隆仓库或执行: git lfs pull" -ForegroundColor White

Write-Host "`n👥 团队成员操作指南:" -ForegroundColor Magenta
Write-Host "1. 安装Git LFS: https://git-lfs.github.io/" -ForegroundColor White
Write-Host "2. 克隆仓库: git clone <仓库地址>" -ForegroundColor White
Write-Host "3. 如果已有本地仓库: git lfs pull" -ForegroundColor White

Write-Host "`n⚠️ 注意事项:" -ForegroundColor Red
Write-Host "- GitHub免费账户LFS限额: 1GB存储 + 1GB/月带宽" -ForegroundColor White
Write-Host "- 大文件修改会产生新版本，注意存储使用量" -ForegroundColor White
Write-Host "- 团队所有成员都需要安装Git LFS" -ForegroundColor White
