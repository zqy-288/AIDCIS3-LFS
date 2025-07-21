#!/usr/bin/env python3
"""
快速测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🚀 快速测试 - 临时禁用图表更新")
    print("=" * 80)
    
    print("✅ **已应用临时修复**:")
    print("=" * 60)
    
    print("修复内容:")
    print("1. 🚫 临时禁用matplotlib图表更新定时器")
    print("2. 🛡️ 保留超级安全的update_plot方法")
    print("3. 🔤 保持简化的字体配置")
    print("4. ⏱️ 保持降低的CSV播放频率")
    print()
    
    print("🧪 **现在请测试**:")
    print("=" * 60)
    
    print("步骤1: 启动程序")
    print("  python main.py")
    print("  预期: 程序应该能正常启动，无matplotlib错误")
    print()
    
    print("步骤2: 检查基本功能")
    print("  - 界面正常显示")
    print("  - 选项卡切换正常")
    print("  - 孔位选择正常")
    print("  - 按钮响应正常")
    print()
    
    print("步骤3: 测试面板B")
    print("  - 切换到实时监控")
    print("  - 选择孔位H00001")
    print("  - 点击面板B的'启动算法'")
    print("  - 观察控制台调试信息")
    print()
    
    print("🔍 **预期结果**:")
    print("=" * 60)
    
    print("如果修复成功:")
    print("✅ 程序启动无KeyboardInterrupt")
    print("✅ 程序启动无matplotlib错误")
    print("✅ 界面正常显示")
    print("✅ 基本功能可以使用")
    print("✅ 面板B图像调试信息正常输出")
    print()
    
    print("注意事项:")
    print("⚠️ 面板A图表暂时不会更新(已禁用)")
    print("⚠️ 这是为了排查问题的临时措施")
    print("⚠️ 其他功能应该正常工作")
    print()
    
    print("🔧 **如果测试成功**:")
    print("=" * 60)
    
    print("说明问题确实在matplotlib图表更新部分")
    print("可以逐步恢复功能:")
    print()
    print("1. 先恢复定时器但降低频率:")
    print("   self.update_timer.start(1000)  # 1秒更新一次")
    print()
    print("2. 简化update_plot方法:")
    print("   只更新数据，不调整坐标轴")
    print()
    print("3. 逐步增加功能直到找到具体问题")
    print()
    
    print("🚨 **如果仍有错误**:")
    print("=" * 60)
    
    print("说明问题不在matplotlib部分，可能在:")
    print("1. 🔤 字体配置")
    print("2. 🖼️ 图像加载")
    print("3. 🔄 其他定时器")
    print("4. 📊 数据处理")
    print()
    
    print("请提供具体的错误信息进行进一步诊断")
    print()
    
    print("🎯 **测试重点**:")
    print("=" * 60)
    
    print("重点观察:")
    print("1. 🚀 程序是否能正常启动")
    print("2. 🖥️ 界面是否正常显示")
    print("3. 🔄 基本操作是否响应")
    print("4. 🖼️ 面板B图像调试信息")
    print()
    
    print("面板B调试信息应该显示:")
    print("🔍 调试: 尝试显示图像索引 0")
    print("🔍 调试: 当前图像列表长度 X")
    print("🔍 调试: 图像路径 /path/to/image")
    print("🔍 调试: 文件存在 True/False")
    print()
    
    print("🚀 **开始测试**:")
    print("现在请运行: python main.py")
    print("并按照上述步骤进行测试")

if __name__ == "__main__":
    main()
