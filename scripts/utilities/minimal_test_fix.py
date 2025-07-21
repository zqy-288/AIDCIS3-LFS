#!/usr/bin/env python3
"""
最小化测试修复 - 临时禁用有问题的功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def apply_minimal_fix():
    """应用最小化修复"""
    
    print("🚨 应用最小化修复")
    print("=" * 60)
    
    # 读取当前文件
    file_path = "modules/realtime_chart.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建备份
        backup_path = f"{file_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已创建备份: {backup_path}")
        
        # 应用最小化修复
        # 1. 简化update_plot方法
        minimal_update_plot = '''    def update_plot(self):
        """最小化图表更新 - 临时禁用复杂功能"""
        try:
            # 临时禁用所有matplotlib操作
            pass
        except:
            pass'''
        
        # 查找并替换update_plot方法
        import re
        
        # 匹配整个update_plot方法
        pattern = r'    def update_plot\(self\):.*?(?=    def |\Z)'
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, minimal_update_plot + '\n\n', content, flags=re.DOTALL)
            print("✅ 已简化update_plot方法")
        else:
            print("⚠️ 未找到update_plot方法")
        
        # 2. 禁用定时器
        content = content.replace(
            'self.update_timer.start(500)',
            '# self.update_timer.start(500)  # 临时禁用'
        )
        print("✅ 已禁用图表更新定时器")
        
        # 写入修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 最小化修复已应用")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def restore_backup():
    """恢复备份"""
    file_path = "modules/realtime_chart.py"
    backup_path = f"{file_path}.backup"
    
    try:
        if os.path.exists(backup_path):
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 已恢复备份文件")
            return True
        else:
            print("❌ 备份文件不存在")
            return False
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False

def main():
    print("🔧 最小化测试修复工具")
    print("=" * 80)
    
    print("📋 **修复说明**:")
    print("=" * 60)
    
    print("这是一个临时的最小化修复，用于:")
    print("1. 🚫 完全禁用matplotlib图表更新")
    print("2. ⏱️ 禁用可能有问题的定时器")
    print("3. 🛡️ 确保程序基本功能可以运行")
    print("4. 🔍 帮助定位具体问题所在")
    print()
    
    print("⚠️ **注意事项**:")
    print("- 这会临时禁用图表显示功能")
    print("- 仅用于测试程序是否能正常启动")
    print("- 修复后需要恢复正常功能")
    print()
    
    choice = input("是否应用最小化修复? (y/n): ").lower().strip()
    
    if choice == 'y':
        if apply_minimal_fix():
            print("\n🧪 **测试步骤**:")
            print("=" * 60)
            print("1. 🚀 启动程序: python main.py")
            print("2. 📊 检查是否还有错误")
            print("3. 🖥️ 验证基本界面功能")
            print("4. 📝 记录测试结果")
            print()
            
            print("如果程序能正常启动，说明问题在matplotlib部分")
            print("如果仍有错误，说明问题在其他地方")
            print()
            
            restore_choice = input("测试完成后是否恢复备份? (y/n): ").lower().strip()
            if restore_choice == 'y':
                restore_backup()
        
    elif choice == 'restore' or choice == 'r':
        restore_backup()
    
    else:
        print("取消操作")

if __name__ == "__main__":
    main()
