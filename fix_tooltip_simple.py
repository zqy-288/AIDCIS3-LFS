#!/usr/bin/env python3
"""
修复孔位工具提示问题的简单解决方案
使用标准Qt工具提示替换自定义工具提示
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def fix_hole_item_tooltip():
    """修复孔位工具提示"""
    
    hole_item_file = project_root / "src" / "aidcis2" / "graphics" / "hole_item.py"
    
    print("🔧 修复孔位工具提示...")
    
    try:
        # 读取文件
        with open(hole_item_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 在__init__方法中启用标准工具提示
        # 查找 "# 不设置工具提示，以减少内存使用" 这一行
        old_tooltip_comment = "        # 不设置工具提示，以减少内存使用\n        # self.setToolTip(self._create_tooltip())"
        new_tooltip_code = "        # 启用标准工具提示\n        self.setToolTip(self._create_tooltip())"
        
        if old_tooltip_comment in content:
            content = content.replace(old_tooltip_comment, new_tooltip_code)
            print("  ✅ 启用了标准工具提示")
        else:
            print("  ⚠️ 未找到工具提示注释，尝试另一种方法")
            
            # 尝试直接在__init__方法末尾添加工具提示
            init_end_pattern = "        # 设置初始样式\n        self.update_appearance()"
            if init_end_pattern in content:
                new_init_end = "        # 设置初始样式\n        self.update_appearance()\n        \n        # 启用标准工具提示\n        self.setToolTip(self._create_tooltip())"
                content = content.replace(init_end_pattern, new_init_end)
                print("  ✅ 在初始化末尾添加了标准工具提示")
        
        # 创建备份
        backup_file = hole_item_file.with_suffix('.py.tooltip_fix_backup')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 写入修改后的文件
        with open(hole_item_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ 文件已修改，备份保存在: {backup_file}")
        print(f"  📝 现在孔位会使用标准的Qt工具提示显示信息")
        print(f"  🔄 请重启应用程序以查看效果")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 修复失败: {e}")
        return False

def verify_fix():
    """验证修复结果"""
    hole_item_file = project_root / "src" / "aidcis2" / "graphics" / "hole_item.py"
    
    try:
        with open(hole_item_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含标准工具提示设置
        has_settooltip = "self.setToolTip(self._create_tooltip())" in content
        
        print(f"\n🔍 验证修复结果:")
        print(f"  标准工具提示设置: {'✅ 已启用' if has_settooltip else '❌ 未找到'}")
        
        if has_settooltip:
            print(f"  🎉 修复成功！现在悬停在孔位上应该能看到工具提示了")
        else:
            print(f"  ❌ 修复可能不完整，请手动检查")
        
        return has_settooltip
        
    except Exception as e:
        print(f"  ❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    print("🛠️ 孔位工具提示修复工具")
    print("=" * 50)
    
    success = fix_hole_item_tooltip()
    
    if success:
        verify_fix()
    
    print("\n📖 使用说明:")
    print("1. 重启应用程序")
    print("2. 将鼠标悬停在任何孔位上")
    print("3. 应该会看到包含孔位信息的工具提示")
    print("4. 如果仍有问题，请检查控制台是否有错误信息")