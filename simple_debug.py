#!/usr/bin/env python3
"""简化的全景预览诊断"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def check_main_window_updates():
    """检查主窗口的状态更新调用"""
    print("🔍 检查主窗口的状态更新调用")
    
    main_window_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/src/main_window.py"
    
    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("📋 查找_update_panorama_hole_status调用:")
        
        for i, line in enumerate(lines):
            if '_update_panorama_hole_status' in line:
                print(f"\n📍 第{i+1}行: {line.strip()}")
                
                # 显示前后几行上下文
                start = max(0, i-3)
                end = min(len(lines), i+4)
                print("   上下文:")
                for j in range(start, end):
                    marker = ">>>" if j == i else "   "
                    print(f"   {marker} {j+1:4d}: {lines[j].rstrip()}")
        
        # 检查是否移除了限制条件
        found_restriction = False
        for line in lines:
            if "% 10 == 0" in line and "_update_panorama_hole_status" in line:
                found_restriction = True
                break
        
        if found_restriction:
            print("\n❌ 仍然存在每10个孔位同步一次的限制!")
            return False
        else:
            print("\n✅ 没有发现同步频率限制")
            return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def check_panorama_code():
    """检查全景预览代码"""
    print("\n🔧 检查全景预览代码")
    
    panorama_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/src/aidcis2/graphics/dynamic_sector_view.py"
    
    try:
        with open(panorama_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查批量更新间隔
        if "batch_update_interval = 1000" in content:
            print("✅ 批量更新间隔设置为1000ms")
        else:
            print("❌ 批量更新间隔设置不正确")
        
        # 检查update_hole_status方法
        if "def update_hole_status(self, hole_id: str, status):" in content:
            print("✅ update_hole_status方法存在")
        else:
            print("❌ update_hole_status方法缺失")
        
        # 检查_apply_batch_updates方法
        if "def _apply_batch_updates(self):" in content:
            print("✅ _apply_batch_updates方法存在")
        else:
            print("❌ _apply_batch_updates方法缺失")
        
        # 检查状态颜色映射
        status_colors_found = "status_colors = {" in content and "HoleStatus.QUALIFIED: QColor" in content
        if status_colors_found:
            print("✅ 状态颜色映射存在")
        else:
            print("❌ 状态颜色映射缺失")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def suggest_debug_steps():
    """建议调试步骤"""
    print("\n💡 建议的调试步骤:")
    print("1. 运行程序并点击'使用模拟进度'")
    print("2. 观察控制台输出中是否有以下信息:")
    print("   - '📦 [全景图] 缓存状态更新: X 个待更新'")
    print("   - '🔄 [全景图] 开始批量更新 X 个孔位状态'")
    print("   - '🔍 [全景图] 全景视图中有 X 个孔位图形项'")
    print("   - '✅ [全景图] 批量更新完成: X/Y 个孔位'")
    print("")
    print("3. 如果没有看到这些信息，说明:")
    print("   - 状态更新调用可能没有到达全景预览")
    print("   - 或者全景预览的hole_items为空")
    print("")
    print("4. 如果看到了但更新数量为0，说明:")
    print("   - hole_items字典中没有对应的孔位ID")
    print("   - 或者图形项的颜色设置失败")

def main():
    print("=" * 60)
    print("全景预览问题简化诊断")
    print("=" * 60)
    
    # 检查主窗口
    main_ok = check_main_window_updates()
    
    # 检查全景预览代码
    panorama_ok = check_panorama_code()
    
    print("\n" + "=" * 60)
    print("诊断结果")
    print("=" * 60)
    print(f"主窗口状态更新: {'✅ 正常' if main_ok else '❌ 异常'}")
    print(f"全景预览代码: {'✅ 正常' if panorama_ok else '❌ 异常'}")
    
    # 建议调试步骤
    suggest_debug_steps()

if __name__ == "__main__":
    main()