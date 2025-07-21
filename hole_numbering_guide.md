# 孔位编号逻辑详细说明

## 当前数据结构分析

基于对 `dongzhong_hole_grid.json` 的分析，现有编号系统如下：

### 现状
- **总孔位数**: 25,210 个
- **编号格式**: CxxxRyyy (C=Column列, R=Row行)
- **列范围**: C001 到 C098 (98列)
- **行范围**: R001 到 R328 (328行)
- **编号特点**: 每列都从R001开始，连续编号到该列的最后一个孔

### 现有编号示例
```
C001列: C001R001, C001R002, C001R003, ..., C001R328
C002列: C002R001, C002R002, C002R003, ..., C002R328
...
C098列: C098R001, C098R002, C098R003, ..., C098R328
```

## 可能的重新编号策略

### 策略1: 连续序列编号
将所有孔位重新编号为连续的数字序列：
```
原来: C001R001, C002R001, C003R001, ...
新的: 00001, 00002, 00003, ...
```

### 策略2: 基于空间位置的重新编号
如果您的 C001R165->C001R001 示例是指：
- 重新定义坐标系起点
- 将某个物理位置重新定义为(1,1)点

### 策略3: 自定义行列映射
```python
# 示例映射规则
row_mapping = {
    165: 1,    # 将原来的R165重新编号为R001
    166: 2,    # 将原来的R166重新编号为R002  
    167: 3,    # 将原来的R167重新编号为R003
    # ... 继续其他映射
}
```

### 策略4: 区域选择重新编号
只对特定区域的孔位进行重新编号，比如：
- 只重新编号R150-R200范围的孔位
- 保持其他区域编号不变

## 具体实现建议

### 方案A: 如果您希望简化编号系统
```python
def simple_sequential_numbering():
    """将所有孔位重新编号为1, 2, 3, ..."""
    new_mapping = {}
    counter = 1
    
    for hole in sorted_holes:
        old_id = hole['hole_id']
        new_id = f"{counter:05d}"  # 00001, 00002, etc.
        new_mapping[old_id] = new_id
        counter += 1
    
    return new_mapping
```

### 方案B: 如果您希望重新定义坐标原点
```python
def redefine_coordinate_origin(origin_col=1, origin_row=165):
    """以指定位置为新的(1,1)点重新编号"""
    new_mapping = {}
    
    for hole in holes:
        old_col, old_row = parse_hole_id(hole['hole_id'])
        new_col = old_col - origin_col + 1
        new_row = old_row - origin_row + 1
        
        if new_col > 0 and new_row > 0:  # 只保留正坐标
            new_id = f"C{new_col:03d}R{new_row:03d}"
            new_mapping[hole['hole_id']] = new_id
    
    return new_mapping
```

### 方案C: 基于您的具体示例模式
```python
def custom_pattern_mapping():
    """基于C001R165->C001R001的模式"""
    # 如果165对应1，那么映射关系是: new = old - 164
    offset = 164
    
    new_mapping = {}
    for hole in holes:
        col, row = parse_hole_id(hole['hole_id'])
        if row >= 165:  # 只处理R165及以后的行
            new_row = row - offset
            new_id = f"C{col:03d}R{new_row:03d}"
            new_mapping[hole['hole_id']] = new_id
        else:
            # 保持原编号或其他处理逻辑
            new_mapping[hole['hole_id']] = hole['hole_id']
    
    return new_mapping
```

## 推荐实现脚本

```python
#!/usr/bin/env python3
"""
根据具体需求选择合适的重新编号策略
"""

import json
import re

def main():
    # 读取原始数据
    with open('dongzhong_hole_grid.json', 'r') as f:
        data = json.load(f)
    
    # 选择编号策略
    print("请选择编号策略:")
    print("1. 连续序列编号 (1, 2, 3, ...)")
    print("2. 重新定义坐标原点 (以R165为新R001)")
    print("3. 自定义偏移映射")
    
    choice = input("请输入选择 (1-3): ")
    
    if choice == "1":
        mapping = simple_sequential_numbering(data)
    elif choice == "2":
        mapping = redefine_coordinate_origin(data, origin_row=165)
    elif choice == "3":
        mapping = custom_pattern_mapping(data)
    else:
        print("无效选择")
        return
    
    # 应用映射并保存结果
    apply_mapping_and_save(data, mapping)

if __name__ == "__main__":
    main()
```

## 问题澄清

为了提供最准确的解决方案，请明确以下问题：

1. **您的具体目标是什么？**
   - 简化编号系统？
   - 重新定义坐标原点？
   - 其他特定需求？

2. **C001R165->C001R001的具体含义？**
   - 是将R165重新定义为R001？
   - 还是将165这个数值减少164变成1？

3. **编号范围？**
   - 是否所有孔位都需要重新编号？
   - 还是只处理特定范围？

4. **保持列编号不变？**
   - C001还是C001，只改变行编号？
   - 还是列编号也需要调整？

请提供这些信息，我将为您创建精确的重新编号脚本。