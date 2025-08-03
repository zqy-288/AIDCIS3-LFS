"""
模拟间隔4列配对逻辑
"""

def simulate_pairing(columns):
    """模拟_create_row_interval_pairs的逻辑"""
    print(f"\n模拟配对逻辑，列号序列: {columns}")
    print("-" * 60)
    
    # 创建列号到索引的映射
    holes_by_col = {col: f"BC{col:03d}R164" for col in columns}
    sorted_cols = sorted(holes_by_col.keys())
    
    pairs = []
    processed_indices = set()
    
    i = 0
    while i < len(sorted_cols):
        if i in processed_indices:
            i += 1
            continue
            
        current_col = sorted_cols[i]
        current_hole = holes_by_col[current_col]
        
        # 寻找间隔4列的配对孔位
        target_col = current_col + 4
        pair_hole = holes_by_col.get(target_col)
        
        if pair_hole:
            # 找到配对
            pairs.append((current_hole, pair_hole))
            processed_indices.add(i)
            
            # 找到并标记配对孔位的索引
            pair_index = None
            for j, col in enumerate(sorted_cols):
                if col == target_col:
                    pair_index = j
                    break
            if pair_index is not None:
                processed_indices.add(pair_index)
            
            print(f"✅ 配对: {current_hole} + {pair_hole} (列{current_col} + 列{target_col})")
        else:
            # 无法配对
            pairs.append((current_hole,))
            print(f"❌ 单独: {current_hole} (列{current_col}，找不到列{target_col})")
        
        i += 1
    
    return pairs

# 测试不同的列号序列
print("="*60)
print("测试不同的列号序列")
print("="*60)

# 1. 连续列号（98-107）
continuous_cols = list(range(98, 108))
print("\n1. 连续列号（98-107）:")
pairs1 = simulate_pairing(continuous_cols)

# 2. 只有偶数列号
even_cols = [98, 100, 102, 104, 106, 108, 110]
print("\n2. 只有偶数列号:")
pairs2 = simulate_pairing(even_cols)

# 3. 实际可能的列号（根据测试数据推测）
actual_cols = [98, 99, 100, 101, 102, 103, 104, 105, 106, 107]
print("\n3. 根据测试数据推测的列号:")
pairs3 = simulate_pairing(actual_cols)

# 4. 如果间隔被修改为8
print("\n4. 如果代码被修改为 target_col = current_col + 8:")
print("   那么98 + 8 = 106，这就解释了BC098R164 + BC106R164的配对")

print("\n结论:")
print("- 代码逻辑是 target_col = current_col + 4")
print("- 对于连续列号，应该产生 98+102, 99+103, 100+104 等配对")
print("- 实际看到 98+106 表示:")
print("  1. 代码可能被修改过（+4 改为 +8）")
print("  2. 或者列号序列不是我们想象的那样")
print("  3. 或者存在其他影响配对的逻辑")