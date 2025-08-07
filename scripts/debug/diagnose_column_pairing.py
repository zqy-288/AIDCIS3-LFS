"""
诊断列号配对问题
分析为什么配对是BC098R164+BC106R164而不是BC098R164+BC102R164
"""

# 测试列号配对逻辑
def test_column_pairing():
    print("🔍 分析列号配对逻辑")
    print("="*60)
    
    # 假设的列号序列
    column_numbers = [98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108]
    
    print("\n1. 如果列号是连续的（98, 99, 100, 101, 102...）：")
    print("   间隔4列配对应该是：")
    for i, col in enumerate(column_numbers):
        if i + 4 < len(column_numbers):
            pair_col = column_numbers[i + 4]
            print(f"   - 列{col} + 列{pair_col} (间隔4列)")
    
    print("\n2. 实际测试数据显示的配对：")
    print("   - BC098R164 + BC106R164")
    print("   - 这表示列98和列106配对")
    print("   - 106 - 98 = 8")
    
    print("\n3. 可能的解释：")
    print("   a) '间隔4列'可能是指中间有4个列")
    print("      98 -> (99, 100, 101, 102) -> 103")
    print("      但这样应该是98+103配对，不是98+106")
    
    print("\n   b) 列号可能不是连续的")
    print("      比如：98, 100, 102, 104, 106...")
    print("      如果是偶数列号，那么98后面第4个是106")
    
    print("\n   c) 可能存在特殊的列号编号规则")
    
    # 测试不同的列号序列
    print("\n4. 测试不同的列号序列：")
    
    # 偶数列号序列
    even_columns = [98, 100, 102, 104, 106, 108, 110]
    print("\n   如果只有偶数列号：")
    for i in range(len(even_columns)):
        if i + 4 < len(even_columns):
            print(f"   - 列{even_columns[i]} + 列{even_columns[i+4]} (索引间隔4)")
    
    # 查看snake_path_renderer.py中的实际逻辑
    print("\n5. 代码分析：")
    print("   在_create_row_interval_pairs中：")
    print("   target_col = current_col + 4")
    print("   这意味着是列号数值+4，不是索引+4")
    print("   所以98+4=102才对")
    
    print("\n6. 结论：")
    print("   ❌ 如果代码是target_col = current_col + 4")
    print("      那么BC098应该配对BC102，而不是BC106")
    print("   ❌ 实际配对BC098+BC106表示间隔是8，不是4")
    print("\n   可能的原因：")
    print("   - 代码中的+4可能被修改过")
    print("   - 或者列号编号有特殊规则")
    print("   - 或者'间隔4列'的定义与我们理解的不同")

if __name__ == "__main__":
    test_column_pairing()