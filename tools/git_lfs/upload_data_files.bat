@echo off
echo 开始上传重要的数据文件到GitHub...

echo.
echo 添加CSV数据文件...
git add -f "Data/H00001/CCIDM/measurement_data_Fri_Jul__4_18_40_29_2025.csv"
git add -f "Data/H00002/CCIDM/measurement_data_Sat_Jul__5_15_18_46_2025.csv"

echo.
echo 添加DXF测试文件...
git add -f "DXF Graph/测试管板.dxf"

echo.
echo 添加Data目录结构...
git add -f "Data/"

echo.
echo 检查Git状态...
git status

echo.
echo 提交更改...
git commit -m "添加重要的数据文件：CSV测量数据和DXF测试文件

- 添加H00001和H00002的CSV测量数据
- 添加测试管板.dxf文件  
- 更新.gitignore以正确处理数据文件
- 保留大文件东重管板.dxf在本地（因为文件过大）"

echo.
echo 完成！现在可以推送到GitHub了：
echo git push origin main

echo.
echo 注意事项：
echo 1. 东重管板.dxf文件较大，已在.gitignore中排除
echo 2. 如果需要上传大文件，建议使用Git LFS
echo 3. cache目录下的临时文件不会被上传

pause
