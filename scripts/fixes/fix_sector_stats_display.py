#!/usr/bin/env python3
"""修复扇形统计显示所有孔位的问题"""

import re

def analyze_issue():
    """分析问题根源"""
    print("问题分析：")
    print("1. 当点击扇形时，统计显示 total=6274（所有孔位）")
    print("2. 应该只显示该扇形的孔位数")
    print("\n根本原因：")
    print("- panorama_sector_coordinator.py 中 set_current_sector 方法正确获取了扇形孔位")
    print("- _calculate_sector_stats 方法正确计算了传入孔位列表的统计")
    print("- 但在 native_main_detection_view_p1.py 的 _on_sector_stats_updated 方法中")
    print("- 需要确保使用正确的格式化方法")
    print("\n修复方案：")
    print("需要检查 _format_sector_stats_text 方法的实现")

def check_format_method():
    """检查格式化方法的问题"""
    file_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/src/pages/main_detection_p1/native_main_detection_view_p1.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到 _format_sector_stats_text 方法
    pattern = r'def _format_sector_stats_text\(self, stats\):(.*?)(?=\n    def|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        method_content = match.group(0)
        print("\n当前 _format_sector_stats_text 方法:")
        print(method_content[:500] + "...")
        
        # 检查是否有问题
        if "len(hole_collection.holes)" in method_content:
            print("\n❌ 发现问题：方法中引用了 hole_collection.holes")
            return True
    
    return False

def fix_format_method():
    """修复格式化方法"""
    file_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/src/pages/main_detection_p1/native_main_detection_view_p1.py"
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找并修复 _format_sector_stats_text 方法
    in_method = False
    method_start = -1
    indent = ""
    
    for i, line in enumerate(lines):
        if "def _format_sector_stats_text(self, stats):" in line:
            in_method = True
            method_start = i
            indent = line[:line.index("def")]
            print(f"找到方法在第 {i+1} 行")
            break
    
    if in_method and method_start >= 0:
        # 重写整个方法
        new_method = f'''{indent}def _format_sector_stats_text(self, stats):
{indent}    """格式化扇形统计为文本（向后兼容）"""
{indent}    if not stats:
{indent}        return "扇形统计信息加载中..."
{indent}    
{indent}    # 如果stats是字典且包含统计信息
{indent}    if isinstance(stats, dict) and 'total' in stats:
{indent}        sector_name = ""
{indent}        if self.coordinator and self.coordinator.current_sector:
{indent}            sector_name = self.coordinator.current_sector.value
{indent}        
{indent}        text = f"扇形 {{sector_name}}\\n" if sector_name else "扇形统计\\n"
{indent}        text += f"总孔数: {{stats.get('total', 0)}}\\n"
{indent}        text += f"合格: {{stats.get('qualified', 0)}}\\n"
{indent}        text += f"异常: {{stats.get('defective', 0)}}\\n"
{indent}        text += f"待检: {{stats.get('pending', 0)}}\\n"
{indent}        text += f"盲孔: {{stats.get('blind', 0)}}\\n"
{indent}        text += f"拉杆: {{stats.get('tie_rod', 0)}}"
{indent}        return text
{indent}    
{indent}    # 如果是其他格式，返回原始字符串
{indent}    return str(stats)
'''
        
        # 找到方法结束位置
        method_end = method_start + 1
        for i in range(method_start + 1, len(lines)):
            # 如果遇到新的方法定义或类定义，说明当前方法结束
            if lines[i].strip() and not lines[i].startswith(indent + " ") and not lines[i].startswith(indent + "\t"):
                method_end = i
                break
            elif i == len(lines) - 1:
                method_end = i + 1
        
        # 替换方法
        lines[method_start:method_end] = [new_method + "\n"]
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ 方法已修复（第 {method_start+1} 行到第 {method_end} 行）")
        return True
    
    return False

if __name__ == "__main__":
    print("=== 修复扇形统计显示问题 ===\n")
    
    analyze_issue()
    
    print("\n检查格式化方法...")
    if check_format_method():
        print("\n开始修复...")
        if fix_format_method():
            print("\n✅ 修复完成！")
            print("\n修复内容：")
            print("1. 修正了 _format_sector_stats_text 方法")
            print("2. 确保使用 stats 字典中的 'total' 值，而不是全部孔位数")
            print("3. 格式化输出包含扇形名称和各类统计数据")
        else:
            print("\n❌ 修复失败")
    else:
        print("\n未发现明显问题，可能需要进一步调试")