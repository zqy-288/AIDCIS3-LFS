# GitHub上传数据文件指南

## 问题描述
在上传代码到GitHub时，`.gitignore` 文件将DXF和CSV文件排除了，导致重要的测试数据无法正常上传。

## 解决方案

### 方案1：使用提供的脚本（推荐）

#### Windows PowerShell
```powershell
.\upload_data_files.ps1
```

#### Windows 批处理
```cmd
upload_data_files.bat
```

### 方案2：手动操作

#### 1. 修改 .gitignore 文件
已经修改了 `.gitignore` 文件，主要更改：
- 将 `measurement_data_*.csv` 改为 `cache/measurement_data_*.csv`
- 添加了明确的允许规则：
  ```
  # 允许重要的项目文件
  !Data/
  !Data/**/*.csv
  !"DXF Graph"/
  !"DXF Graph"/*.dxf
  ```

#### 2. 强制添加重要文件
```bash
# 添加CSV数据文件
git add -f "Data/H00001/CCIDM/measurement_data_Fri_Jul__4_18_40_29_2025.csv"
git add -f "Data/H00002/CCIDM/measurement_data_Sat_Jul__5_15_18_46_2025.csv"

# 添加小的DXF测试文件
git add -f "DXF Graph/测试管板.dxf"

# 添加整个Data目录结构
git add -f "Data/"
```

#### 3. 提交和推送
```bash
git commit -m "添加重要的数据文件：CSV测量数据和DXF测试文件"
git push origin main
```

## 文件说明

### 包含的重要文件
- `Data/H00001/CCIDM/measurement_data_Fri_Jul__4_18_40_29_2025.csv` - H00001孔位的测量数据
- `Data/H00002/CCIDM/measurement_data_Sat_Jul__5_15_18_46_2025.csv` - H00002孔位的测量数据  
- `DXF Graph/测试管板.dxf` - 测试用的DXF文件（较小）

### 排除的文件
- `DXF Graph/东重管板.dxf` - 大型DXF文件（文件过大，保留在本地）
- `cache/measurement_data_*.csv` - 临时缓存文件
- `detection_system.db` - 数据库文件
- 各种编译文件和缓存文件

## 大文件处理建议

如果需要上传大文件（如东重管板.dxf），建议使用Git LFS：

### 安装Git LFS
```bash
git lfs install
```

### 跟踪大文件
```bash
git lfs track "*.dxf"
git lfs track "DXF Graph/东重管板.dxf"
```

### 添加和提交
```bash
git add .gitattributes
git add "DXF Graph/东重管板.dxf"
git commit -m "添加大型DXF文件使用Git LFS"
git push origin main
```

## 验证上传结果

### 检查文件状态
```bash
git status
git ls-files | grep -E "\.(csv|dxf)$"
```

### 检查忽略的文件
```bash
git ls-files --others --ignored --exclude-standard
```

## 注意事项

1. **文件大小限制**：GitHub单个文件限制100MB，仓库总大小建议不超过1GB
2. **敏感数据**：确保不包含敏感信息（密码、密钥等）
3. **文件编码**：确保CSV文件使用UTF-8编码，避免中文乱码
4. **路径问题**：Windows路径包含空格的需要用引号包围

## 常见问题

### Q: 文件仍然被忽略怎么办？
A: 使用 `git add -f` 强制添加，或检查 `.gitignore` 规则

### Q: 推送时提示文件过大？
A: 使用Git LFS处理大文件，或将大文件移到云存储

### Q: 中文文件名显示乱码？
A: 设置Git配置：`git config core.quotepath false`

## 完成后的目录结构

```
AIDCIS2-AIDCIS3/
├── Data/
│   ├── H00001/
│   │   └── CCIDM/
│   │       └── measurement_data_Fri_Jul__4_18_40_29_2025.csv ✅
│   └── H00002/
│       └── CCIDM/
│           └── measurement_data_Sat_Jul__5_15_18_46_2025.csv ✅
├── DXF Graph/
│   ├── 测试管板.dxf ✅
│   └── 东重管板.dxf ❌ (太大，本地保留)
└── cache/
    └── measurement_data_*.csv ❌ (临时文件，忽略)
```

现在您的重要数据文件应该可以正常上传到GitHub了！
