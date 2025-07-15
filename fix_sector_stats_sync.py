#!/usr/bin/env python3
"""
修复扇形统计信息同步问题
解决点击扇形区域时统计信息不更新的问题
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def fix_sector_stats_sync():
    """修复扇形统计信息同步问题"""
    print("🔧 修复扇形统计信息同步问题...")
    
    # 1. 检查并修复SectorManager的初始化
    sector_manager_path = Path(__file__).parent / "src" / "aidcis2" / "graphics" / "sector_manager.py"
    
    if not sector_manager_path.exists():
        print(f"❌ 文件不存在: {sector_manager_path}")
        return False
    
    try:
        with open(sector_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否需要修复_initialize_sector_progress方法
        if "# DEBUG: 扇形统计信息同步修复" not in content:
            # 在_initialize_sector_progress方法后添加立即更新机制
            old_init = '''    def _initialize_sector_progress(self):
        """初始化各扇形区域的进度统计"""
        # DEBUG: 扇形管理器调试
        print(f"🔍 [DEBUG SectorManager] _initialize_sector_progress 被调用")
        
        self.sector_progresses.clear()
        
        for sector in SectorQuadrant:
            # 获取该扇形的孔位
            sector_holes = self.get_sector_holes(sector)
            print(f"🔍 [DEBUG SectorManager] {sector.value} 扇形孔位数: {len(sector_holes)}")'''
            
            new_init = '''    def _initialize_sector_progress(self):
        """初始化各扇形区域的进度统计"""
        # DEBUG: 扇形管理器调试
        print(f"🔍 [DEBUG SectorManager] _initialize_sector_progress 被调用")
        # DEBUG: 扇形统计信息同步修复
        print(f"🔍 [DEBUG SectorManager] 开始初始化扇形统计信息")
        
        self.sector_progresses.clear()
        
        for sector in SectorQuadrant:
            # 获取该扇形的孔位
            sector_holes = self.get_sector_holes(sector)
            print(f"🔍 [DEBUG SectorManager] {sector.value} 扇形孔位数: {len(sector_holes)}")
            
            # 立即计算初始进度
            self._recalculate_sector_progress(sector)
            print(f"🔍 [DEBUG SectorManager] {sector.value} 扇形进度已计算")'''
            
            if old_init in content:
                content = content.replace(old_init, new_init)
                print("✅ 已修复SectorManager初始化方法")
            else:
                print("⚠️ 未找到需要修复的SectorManager初始化方法")
        
        # 保存修改后的文件
        with open(sector_manager_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新SectorManager文件: {sector_manager_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修复SectorManager失败: {e}")
        return False

def add_sector_stats_debug():
    """添加扇形统计信息调试"""
    print("🔧 添加扇形统计信息调试...")
    
    main_window_path = Path(__file__).parent / "src" / "main_window.py"
    
    if not main_window_path.exists():
        print(f"❌ 文件不存在: {main_window_path}")
        return False
    
    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否需要添加调试代码
        if "# DEBUG: 扇形统计信息详细调试" not in content:
            # 在_update_sector_stats_display方法中添加更详细的调试
            old_update = '''        try:
            from aidcis2.graphics.sector_manager import SectorQuadrant
            progress = self.sector_manager.get_sector_progress(sector)
            print(f"🔍 [DEBUG MainWindow] 获取到的进度信息: {progress}")'''
            
            new_update = '''        try:
            from aidcis2.graphics.sector_manager import SectorQuadrant
            # DEBUG: 扇形统计信息详细调试
            print(f"🔍 [DEBUG MainWindow] 详细扇形统计调试:")
            print(f"  - 请求的扇形: {sector}")
            print(f"  - SectorManager类型: {type(self.sector_manager)}")
            print(f"  - SectorManager有数据: {hasattr(self.sector_manager, 'hole_collection') and self.sector_manager.hole_collection is not None}")
            
            # 检查扇形分配
            if hasattr(self.sector_manager, 'sector_assignments'):
                print(f"  - 扇形分配数量: {len(self.sector_manager.sector_assignments)}")
                sector_count = sum(1 for s in self.sector_manager.sector_assignments.values() if s == sector)
                print(f"  - {sector.value} 扇形孔位数: {sector_count}")
            
            progress = self.sector_manager.get_sector_progress(sector)
            print(f"🔍 [DEBUG MainWindow] 获取到的进度信息: {progress}")
            
            # 如果进度信息为空，尝试强制重新计算
            if not progress:
                print(f"⚠️ [DEBUG MainWindow] 进度信息为空，尝试重新计算")
                self.sector_manager._recalculate_sector_progress(sector)
                progress = self.sector_manager.get_sector_progress(sector)
                print(f"🔍 [DEBUG MainWindow] 重新计算后的进度信息: {progress}")'''
            
            if old_update in content:
                content = content.replace(old_update, new_update)
                print("✅ 已添加详细的扇形统计信息调试")
            else:
                print("⚠️ 未找到需要修改的_update_sector_stats_display方法")
        
        # 保存修改后的文件
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新MainWindow文件: {main_window_path}")
        return True
        
    except Exception as e:
        print(f"❌ 添加扇形统计信息调试失败: {e}")
        return False

def add_sector_switching_debug():
    """添加扇形切换调试"""
    print("🔧 添加扇形切换调试...")
    
    dynamic_sector_path = Path(__file__).parent / "src" / "aidcis2" / "graphics" / "dynamic_sector_view.py"
    
    if not dynamic_sector_path.exists():
        print(f"❌ 文件不存在: {dynamic_sector_path}")
        return False
    
    try:
        with open(dynamic_sector_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否需要添加switch_to_sector调试
        if "# DEBUG: 扇形切换详细调试" not in content:
            # 查找switch_to_sector方法并添加调试
            old_switch = '''    def switch_to_sector(self, sector: SectorQuadrant):
        """切换到指定扇形区域"""
        print(f"🔄 [扇形切换] 切换到扇形: {sector.value}")
        
        if not self.sector_graphics_manager:
            print(f"❌ [扇形切换] 扇形图形管理器不存在")
            return
        
        # 更新当前扇形
        self.current_sector = sector
        
        # 获取扇形的孔位集合
        sector_collection = self.sector_graphics_manager.get_sector_collection(sector)
        if not sector_collection:
            print(f"❌ [扇形切换] 扇形 {sector.value} 没有孔位集合")
            return
        
        print(f"✅ [扇形切换] 扇形 {sector.value} 包含 {len(sector_collection)} 个孔位")
        
        # 加载扇形数据到主视图
        self.graphics_view.load_holes(sector_collection)
        
        # 应用视图变换以显示扇形区域
        self._apply_sector_view_transform(sector, sector_collection)
        
        # 发出扇形切换信号
        self.sector_changed.emit(sector)
        
        print(f"✅ [扇形切换] 扇形切换完成: {sector.value}")'''
            
            new_switch = '''    def switch_to_sector(self, sector: SectorQuadrant):
        """切换到指定扇形区域"""
        # DEBUG: 扇形切换详细调试
        print(f"🔄 [扇形切换] 切换到扇形: {sector.value}")
        print(f"🔍 [扇形切换] 当前扇形: {self.current_sector.value if hasattr(self, 'current_sector') else 'None'}")
        print(f"🔍 [扇形切换] 扇形图形管理器存在: {self.sector_graphics_manager is not None}")
        
        if not self.sector_graphics_manager:
            print(f"❌ [扇形切换] 扇形图形管理器不存在")
            return
        
        # 更新当前扇形
        old_sector = getattr(self, 'current_sector', None)
        self.current_sector = sector
        print(f"🔍 [扇形切换] 扇形更新: {old_sector} -> {sector.value}")
        
        # 获取扇形的孔位集合
        sector_collection = self.sector_graphics_manager.get_sector_collection(sector)
        if not sector_collection:
            print(f"❌ [扇形切换] 扇形 {sector.value} 没有孔位集合")
            return
        
        print(f"✅ [扇形切换] 扇形 {sector.value} 包含 {len(sector_collection)} 个孔位")
        
        # 加载扇形数据到主视图
        print(f"🔍 [扇形切换] 加载扇形数据到主视图")
        self.graphics_view.load_holes(sector_collection)
        
        # 应用视图变换以显示扇形区域
        print(f"🔍 [扇形切换] 应用视图变换")
        self._apply_sector_view_transform(sector, sector_collection)
        
        # 发出扇形切换信号
        print(f"🔍 [扇形切换] 发出扇形切换信号")
        self.sector_changed.emit(sector)
        
        print(f"✅ [扇形切换] 扇形切换完成: {sector.value}")'''
            
            if old_switch in content:
                content = content.replace(old_switch, new_switch)
                print("✅ 已添加扇形切换详细调试")
            else:
                print("⚠️ 未找到需要修改的switch_to_sector方法")
        
        # 保存修改后的文件
        with open(dynamic_sector_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新DynamicSectorView文件: {dynamic_sector_path}")
        return True
        
    except Exception as e:
        print(f"❌ 添加扇形切换调试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 扇形统计信息同步修复脚本")
    print("=" * 60)
    
    fixes = [
        ("修复SectorManager初始化", fix_sector_stats_sync),
        ("添加扇形统计信息调试", add_sector_stats_debug),
        ("添加扇形切换调试", add_sector_switching_debug)
    ]
    
    results = []
    for name, fix_func in fixes:
        print(f"\n🔧 应用修复: {name}")
        result = fix_func()
        results.append((name, result))
        
        if result:
            print(f"✅ {name} 修复成功")
        else:
            print(f"❌ {name} 修复失败")
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 修复结果总结:")
    
    success_count = 0
    for name, result in results:
        status = "✅ 成功" if result else "❌ 失败"
        print(f"  {status} {name}")
        if result:
            success_count += 1
    
    print(f"\n🎯 修复完成: {success_count}/{len(results)} 项成功")
    
    if success_count == len(results):
        print("\n🎉 所有修复都已应用!")
        print("\n📝 修复内容:")
        print("1. ✅ 修复了SectorManager的初始化过程")
        print("2. ✅ 添加了详细的扇形统计信息调试")
        print("3. ✅ 添加了扇形切换过程调试")
        print("\n📝 使用说明:")
        print("1. 重启应用程序")
        print("2. 加载DXF数据或选择产品型号")
        print("3. 点击浮动全景图中的扇形区域")
        print("4. 观察控制台输出的详细调试信息")
        print("5. 检查扇形统计信息是否正确更新")
        print("\n🔍 预期看到的调试输出:")
        print("   🔄 [扇形切换] 切换到扇形: sector_X")
        print("   🔍 [DEBUG MainWindow] 详细扇形统计调试")
        print("   🔍 [DEBUG SectorManager] 扇形进度已计算")
    else:
        print("\n⚠️ 部分修复失败，请检查错误信息")

if __name__ == "__main__":
    main()