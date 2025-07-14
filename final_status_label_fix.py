#!/usr/bin/env python3
"""
修复状态标签不隐藏的问题
"""

import re

def fix_status_label_hide():
    """确保加载DXF后隐藏状态提示标签"""
    print("🔧 修复状态标签隐藏...")
    
    filepath = "src/main_window.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在load_dxf_from_product方法的成功加载部分添加隐藏逻辑
    # 查找设置标签文本的地方
    pattern = r'(self\.sidebar_panorama\.update_from_hole_collection\(hole_collection\))'
    replacement = r'''\1
                
                # 隐藏提示信息标签
                if hasattr(self.sidebar_panorama, 'info_label') and self.sidebar_panorama.info_label:
                    self.sidebar_panorama.info_label.hide()
                    self.log_message("✅ 隐藏状态提示标签")'''
    
    content = re.sub(pattern, replacement, content)
    
    # 同时在DXF解析成功的地方确保标签隐藏
    pattern2 = r'(self\.statusBar\(\)\.showMessage\(f"已加载: \{dxf_file_path\}[^"]+"\))'
    replacement2 = r'''\1
                
                # 确保隐藏提示标签
                if hasattr(self, 'sidebar_panorama') and self.sidebar_panorama:
                    if hasattr(self.sidebar_panorama, 'info_label') and self.sidebar_panorama.info_label:
                        self.sidebar_panorama.info_label.hide()'''
    
    content = re.sub(pattern2, replacement2, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 状态标签隐藏修复完成")

def fix_layout_proportions():
    """修复布局比例问题"""
    print("\n🔧 修复布局比例...")
    
    filepath = "src/main_window.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找main_splitter的创建位置
    # 在添加widget之后设置比例
    pattern = r'(main_splitter\.addWidget\(main_content_widget\))'
    replacement = r'''\1
        
        # 设置分割器比例（侧边栏:主内容 = 1:3）
        main_splitter.setSizes([350, 1050])
        main_splitter.setStretchFactor(0, 0)  # 侧边栏固定
        main_splitter.setStretchFactor(1, 1)  # 主内容可伸缩'''
    
    content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 布局比例修复完成")

def verify_syntax():
    """验证语法"""
    import subprocess
    import sys
    
    print("\n🔍 验证语法...")
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', 'src/main_window.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ 语法验证通过")
        return True
    else:
        print("❌ 语法错误:")
        print(result.stderr)
        return False

def main():
    print("=" * 60)
    print("修复状态标签和布局问题")
    print("=" * 60)
    
    fix_status_label_hide()
    fix_layout_proportions()
    
    if verify_syntax():
        print("\n✅ 所有修复完成！")
        print("\n修复内容：")
        print("1. ✅ 加载DXF后自动隐藏状态提示标签")
        print("2. ✅ 优化侧边栏和主内容的布局比例")
    else:
        print("\n❌ 修复过程中出现语法错误，请检查")

if __name__ == "__main__":
    main()