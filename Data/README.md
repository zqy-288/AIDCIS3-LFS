# AIDCIS3 数据目录结构说明

> **文档版本**: v1.0  
> **创建时间**: 2025-01-13  
> **最后更新**: 2025-01-13  
> **维护者**: AIDCIS3 开发团队

## 概述

本目录用于存储AIDCIS3系统的所有产品数据和检测结果。采用分层架构设计，确保数据的有序管理和高效检索。

## 目录结构设计

### 理想架构 (推荐)

```
Data/
├── README.md                           # 本说明文档
├── .gitignore                          # Git忽略配置
└── Products/                           # 产品数据根目录
    └── [产品型号]/                     # 产品型号目录 (如: TP-001)
        ├── product_info.json           # 产品基本信息
        ├── dxf/                        # DXF文件存储
        │   ├── original.dxf            # 原始DXF文件
        │   └── processed.dxf           # 处理后的DXF文件
        └── Inspections/                # 检测记录目录
            └── [检测批次ID]/           # 检测批次 (如: 20250113_142530)
                ├── inspection_info.json   # 检测元信息
                ├── summary.json            # 检测汇总结果
                └── Holes/                  # 孔位检测结果
                    └── [孔位ID]/          # 孔位标识 (如: H00001)
                        ├── BISDM/          # 内窥镜展开图像
                        │   ├── panorama.png
                        │   └── result/
                        │       ├── 2-3.0.png
                        │       ├── 2-4.0.png
                        │       └── ...
                        └── CCIDM/          # 孔径检测数据
                            └── measurement_data.csv
```

### 当前兼容结构 (过渡期)

```
Data/
├── README.md                           # 本说明文档
├── H00001/                            # 遗留工件编号方式
│   ├── BISDM/                         # 内窥镜展开图像
│   │   └── result/
│   │       ├── 2-3.0.png
│   │       ├── 2-4.0.png
│   │       └── ...
│   └── CCIDM/                         # 孔径检测数据
│       └── measurement_data_*.csv
└── H00002/                            # 遗留工件编号方式
    ├── BISDM/
    └── CCIDM/
```

## 文件格式说明

### 产品信息文件 (product_info.json)

```json
{
  "product_id": "TP-001",
  "product_name": "标准管板10mm",
  "model_code": "TP001",
  "standard_diameter": 10.0,
  "tolerance_upper": 0.05,
  "tolerance_lower": -0.05,
  "sector_count": 4,
  "created_at": "2025-01-13T14:25:30Z",
  "description": "标准孔径10mm产品型号",
  "dxf_file_path": "./dxf/original.dxf"
}
```

### 检测信息文件 (inspection_info.json)

```json
{
  "batch_id": "20250113_142530",
  "product_id": "TP-001",
  "start_time": "2025-01-13T14:25:30Z",
  "end_time": "2025-01-13T15:30:45Z",
  "operator": "operator_001",
  "equipment_id": "AIDCIS3_001",
  "total_holes": 2521,
  "status": "completed"
}
```

### 检测汇总文件 (summary.json)

```json
{
  "batch_id": "20250113_142530",
  "total_holes": 2521,
  "completed_holes": 2521,
  "qualified_holes": 2485,
  "defective_holes": 36,
  "overall_progress": 100.0,
  "qualification_rate": 98.57,
  "sector_results": {
    "sector_1": {"total": 630, "qualified": 620, "defective": 10},
    "sector_2": {"total": 631, "qualified": 625, "defective": 6},
    "sector_3": {"total": 630, "qualified": 620, "defective": 10},
    "sector_4": {"total": 630, "qualified": 620, "defective": 10}
  },
  "updated_at": "2025-01-13T15:30:45Z"
}
```

## 数据类型说明

### BISDM (内窥镜展开图像)
- **文件类型**: PNG图像
- **命名规则**: `[序号]-[参数].png` (如: 2-3.0.png)
- **用途**: 存储孔位内表面的展开图像
- **特殊文件**: `panorama.png` - 全景图像

### CCIDM (孔径检测数据)
- **文件类型**: CSV数据文件
- **命名规则**: `measurement_data_[时间戳].csv`
- **内容**: 孔径测量数据、坐标信息、质量判定结果

## 文件命名规范

### 产品型号目录
- 格式: `[前缀]-[编号]` 或 `[自定义名称]`
- 示例: `TP-001`, `DZ-Standard-10mm`
- 避免使用特殊字符: `/ \ : * ? " < > |`

### 检测批次目录
- 格式: `YYYYMMDD_HHMMSS`
- 示例: `20250113_142530`
- 时区: 本地时间

### 孔位目录
- 格式: `H[5位数字]` 或 `[自定义编号]`
- 示例: `H00001`, `H02521`

## 数据管理策略

### 数据保留策略
- **产品数据**: 永久保留
- **检测记录**: 保留2年
- **临时文件**: 24小时后清理

### 备份策略
- **自动备份**: 每日增量备份
- **手动备份**: 检测完成后立即备份
- **异地备份**: 每周同步到备份服务器

### 数据迁移
- 系统会自动识别并兼容旧格式数据
- 建议逐步迁移到新的目录结构
- 迁移过程中原数据保持不变

## 系统集成

### 数据库关联
- 产品信息存储在SQLite数据库中
- 文件路径作为关联字段
- 支持批量数据导入/导出

### API接口
- `DataPathManager`: 统一路径管理
- `ProductModel`: 产品数据模型  
- `InspectionBatch`: 检测批次管理

## 注意事项

### 磁盘空间管理
- 单个产品数据通常占用 50-500MB
- 图像文件是主要空间消耗
- 建议定期清理过期数据

### 权限设置
- 读权限: 所有用户
- 写权限: 仅授权操作员
- 删除权限: 仅管理员

### 数据完整性
- 定期检查文件完整性
- 自动验证JSON格式
- 监控磁盘空间使用

## 故障排除

### 常见问题

1. **数据目录不存在**
   - 检查路径配置
   - 确认磁盘挂载状态

2. **权限不足**
   - 检查文件系统权限
   - 确认用户组设置

3. **磁盘空间不足**
   - 清理临时文件
   - 归档历史数据

### 数据恢复
- 从备份恢复
- 重建索引文件
- 修复损坏的JSON文件

## 更新日志

### v1.0 (2025-01-13)
- 初始版本
- 定义基本目录结构
- 建立命名规范
- 添加文件格式说明

---

**技术支持**: 如有问题请联系开发团队  
**文档位置**: `/Data/README.md`