#!/usr/bin/env python3
"""
实时显示时间间隔配置工具
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def show_current_settings():
    """显示当前时间间隔设置"""
    print("⏱️ 当前时间间隔设置")
    print("=" * 60)
    
    print("📊 **图表更新频率**:")
    print("  当前设置: 1000ms (1秒)")
    print("  作用: 控制面板A图表的刷新频率")
    print("  位置: self.update_timer.start(1000)")
    print()
    
    print("📈 **CSV数据播放频率**:")
    print("  当前设置: 100ms (0.1秒)")
    print("  作用: 控制数据点的播放速度")
    print("  位置: self.csv_timer.start(100)")
    print()
    
    print("🖼️ **图像切换频率**:")
    print("  当前设置: 跟随CSV数据播放")
    print("  作用: 根据数据进度自动切换图像")
    print("  计算: 每176个数据点切换一次图像")
    print()

def calculate_timing_effects(csv_interval, chart_interval):
    """计算时间间隔的效果"""
    print(f"📊 时间间隔效果计算 (CSV: {csv_interval}ms, 图表: {chart_interval}ms)")
    print("=" * 60)
    
    # 计算数据播放速度
    points_per_second = 1000 / csv_interval
    total_points = 882  # C001R001的数据点数
    total_time_seconds = total_points / points_per_second
    
    print(f"📈 **数据播放效果**:")
    print(f"  数据点播放速度: {points_per_second:.1f} 点/秒")
    print(f"  完整播放时间: {total_time_seconds:.1f} 秒 ({total_time_seconds/60:.1f} 分钟)")
    print()
    
    # 计算图像切换频率
    image_switch_interval = 176 * csv_interval / 1000  # 秒
    print(f"🖼️ **图像切换效果**:")
    print(f"  图像切换间隔: {image_switch_interval:.1f} 秒")
    print(f"  总共5张图像，每张显示 {image_switch_interval:.1f} 秒")
    print()
    
    # 计算图表更新频率
    chart_updates_per_second = 1000 / chart_interval
    print(f"📊 **图表更新效果**:")
    print(f"  图表刷新频率: {chart_updates_per_second:.1f} 次/秒")
    print(f"  视觉流畅度: {'很流畅' if chart_interval <= 50 else '流畅' if chart_interval <= 200 else '一般' if chart_interval <= 500 else '较慢'}")
    print()

def suggest_timing_presets():
    """建议的时间间隔预设"""
    print("🎯 推荐的时间间隔预设")
    print("=" * 60)
    
    presets = [
        {
            "name": "超快速演示",
            "csv": 20,
            "chart": 100,
            "desc": "快速演示效果，数据播放很快"
        },
        {
            "name": "快速演示", 
            "csv": 50,
            "chart": 200,
            "desc": "适合演示和测试，播放速度较快"
        },
        {
            "name": "标准速度",
            "csv": 100,
            "chart": 500,
            "desc": "当前设置，平衡速度和稳定性"
        },
        {
            "name": "慢速详细",
            "csv": 200,
            "chart": 1000,
            "desc": "慢速播放，便于观察细节"
        },
        {
            "name": "实时模拟",
            "csv": 500,
            "chart": 1000,
            "desc": "接近真实测量速度"
        }
    ]
    
    for i, preset in enumerate(presets, 1):
        print(f"{i}. **{preset['name']}**:")
        print(f"   CSV间隔: {preset['csv']}ms")
        print(f"   图表间隔: {preset['chart']}ms")
        print(f"   说明: {preset['desc']}")
        calculate_timing_effects(preset['csv'], preset['chart'])
        print()

def apply_timing_settings(csv_interval, chart_interval):
    """应用时间间隔设置"""
    print(f"🔧 应用时间间隔设置: CSV={csv_interval}ms, 图表={chart_interval}ms")
    
    try:
        # 读取文件
        file_path = "modules/realtime_chart.py"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建备份
        backup_path = f"{file_path}.timing_backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已创建备份: {backup_path}")
        
        # 替换CSV定时器间隔
        old_csv = 'self.csv_timer.start(100)'
        new_csv = f'self.csv_timer.start({csv_interval})'
        content = content.replace(old_csv, new_csv)
        
        # 替换图表更新间隔
        old_chart = 'self.update_timer.start(1000)'
        new_chart = f'self.update_timer.start({chart_interval})'
        content = content.replace(old_chart, new_chart)
        
        # 写入修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 时间间隔设置已更新")
        print()
        print("🔄 **重新启动程序以应用新设置**:")
        print("  python main.py")
        
        return True
        
    except Exception as e:
        print(f"❌ 设置失败: {e}")
        return False

def main():
    print("⏱️ 实时显示时间间隔配置工具")
    print("=" * 80)
    
    # 显示当前设置
    show_current_settings()
    
    # 显示推荐预设
    suggest_timing_presets()
    
    print("🎛️ **配置选项**:")
    print("=" * 60)
    
    print("选择配置方式:")
    print("1. 使用推荐预设")
    print("2. 自定义时间间隔")
    print("3. 仅查看当前设置")
    print()
    
    try:
        choice = input("请选择 (1-3): ").strip()
        
        if choice == "1":
            print("\n选择预设:")
            print("1. 超快速演示 (20ms/100ms)")
            print("2. 快速演示 (50ms/200ms)")  
            print("3. 标准速度 (100ms/500ms) - 当前")
            print("4. 慢速详细 (200ms/1000ms)")
            print("5. 实时模拟 (500ms/1000ms)")
            
            preset_choice = input("请选择预设 (1-5): ").strip()
            
            presets = [
                (20, 100),   # 超快速
                (50, 200),   # 快速
                (100, 500),  # 标准
                (200, 1000), # 慢速
                (500, 1000)  # 实时
            ]
            
            if preset_choice in ["1", "2", "3", "4", "5"]:
                csv_interval, chart_interval = presets[int(preset_choice) - 1]
                apply_timing_settings(csv_interval, chart_interval)
            else:
                print("无效选择")
                
        elif choice == "2":
            print("\n自定义时间间隔:")
            csv_interval = int(input("CSV数据播放间隔 (ms, 建议20-500): "))
            chart_interval = int(input("图表更新间隔 (ms, 建议100-1000): "))
            
            if 10 <= csv_interval <= 1000 and 50 <= chart_interval <= 2000:
                apply_timing_settings(csv_interval, chart_interval)
            else:
                print("❌ 时间间隔超出建议范围")
                
        elif choice == "3":
            print("✅ 当前设置已显示")
            
        else:
            print("无效选择")
            
    except (ValueError, KeyboardInterrupt):
        print("\n操作取消")

if __name__ == "__main__":
    main()
