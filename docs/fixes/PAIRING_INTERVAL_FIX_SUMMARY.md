# 配对间隔修复总结

## 问题描述
用户报告检测配对间隔过大：
- 实际配对：BC098R164 + BC106R164（间隔8列）
- 期望配对：BC098R164 + BC102R164（间隔4列）

## 根本原因
1. **列号序列特点**：
   - 实际列号：86, 88, 90, 92, 94, 96, 98, 100, 102, 104, 106, 108, 110
   - 相邻列号间隔为2

2. **代码逻辑错误**：
   - 原代码：`if i + 4 < len(row_holes)`
   - 在索引上跳过4个位置：98(索引0) → 106(索引4)
   - 实际应该跳过2个位置：98(索引0) → 102(索引2)

3. **存在两套配对实现**：
   - `_generate_interval_four_path()` - 实际使用的方法
   - `_create_row_interval_pairs()` - 未被使用的方法

## 修复方案

### 文件：src/pages/shared/components/snake_path/snake_path_renderer.py

```python
# 第454行，修改配对逻辑
# 原代码：
if i + 4 < len(row_holes) and (i + 4) not in processed:
    pair = HolePair(holes=[row_holes[i], row_holes[i + 4]], is_pair=True)

# 新代码：
target_index = i + 2  # 跳过2个位置而不是4个
if target_index < len(row_holes) and target_index not in processed:
    pair = HolePair(holes=[row_holes[i], row_holes[target_index]], is_pair=True)
```

## 验证结果
修复后的配对结果：
- 第1对：BC098R164 + BC102R164（列间隔：4）✓
- 第2对：BC100R164 + BC104R164（列间隔：4）✓
- 第3对：BC106R164 + BC110R164（列间隔：4）✓

## 关键理解
- "间隔4列"指的是列号数值差为4（98→102）
- 由于列号序列间隔为2，需要在索引上跳过2个位置
- 这确保了正确的检测配对间隔