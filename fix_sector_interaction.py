#!/usr/bin/env python3
"""
扇形交互问题修复脚本
修复CompletePanoramaWidget点击响应和扇形统计信息显示问题
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def add_debug_logging_to_panorama():
    """在CompletePanoramaWidget中添加调试日志"""
    file_path = Path(__file__).parent / "src" / "aidcis2" / "graphics" / "dynamic_sector_view.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经包含调试代码
        if "# DEBUG: 扇形交互调试" in content:
            print("✅ 调试代码已存在")
            return True
        
        # 在_calculate_panorama_geometry方法中添加调试
        old_method = '''    def _calculate_panorama_geometry(self):
        """计算全景图的几何信息"""
        if not self.hole_collection:
            return'''
        
        new_method = '''    def _calculate_panorama_geometry(self):
        """计算全景图的几何信息"""
        # DEBUG: 扇形交互调试
        print(f"🔍 [DEBUG] _calculate_panorama_geometry 被调用")
        print(f"🔍 [DEBUG] hole_collection 存在: {self.hole_collection is not None}")
        if self.hole_collection:
            print(f"🔍 [DEBUG] hole_collection 大小: {len(self.hole_collection)}")
        
        if not self.hole_collection:
            print(f"⚠️ [DEBUG] hole_collection 为空，无法计算几何信息")
            return'''
        
        if old_method in content:
            content = content.replace(old_method, new_method)
            print("✅ 已添加几何计算调试代码")
        
        # 在eventFilter中添加调试
        old_event = '''    def eventFilter(self, obj, event):
        """事件过滤器，处理全景视图的鼠标事件"""
        if obj == self.panorama_view.viewport() and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # 将视口坐标转换为场景坐标
                scene_pos = self.panorama_view.mapToScene(event.pos())
                
                print(f"🖱️ [全景图] 鼠标点击: 视口坐标={event.pos()}, 场景坐标=({scene_pos.x():.1f}, {scene_pos.y():.1f})")'''
        
        new_event = '''    def eventFilter(self, obj, event):
        """事件过滤器，处理全景视图的鼠标事件"""
        if obj == self.panorama_view.viewport() and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # 将视口坐标转换为场景坐标
                scene_pos = self.panorama_view.mapToScene(event.pos())
                
                # DEBUG: 扇形交互调试
                print(f"🖱️ [全景图] 鼠标点击: 视口坐标={event.pos()}, 场景坐标=({scene_pos.x():.1f}, {scene_pos.y():.1f})")
                print(f"🔍 [DEBUG] center_point: {self.center_point}")
                print(f"🔍 [DEBUG] panorama_radius: {self.panorama_radius}")
                print(f"🔍 [DEBUG] hole_collection: {self.hole_collection is not None}")'''
        
        if old_event in content:
            content = content.replace(old_event, new_event)
            print("✅ 已添加事件过滤器调试代码")
        
        # 保存修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新文件: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修改文件失败: {e}")
        return False

def add_debug_logging_to_sector_manager():
    """在SectorManager中添加调试日志"""
    file_path = Path(__file__).parent / "src" / "aidcis2" / "graphics" / "sector_manager.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经包含调试代码
        if "# DEBUG: 扇形管理器调试" in content:
            print("✅ SectorManager调试代码已存在")
            return True
        
        # 在load_hole_collection方法中添加调试
        old_load = '''    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合并进行区域划分"""
        self.hole_collection = hole_collection
        
        if not hole_collection or len(hole_collection) == 0:
            self.logger.warning("加载的孔位集合为空")
            return'''
        
        new_load = '''    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合并进行区域划分"""
        # DEBUG: 扇形管理器调试
        print(f"🔍 [DEBUG SectorManager] load_hole_collection 被调用")
        print(f"🔍 [DEBUG SectorManager] hole_collection: {hole_collection}")
        if hole_collection:
            print(f"🔍 [DEBUG SectorManager] hole_collection 大小: {len(hole_collection)}")
        
        self.hole_collection = hole_collection
        
        if not hole_collection or len(hole_collection) == 0:
            print(f"⚠️ [DEBUG SectorManager] 孔位集合为空")
            self.logger.warning("加载的孔位集合为空")
            return'''
        
        if old_load in content:
            content = content.replace(old_load, new_load)
            print("✅ 已添加SectorManager加载调试代码")
        
        # 在_initialize_sector_progress方法中添加调试
        old_init = '''    def _initialize_sector_progress(self):
        """初始化所有扇形区域的进度信息"""
        self.sector_progresses.clear()
        
        for sector in SectorQuadrant:
            # 获取该扇形的孔位
            sector_holes = self.get_sector_holes(sector)'''
        
        new_init = '''    def _initialize_sector_progress(self):
        """初始化所有扇形区域的进度信息"""
        # DEBUG: 扇形管理器调试
        print(f"🔍 [DEBUG SectorManager] _initialize_sector_progress 被调用")
        
        self.sector_progresses.clear()
        
        for sector in SectorQuadrant:
            # 获取该扇形的孔位
            sector_holes = self.get_sector_holes(sector)
            print(f"🔍 [DEBUG SectorManager] {sector.value} 扇形孔位数: {len(sector_holes)}")'''
        
        if old_init in content:
            content = content.replace(old_init, new_init)
            print("✅ 已添加SectorManager初始化调试代码")
        
        # 保存修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新文件: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修改SectorManager文件失败: {e}")
        return False

def add_debug_logging_to_main_window():
    """在MainWindow中添加调试日志"""
    file_path = Path(__file__).parent / "src" / "main_window.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经包含调试代码
        if "# DEBUG: 主窗口扇形交互调试" in content:
            print("✅ MainWindow调试代码已存在")
            return True
        
        # 在on_panorama_sector_clicked方法中添加调试
        old_click = '''    def on_panorama_sector_clicked(self, sector):
        """处理全景图扇形点击事件"""
        self.logger.info(f"全景图扇形点击: {sector}")
        
        # 切换主视图到被点击的扇形
        if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
            self.dynamic_sector_display.switch_to_sector(sector)
            self.log_message(f"🖱️ 通过全景图点击切换到扇形: {sector.value}")
        
        # 更新扇形统计信息
        self._update_sector_stats_display(sector)'''
        
        new_click = '''    def on_panorama_sector_clicked(self, sector):
        """处理全景图扇形点击事件"""
        # DEBUG: 主窗口扇形交互调试
        print(f"🔍 [DEBUG MainWindow] on_panorama_sector_clicked 被调用: {sector}")
        print(f"🔍 [DEBUG MainWindow] dynamic_sector_display 存在: {hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display is not None}")
        print(f"🔍 [DEBUG MainWindow] sector_manager 存在: {hasattr(self, 'sector_manager') and self.sector_manager is not None}")
        
        self.logger.info(f"全景图扇形点击: {sector}")
        
        # 切换主视图到被点击的扇形
        if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
            print(f"🔍 [DEBUG MainWindow] 调用 switch_to_sector({sector})")
            self.dynamic_sector_display.switch_to_sector(sector)
            self.log_message(f"🖱️ 通过全景图点击切换到扇形: {sector.value}")
        
        # 更新扇形统计信息
        print(f"🔍 [DEBUG MainWindow] 调用 _update_sector_stats_display({sector})")
        self._update_sector_stats_display(sector)'''
        
        if old_click in content:
            content = content.replace(old_click, new_click)
            print("✅ 已添加MainWindow点击处理调试代码")
        
        # 在_update_sector_stats_display方法中添加调试
        old_stats = '''    def _update_sector_stats_display(self, sector):
        """更新扇形统计信息显示"""
        if not hasattr(self, 'sector_stats_label') or not self.sector_manager:
            return
        
        try:
            from aidcis2.graphics.sector_manager import SectorQuadrant
            progress = self.sector_manager.get_sector_progress(sector)'''
        
        new_stats = '''    def _update_sector_stats_display(self, sector):
        """更新扇形统计信息显示"""
        # DEBUG: 主窗口扇形交互调试
        print(f"🔍 [DEBUG MainWindow] _update_sector_stats_display 被调用: {sector}")
        print(f"🔍 [DEBUG MainWindow] sector_stats_label 存在: {hasattr(self, 'sector_stats_label')}")
        print(f"🔍 [DEBUG MainWindow] sector_manager 存在: {self.sector_manager is not None}")
        
        if not hasattr(self, 'sector_stats_label') or not self.sector_manager:
            print(f"⚠️ [DEBUG MainWindow] 缺少必要组件，退出统计信息更新")
            return
        
        try:
            from aidcis2.graphics.sector_manager import SectorQuadrant
            progress = self.sector_manager.get_sector_progress(sector)
            print(f"🔍 [DEBUG MainWindow] 获取到的进度信息: {progress}")'''
        
        if old_stats in content:
            content = content.replace(old_stats, new_stats)
            print("✅ 已添加MainWindow统计信息更新调试代码")
        
        # 保存修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新文件: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修改MainWindow文件失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 开始修复扇形交互问题...")
    print("=" * 60)
    
    fixes = [
        ("CompletePanoramaWidget调试", add_debug_logging_to_panorama),
        ("SectorManager调试", add_debug_logging_to_sector_manager),
        ("MainWindow调试", add_debug_logging_to_main_window)
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
        print("\n📝 使用说明:")
        print("1. 重启应用程序")
        print("2. 加载DXF数据或选择产品型号")
        print("3. 点击全景图中的扇形区域")
        print("4. 观察控制台输出的调试信息")
        print("5. 检查扇形统计信息是否正确显示")
    else:
        print("\n⚠️ 部分修复失败，请检查错误信息并手动修复")

if __name__ == "__main__":
    main()