# PowerShell脚本：上传重要的数据文件到GitHub
# 解决.gitignore忽略DXF和CSV文件的问题

Write-Host "开始上传重要的数据文件到GitHub..." -ForegroundColor Green

# 1. 强制添加重要的CSV数据文件
Write-Host "添加CSV数据文件..." -ForegroundColor Yellow
git add -f "Data/H00001/CCIDM/measurement_data_Fri_Jul__4_18_40_29_2025.csv"
git add -f "Data/H00002/CCIDM/measurement_data_Sat_Jul__5_15_18_46_2025.csv"

# 2. 强制添加小的DXF测试文件（跳过大文件）
Write-Host "添加DXF测试文件..." -ForegroundColor Yellow
git add -f "DXF Graph/测试管板.dxf"

# 3. 添加整个Data目录结构（但排除大文件）
Write-Host "添加Data目录结构..." -ForegroundColor Yellow
git add -f "Data/"

# 4. 检查当前状态
Write-Host "检查Git状态..." -ForegroundColor Yellow
git status

# 5. 提交更改
Write-Host "提交更改..." -ForegroundColor Yellow
git commit -m "添加重要的数据文件：CSV测量数据和DXF测试文件

- 添加H00001和H00002的CSV测量数据
- 添加测试管板.dxf文件
- 更新.gitignore以正确处理数据文件
- 保留大文件东重管板.dxf在本地（因为文件过大）"

Write-Host "完成！现在可以推送到GitHub了：" -ForegroundColor Green
Write-Host "git push origin main" -ForegroundColor Cyan

Write-Host "`n注意事项：" -ForegroundColor Magenta
Write-Host "1. 东重管板.dxf文件较大，已在.gitignore中排除" -ForegroundColor White
Write-Host "2. 如果需要上传大文件，建议使用Git LFS" -ForegroundColor White
Write-Host "3. cache目录下的临时文件不会被上传" -ForegroundColor White
