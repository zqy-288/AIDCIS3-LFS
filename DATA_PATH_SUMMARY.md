# AIDCIS3 数据路径总结

## 主要数据目录

### 1. Data/ (项目根目录下)
这是主要的数据存储目录，由 DataPathManager 管理。

#### 目录结构：
```
Data/
├── Products/                    # 产品相关数据
│   ├── CAP1000/                # 产品ID目录
│   │   ├── dxf/               # DXF文件存储
│   │   │   └── CAP1000.dxf    # 产品对应的DXF文件
│   │   └── InspectionBatches/ # 检测批次数据
│   │       └── {timestamp}/    # 批次目录
│   │           └── data_batches/ # 批次数据文件
│   └── {其他产品ID}/
│
├── CAP1000/                    # 实时数据目录（旧格式）
│   ├── AC002R001/             # 孔位ID目录
│   │   ├── BISDM/            # 图像数据
│   │   │   └── result/       # 检测结果图像
│   │   └── CCIDM/            # 测量数据
│   │       └── measurement_data_*.csv
│   └── {其他孔位ID}/
│
└── README.md
```

### 2. src/data/ (源代码目录)
存储系统配置和数据库文件。

```
src/data/
├── config_manager.py          # 配置管理
├── data_access_layer.py      # 数据访问层
├── product_models.db         # 产品型号数据库
└── repositories.py           # 数据仓库
```

### 3. config/ (配置目录)
存储系统配置文件。

```
config/
├── config.json              # 主配置文件
├── hole_id_mapping.json     # 孔位ID映射
├── migration_config.json    # 迁移配置
└── rotation_settings.json   # 旋转设置
```

## 路径管理器 (DataPathManager)

DataPathManager 提供了统一的路径管理接口：

- `get_product_path(product_id)` - 获取产品目录路径
- `get_product_dxf_path(product_id, filename)` - 获取产品DXF文件路径
- `get_inspection_batch_path(product_name, batch_id)` - 获取检测批次路径
- `get_hole_data_path(hole_id, product_id)` - 获取孔位数据路径

## 路径使用示例

```python
from src.models.data_path_manager import DataPathManager

path_manager = DataPathManager()

# 获取CAP1000的DXF文件路径
dxf_path = path_manager.get_product_dxf_path("CAP1000", "CAP1000.dxf")
# 返回: "Data/Products/CAP1000/dxf/CAP1000.dxf"

# 获取检测批次路径
batch_path = path_manager.get_inspection_batch_path("CAP1000", "20250720_091056")
# 返回: "Data/Products/CAP1000/InspectionBatches/20250720_091056"
```

## 注意事项

1. 所有数据路径都相对于项目根目录
2. Data目录使用大写"D"
3. 产品DXF文件应存储在 `Data/Products/{产品ID}/dxf/` 目录下
4. 实时检测数据存储在 `Data/{产品ID}/{孔位ID}/` 目录下
5. 批次数据存储在 `Data/Products/{产品ID}/InspectionBatches/` 目录下

## 更新记录

- 2025-07-29: 将CAP1000的DXF文件从 assets 目录复制到 Data/Products/CAP1000/dxf/ 并重命名为 CAP1000.dxf