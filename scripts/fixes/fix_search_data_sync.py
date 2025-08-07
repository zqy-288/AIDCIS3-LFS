#!/usr/bin/env python3
"""
搜索功能数据同步修复脚本
应用关键修复：确保孔位数据正确传递到搜索服务
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def apply_search_data_sync_fixes():
    """应用搜索数据同步修复"""
    print("🔧 应用搜索功能数据同步修复")
    print("=" * 60)
    
    fixes_applied = []
    
    # 修复1: 增强 MainDetectionPage._on_search_hole 方法
    print("\n1️⃣ 增强搜索处理方法...")
    
    main_page_file = project_root / "src/pages/main_detection_p1/main_detection_page.py"
    
    if main_page_file.exists():
        with open(main_page_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经有增强版的搜索方法
        if "coordinator.update_search_data()" in content:
            print("   ✅ 搜索方法已经包含数据更新逻辑")
        else:
            # 查找现有的_on_search_hole方法并增强
            old_method = '''def _on_search_hole(self, query):
        """处理搜索孔位"""
        try:
            self.logger.info(f"🔍 页面接收到搜索请求: {query}")
            
            # 使用控制器的搜索功能
            if self.controller and hasattr(self.controller, 'search_hole'):
                results = self.controller.search_hole(query)
                self.logger.info(f"✅ 页面搜索完成: {len(results)} 个结果")'''
            
            enhanced_method = '''def _on_search_hole(self, query):
        """处理搜索孔位 - 增强版"""
        try:
            self.logger.info(f"🔍 页面接收到搜索请求: {query}")
            
            # 检查并更新搜索数据
            if self.controller and hasattr(self.controller, 'business_coordinator'):
                coordinator = self.controller.business_coordinator
                if coordinator and hasattr(coordinator, 'update_search_data'):
                    coordinator.update_search_data()
                    self.logger.info("🔄 已更新搜索数据")
                    
                    # 调试：检查搜索服务数据状态
                    if coordinator._search_service and hasattr(coordinator._search_service, 'debug_search_data'):
                        debug_info = coordinator._search_service.debug_search_data()
                        self.logger.info(f"🔍 搜索数据状态: {debug_info}")
                        
                        # 如果没有数据，提示用户
                        if debug_info['total_holes'] == 0:
                            self.error_occurred.emit("请先加载DXF文件或选择产品")
                            self.logger.warning("⚠️ 搜索数据为空，请先加载数据")
                            return
            
            # 使用控制器的搜索功能
            if self.controller and hasattr(self.controller, 'search_hole'):
                results = self.controller.search_hole(query)
                self.logger.info(f"✅ 页面搜索完成: {len(results)} 个结果")
                
                # 用户反馈
                if results:
                    self.status_updated.emit(f"找到 {len(results)} 个匹配的孔位")
                    self.logger.info(f"📋 搜索结果: {results[:5]}{'...' if len(results) > 5 else ''}")
                else:
                    self.status_updated.emit(f"未找到匹配 '{query}' 的孔位")
                    self.logger.info(f"⚠️ 没有找到匹配 '{query}' 的孔位")'''
            
            if old_method in content:
                content = content.replace(old_method, enhanced_method)
                
                with open(main_page_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("   ✅ 已增强搜索处理方法")
                fixes_applied.append("增强搜索处理方法")
            else:
                print("   ⚠️ 未找到预期的搜索方法结构，请手动检查")
    else:
        print("   ❌ 主检测页面文件不存在")
    
    # 修复2: 确保文件加载后更新搜索数据
    print("\n2️⃣ 确保文件加载后更新搜索数据...")
    
    controller_file = project_root / "src/pages/main_detection_p1/controllers/main_window_controller.py"
    
    if controller_file.exists():
        with open(controller_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查_on_file_loaded方法
        if "coordinator.update_search_data()" in content:
            print("   ✅ 文件加载方法已包含搜索数据更新")
        else:
            # 查找_on_file_loaded方法并增强
            old_method = '''def _on_file_loaded(self, file_path):
        """文件加载完成处理"""
        self.logger.info(f"DXF文件加载完成: {file_path}")
        # 转发信号
        self.file_loaded.emit(file_path)
        # 更新图形视图
        self._update_graphics_view()'''
        
            enhanced_method = '''def _on_file_loaded(self, file_path):
        """文件加载完成处理 - 确保搜索数据同步"""
        self.logger.info(f"DXF文件加载完成: {file_path}")
        
        # 立即更新搜索数据
        if hasattr(self, 'business_coordinator') and self.business_coordinator:
            self.business_coordinator.update_search_data()
            self.logger.info("🔍 搜索数据已同步")
        
        # 转发信号
        self.file_loaded.emit(file_path)
        # 更新图形视图
        self._update_graphics_view()'''
        
            if old_method in content:
                content = content.replace(old_method, enhanced_method)
                
                with open(controller_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("   ✅ 已增强文件加载处理方法")
                fixes_applied.append("增强文件加载处理")
            else:
                print("   ⚠️ 未找到预期的文件加载方法结构")
    else:
        print("   ❌ 控制器文件不存在")
    
    # 修复3: 在业务协调器中确保加载产品后更新搜索数据
    print("\n3️⃣ 确保产品加载后更新搜索数据...")
    
    coordinator_file = project_root / "src/shared/services/business_coordinator.py"
    
    if coordinator_file.exists():
        with open(coordinator_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查load_product方法是否已包含搜索数据更新
        if "# Update search service with hole collection data after product selection" in content:
            print("   ✅ 产品加载方法已包含搜索数据更新")
        else:
            print("   ⚠️ 产品加载方法可能需要手动检查")
    else:
        print("   ❌ 业务协调器文件不存在")
    
    # 修复4: 添加工具栏搜索结果反馈
    print("\n4️⃣ 添加工具栏搜索结果反馈...")
    
    toolbar_file = project_root / "src/pages/main_detection_p1/ui/components/toolbar_component.py"
    
    if toolbar_file.exists():
        with open(toolbar_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有set_search_results_count方法
        if "set_search_results_count" in content:
            print("   ✅ 工具栏已包含搜索结果反馈方法")
        else:
            # 在文件末尾添加方法（在最后一个方法后）
            new_method = '''
    def set_search_results_count(self, count: int) -> None:
        """
        更新搜索结果数量显示
        
        Args:
            count: 搜索结果数量
        """
        if self.search_input:
            if count > 0:
                self.search_input.setPlaceholderText(f"找到 {count} 个结果...")
            else:
                self.search_input.setPlaceholderText("无匹配结果，请尝试其他关键词...")
    
    def clear_search_results_feedback(self) -> None:
        """清除搜索结果反馈"""
        if self.search_input:
            self.search_input.setPlaceholderText("输入孔位ID...")'''
            
            # 在最后一个方法后添加新方法
            if "def set_search_results_count" not in content:
                # 找到最后一个方法的位置
                import re
                
                # 查找最后一个缩进的方法定义
                last_method_match = None
                for match in re.finditer(r'    def [^_].*?(?=\n    def|\n\n|\Z)', content, re.DOTALL):
                    last_method_match = match
                
                if last_method_match:
                    insert_pos = last_method_match.end()
                    content = content[:insert_pos] + new_method + content[insert_pos:]
                    
                    with open(toolbar_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print("   ✅ 已添加搜索结果反馈方法")
                    fixes_applied.append("添加搜索结果反馈")
                else:
                    print("   ⚠️ 无法确定插入位置，请手动添加")
    else:
        print("   ❌ 工具栏组件文件不存在")
    
    # 总结
    print("\n" + "=" * 60)
    print("🎯 修复总结")
    print("=" * 60)
    
    if fixes_applied:
        print("✅ 已应用的修复:")
        for fix in fixes_applied:
            print(f"   - {fix}")
        print(f"\n总计应用了 {len(fixes_applied)} 个修复")
    else:
        print("⚠️ 没有应用任何修复，可能文件已经是最新版本")
    
    print("\n📋 后续步骤:")
    print("1. 重启应用程序")
    print("2. 加载DXF文件或选择产品")
    print("3. 测试搜索功能")
    print("4. 检查日志输出确认数据同步")

if __name__ == "__main__":
    apply_search_data_sync_fixes()