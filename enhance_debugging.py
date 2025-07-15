#!/usr/bin/env python3
"""
增强调试信息 - 分析模拟状态检测和数据更新问题
"""

from pathlib import Path

def enhance_debugging():
    """增强调试信息"""
    
    print("🔧 增强调试信息")
    print("=" * 60)
    
    # 1. 增强模拟状态检测调试
    enhance_simulation_status_debugging()
    
    # 2. 增强数据更新流程调试
    enhance_update_flow_debugging()
    
    # 3. 增强tooltip显示调试
    enhance_tooltip_debugging()
    
    print("\n✅ 调试信息增强完成！")

def enhance_simulation_status_debugging():
    """增强模拟状态检测的调试信息"""
    
    print("\n1. 增强模拟状态检测调试:")
    
    dynamic_sector_file = Path(__file__).parent / "src" / "aidcis2" / "graphics" / "dynamic_sector_view.py"
    
    with open(dynamic_sector_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 增强 _check_simulation_status 方法的调试
    old_check_method = '''    def _check_simulation_status(self) -> bool:
        """检查当前是否在模拟期间"""
        try:
            # 通过parent找到主窗口检查模拟状态
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'simulation_running'):
                main_window = main_window.parent()
            
            if main_window:
                simulation_v1 = getattr(main_window, 'simulation_running', False)
                simulation_v2 = getattr(main_window, 'simulation_running_v2', False)
                is_running = simulation_v1 or simulation_v2
                if is_running:
                    print(f"🎯 [全景图] 检测到模拟运行中: V1={simulation_v1}, V2={simulation_v2}")
                return is_running
            else:
                print(f"⚠️ [全景图] 无法找到主窗口，假设非模拟期间")
                return False
        except Exception as e:
            print(f"❌ [全景图] 模拟状态检查失败: {e}")
            return False'''
    
    new_check_method = '''    def _check_simulation_status(self) -> bool:
        """检查当前是否在模拟期间"""
        print(f"🔍 [调试] 开始检查模拟状态...")
        
        try:
            # 通过parent找到主窗口检查模拟状态
            main_window = self.parent()
            parent_chain = []
            while main_window:
                parent_chain.append(type(main_window).__name__)
                if hasattr(main_window, 'simulation_running'):
                    break
                main_window = main_window.parent()
            
            print(f"🔍 [调试] 父级链路: {' -> '.join(parent_chain)}")
            
            if main_window:
                simulation_v1 = getattr(main_window, 'simulation_running', False)
                simulation_v2 = getattr(main_window, 'simulation_running_v2', False)
                is_running = simulation_v1 or simulation_v2
                
                print(f"🔍 [调试] 主窗口类型: {type(main_window).__name__}")
                print(f"🔍 [调试] simulation_running (V1): {simulation_v1}")
                print(f"🔍 [调试] simulation_running_v2 (V2): {simulation_v2}")
                print(f"🔍 [调试] 最终模拟状态: {is_running}")
                
                if is_running:
                    print(f"🎯 [全景图] 检测到模拟运行中: V1={simulation_v1}, V2={simulation_v2}")
                else:
                    print(f"⏸️ [全景图] 模拟未运行: V1={simulation_v1}, V2={simulation_v2}")
                    
                return is_running
            else:
                print(f"⚠️ [全景图] 无法找到主窗口，假设非模拟期间")
                print(f"🔍 [调试] 完整父级链路: {' -> '.join(parent_chain) if parent_chain else '无父级'}")
                return False
        except Exception as e:
            print(f"❌ [全景图] 模拟状态检查失败: {e}")
            import traceback
            traceback.print_exc()
            return False'''
    
    if old_check_method in content:
        content = content.replace(old_check_method, new_check_method)
        print("  ✅ 已增强 _check_simulation_status 调试信息")
    else:
        print("  ⚠️ 未找到 _check_simulation_status 方法")

    # 增强 update_hole_status 方法的调试
    old_update_method = '''    def update_hole_status(self, hole_id: str, status):
        """更新孔位状态（智能批量/实时更新版本）"""
        print(f"📦 [全景图] 接收到状态更新: {hole_id} -> {status.value if hasattr(status, 'value') else status}")
        
        # 检查是否在模拟期间
        is_simulation_running = self._check_simulation_status()'''
    
    new_update_method = '''    def update_hole_status(self, hole_id: str, status):
        """更新孔位状态（智能批量/实时更新版本）"""
        print(f"📦 [全景图] 接收到状态更新: {hole_id} -> {status.value if hasattr(status, 'value') else status}")
        print(f"🔍 [调试] 当前时间: {__import__('datetime').datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        
        # 检查是否在模拟期间
        print(f"🔍 [调试] 开始检查模拟状态...")
        is_simulation_running = self._check_simulation_status()
        print(f"🔍 [调试] 模拟状态检查结果: {is_simulation_running}")'''
    
    if old_update_method in content:
        content = content.replace(old_update_method, new_update_method)
        print("  ✅ 已增强 update_hole_status 调试信息")
    else:
        print("  ⚠️ 未找到 update_hole_status 方法")
    
    # 写入文件
    with open(dynamic_sector_file, 'w', encoding='utf-8') as f:
        f.write(content)

def enhance_update_flow_debugging():
    """增强数据更新流程的调试信息"""
    
    print("\n2. 增强数据更新流程调试:")
    
    main_window_file = Path(__file__).parent / "src" / "main_window.py"
    
    with open(main_window_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在模拟更新处添加调试信息
    old_status_update = '''            # 更新孔位数据状态
            if status_text == "合格":
                current_hole.status = HoleStatus.QUALIFIED
            elif status_text == "异常":
                current_hole.status = HoleStatus.DEFECTIVE
            elif status_text == "盲孔":
                current_hole.status = HoleStatus.BLIND
            elif status_text == "拉杆孔":
                current_hole.status = HoleStatus.TIE_ROD'''
    
    new_status_update = '''            # 更新孔位数据状态
            print(f"🔍 [调试-数据更新] 孔位 {hole_id} 状态更新前: {current_hole.status.value if hasattr(current_hole.status, 'value') else current_hole.status}")
            
            if status_text == "合格":
                current_hole.status = HoleStatus.QUALIFIED
            elif status_text == "异常":
                current_hole.status = HoleStatus.DEFECTIVE
            elif status_text == "盲孔":
                current_hole.status = HoleStatus.BLIND
            elif status_text == "拉杆孔":
                current_hole.status = HoleStatus.TIE_ROD
                
            print(f"✅ [调试-数据更新] 孔位 {hole_id} 状态更新后: {current_hole.status.value}")
            print(f"🔍 [调试-数据更新] 数据对象ID: {id(current_hole)}")'''
    
    if old_status_update in content:
        content = content.replace(old_status_update, new_status_update)
        print("  ✅ 已增强数据状态更新调试信息")
    else:
        print("  ⚠️ 未找到数据状态更新代码")
    
    # 在全景图更新调用处添加调试
    old_panorama_update = '''            # 同步全景图状态更新 - 使用批量更新机制优化性能
            self._update_panorama_hole_status(hole_id, final_color)'''
    
    new_panorama_update = '''            # 同步全景图状态更新 - 使用批量更新机制优化性能
            print(f"🔍 [调试-全景更新] 准备更新全景图: {hole_id}, 颜色: {final_color.name()}")
            print(f"🔍 [调试-全景更新] 当前模拟状态: V1={getattr(self, 'simulation_running', False)}, V2={getattr(self, 'simulation_running_v2', False)}")
            self._update_panorama_hole_status(hole_id, final_color)
            print(f"✅ [调试-全景更新] 全景图更新调用完成")'''
    
    if old_panorama_update in content:
        content = content.replace(old_panorama_update, new_panorama_update)
        print("  ✅ 已增强全景图更新调试信息")
    else:
        print("  ⚠️ 未找到全景图更新代码")
    
    # 写入文件
    with open(main_window_file, 'w', encoding='utf-8') as f:
        f.write(content)

def enhance_tooltip_debugging():
    """增强tooltip显示的调试信息"""
    
    print("\n3. 增强tooltip调试:")
    
    hole_item_file = Path(__file__).parent / "src" / "aidcis2" / "graphics" / "hole_item.py"
    
    # 检查文件是否存在
    if not hole_item_file.exists():
        print("  ⚠️ hole_item.py 文件不存在，跳过tooltip调试增强")
        return
    
    with open(hole_item_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并增强 _create_tooltip 方法
    import re
    tooltip_method = re.search(r'def _create_tooltip\(self\):.*?return.*?\n', content, re.DOTALL)
    
    if tooltip_method:
        old_method = tooltip_method.group(0)
        
        # 在方法开始处添加调试信息
        new_method = old_method.replace(
            'def _create_tooltip(self):',
            '''def _create_tooltip(self):
        """创建工具提示内容"""
        print(f"🔍 [调试-Tooltip] 创建tooltip for {self.hole_data.hole_id}")
        print(f"🔍 [调试-Tooltip] 当前状态: {self.hole_data.status.value if hasattr(self.hole_data.status, 'value') else self.hole_data.status}")
        print(f"🔍 [调试-Tooltip] 数据对象ID: {id(self.hole_data)}")'''
        )
        
        content = content.replace(old_method, new_method)
        print("  ✅ 已增强 _create_tooltip 调试信息")
        
        # 写入文件
        with open(hole_item_file, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print("  ⚠️ 未找到 _create_tooltip 方法")

if __name__ == "__main__":
    enhance_debugging()
    
    print(f"\n🎯 调试增强完成！")
    print(f"\n📋 增强的调试信息包括:")
    print(f"  1. 模拟状态检测的详细日志")
    print(f"  2. 数据更新前后的状态对比")
    print(f"  3. 全景图更新调用的时序信息")
    print(f"  4. Tooltip创建时的数据状态")
    
    print(f"\n🔍 下次测试时请观察:")
    print(f"  1. 模拟状态检查是否正确识别")
    print(f"  2. 数据更新是否真的执行了")
    print(f"  3. 全景图更新是走实时还是批量路径")
    print(f"  4. Tooltip显示的数据是否是最新的")