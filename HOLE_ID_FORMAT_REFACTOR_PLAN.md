# 孔位ID格式统一重构计划

## 概述

当前项目中存在多种孔位ID格式，造成了代码复杂性和潜在的错误。本文档列出所有需要修改的文件，以统一使用 `C{col:03d}R{row:03d}` 格式（如 `C001R001`）作为唯一标准格式。

## 需要修改的文件清单

### 1. **src/aidcis2/graphics/dynamic_sector_view.py**

#### 需要修改的代码：
- **行号 1987-2030**：修改 `_normalize_hole_id` 方法，只保留对C格式的验证
  ```python
  def _normalize_hole_id(self, hole_id: str) -> str:
      """验证孔位ID格式
      只接受标准格式 C{col:03d}R{row:03d}
      """
      import re
      if not hole_id:
          return ""
      
      # 只接受标准格式 C{col:03d}R{row:03d}
      match = re.match(r'^C(\d{3})R(\d{3})$', hole_id)
      if match:
          return hole_id  # 直接返回原始ID，不做转换
      
      # 不支持的格式，记录警告
      print(f"⚠️ 警告：不支持的ID格式: {hole_id}")
      return hole_id  # 返回原始值，让调用者处理
  ```

- **行号 1714-1717**：简化ID处理逻辑
  ```python
  # 直接使用原始ID，不需要规范化
  sector_hole_ids.add(sid)  # 直接添加原始ID
  # 删除规范化相关的代码
  ```

- **行号 1726-1754**：简化ID匹配逻辑
  ```python
  # 直接使用字符串比较，不需要多种格式匹配
  if hole_id in self.graphics_view.hole_items:
      # 直接处理，无需格式转换
  ```

### 2. **src/modules/archive_manager.py**

#### 需要修改的代码：
- **行号 48-76**：保留验证函数，简化转换函数
  ```python
  def validate_new_hole_id_format(hole_id: str) -> bool:
      """验证孔位ID是否符合标准格式 C{col:03d}R{row:03d}"""
      pattern = r'^C\d{3}R\d{3}$'
      return bool(re.match(pattern, hole_id))

  def convert_hole_id_format(hole_id: str) -> str:
      """验证并返回标准格式ID"""
      if validate_new_hole_id_format(hole_id):
          return hole_id
      # 记录警告，但不抛出异常，保持向后兼容
      print(f"⚠️ 警告：非标准ID格式: {hole_id}")
      return hole_id
  ```

### 3. **src/models/batch_data_manager.py**

#### 需要修改的代码：
- **行号 79-108**：保留验证函数，删除旧格式解析
  ```python
  def validate_hole_id_format(hole_id: str) -> bool:
      """验证孔位ID格式是否符合标准 C{col:03d}R{row:03d}"""
      pattern = r'^C\d{3}R\d{3}$'
      return bool(re.match(pattern, hole_id))
  
  # 删除 parse_old_format_ids 方法
  # 删除所有旧格式转换逻辑
  ```

### 4. **src/main_window.py**

#### 需要创建配置常量：
- **在文件开头添加配置常量**（约第50行附近）：
  ```python
  # 孔位数据可用性配置
  HOLES_WITH_DATA = ["C001R001", "C002R001"]  # 有实时监控和历史数据的孔位
  ```

- **行号 1367, 1385**：使用配置常量
  ```python
  # 修改为
  has_data = self.selected_hole.hole_id in HOLES_WITH_DATA
  ```

- **行号 2206, 2244**：使用配置常量
  ```python
  # 修改为
  has_data = hole.hole_id in HOLES_WITH_DATA
  ```

- **行号 3847-3883**：这部分代码需要检查其用途
  ```python
  # 如果是旧的兼容性代码，应该删除
  # 如果仍需要特殊处理某些孔位，应更新为使用标准格式
  ```

### 5. **src/modules/history_viewer.py**

#### 需要修改的代码：
- **行号 750-765**：替换硬编码的旧格式ID
  ```python
  # 原代码使用 H00001-H00005
  holes = ["H00001", "H00002", "H00003", "H00004", "H00005"]
  # 改为使用实际存在的标准格式ID
  holes = ["C048R164", "C047R164", "C046R164", "C045R164", "C044R164"]
  ```

### 6. **src/modules/workpiece_diagram.py**

#### 需要修改的代码：
- **行号 299-301, 454-456**：更新示例ID
  ```python
  # 原代码
  sample_holes = ["H001", "H002", "H003"]
  # 改为使用实际存在的标准格式ID
  sample_holes = ["C048R164", "C047R164", "C046R164"]
  ```

### 7. **src/aidcis2/models/models.py**

#### 需要修改的代码：
- **行号 374-382**：更新示例代码中的ID格式
  ```python
  # 示例代码中使用 H001
  hole_id="H001"
  # 改为使用实际存在的标准格式ID
  hole_id="C048R164"
  ```

### 8. **src/aidcis2/graphics/hole_item.py**

#### 需要修改的代码：
- **检查并移除任何ID格式转换逻辑**
- **确保tooltip和显示使用原始ID格式**
- **验证ID显示不进行任何不必要的格式化**

### 9. **src/aidcis2/graphics/graphics_view.py**

#### 需要修改的代码：
- **load_holes方法**：确保不进行ID格式转换
- **hole_items字典**：验证使用原始ID作为键
- **查找和匹配逻辑**：简化为直接字符串比较

### 10. **src/modules/report_output_interface.py**

#### 需要修改的代码：
- **报告标题和内容**：确保使用标准格式ID
- **Excel列标题**：验证ID列使用正确的格式
- **PDF报告**：检查ID显示格式的一致性

### 11. **src/modules/realtime_chart.py**

#### 需要修改的代码：
- **图表标题**：使用标准格式显示孔位ID
- **数据点标签**：确保tooltip显示正确的ID格式
- **图例**：验证多孔位对比时的ID显示

### 12. **测试文件更新**

需要更新所有测试文件中的ID格式：
- **tests/test_hole_data.py**：更新测试用例中的ID
- **tests/test_batch_manager.py**：验证批处理中的ID格式
- **tests/test_archive_manager.py**：测试归档功能的ID处理
- **tests/test_dxf_parser.py**：确保DXF解析生成正确格式的ID

### 13. **配置文件创建**

需要创建统一的配置文件：
```python
# config/hole_config.py
"""孔位配置管理"""

# 有监控数据的特殊孔位
MONITORED_HOLES = ["C001R001", "C002R001"]

# 孔位ID格式正则表达式
HOLE_ID_PATTERN = r'^C\d{3}R\d{3}$'

# 示例孔位（用于演示和测试）
EXAMPLE_HOLES = ["C048R164", "C047R164", "C046R164"]
```

### 14. **数据迁移工具集**

创建完整的迁移工具：
```python
# scripts/migrate_hole_ids.py - 主迁移脚本
# scripts/backup_before_migration.py - 迁移前备份
# scripts/validate_id_format.py - ID格式验证工具
# scripts/generate_id_mapping.py - 生成新旧ID映射表
```

### 15. **兼容性层（可选）**

如果需要保持向后兼容：
```python
# src/utils/id_compatibility.py
"""ID格式兼容性支持（过渡期使用）"""

def is_legacy_format(hole_id: str) -> bool:
    """检查是否为旧格式ID"""
    return hole_id.startswith('H') and hole_id[1:].isdigit()

def get_compatibility_warning() -> str:
    """返回兼容性警告信息"""
    return "警告：检测到旧格式ID，请尽快迁移到标准格式 C{col:03d}R{row:03d}"
```

## 重构步骤

### 第一阶段：准备工作
1. 创建ID格式映射表
2. 编写数据迁移脚本
3. 备份所有数据文件

### 第二阶段：代码重构
1. 删除 `_normalize_hole_id` 方法
2. 移除所有ID格式转换逻辑
3. 更新所有硬编码的旧格式ID
4. 简化ID比较逻辑（直接字符串比较）

### 第三阶段：数据迁移
1. 运行迁移脚本转换所有存储的数据
2. 更新所有配置文件
3. 验证数据完整性

### 第四阶段：测试验证
1. 单元测试
2. 集成测试
3. 用户验收测试

## 预期收益

1. **代码简化**：删除约200行冗余的ID转换代码
2. **性能提升**：避免运行时的ID格式转换
3. **可维护性**：统一的ID格式便于理解和维护
4. **减少错误**：消除ID格式不匹配导致的bug

## 风险评估

1. **数据兼容性**：需要确保所有历史数据都能正确迁移
2. **第三方集成**：如果有外部系统依赖旧格式，需要提供适配器
3. **用户习惯**：用户可能习惯了旧的ID格式

## 建议的ID映射关系

| 旧格式 | 新格式 | 备注 |
|--------|--------|------|
| H00001 | C001R001 | 第1列第1行 |
| H00002 | C002R001 | 第2列第1行 |
| H00003 | C003R001 | 第3列第1行 |
| (1,1) | C001R001 | 坐标格式转换 |
| hole_1 | - | 需要根据实际位置确定 |

## 注意事项

1. 在修改前必须备份所有数据
2. 逐步迁移，先在测试环境验证
3. 保留一段时间的兼容性层，确保平滑过渡
4. 详细记录所有修改，便于回滚

## 总结

通过统一使用 `C{col:03d}R{row:03d}` 格式，可以显著简化代码逻辑，提高系统的可维护性和可靠性。虽然需要修改多个文件，但长远来看是值得的投资。