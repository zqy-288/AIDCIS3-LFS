"""
事件类型常量定义
定义应用程序中所有事件类型的常量，用于EventBus通信
"""

from typing import Final


class EventTypes:
    """
    事件类型常量类
    
    定义应用程序中所有事件类型的字符串常量，用于EventBus的事件发布和订阅。
    按功能分类组织，便于管理和维护。
    """
    
    # ===================
    # UI导航事件 (Navigation Events)
    # ===================
    
    NAVIGATE_TO_TAB: Final[str] = "navigate_to_tab"
    """导航到指定选项卡"""
    
    NAVIGATE_TO_HOLE: Final[str] = "navigate_to_hole"
    """导航到指定孔位"""
    
    NAVIGATE_TO_REGION: Final[str] = "navigate_to_region"
    """导航到指定区域"""
    
    SWITCH_VIEW_MODE: Final[str] = "switch_view_mode"
    """切换视图模式（列表/网格/图形）"""
    
    # ===================
    # 数据操作事件 (Data Operation Events)
    # ===================
    
    DXF_FILE_LOADED: Final[str] = "dxf_file_loaded"
    """DXF文件加载完成"""
    
    DXF_PARSING_STARTED: Final[str] = "dxf_parsing_started"
    """DXF文件开始解析"""
    
    DXF_PARSING_PROGRESS: Final[str] = "dxf_parsing_progress"
    """DXF文件解析进度更新"""
    
    DXF_PARSING_COMPLETED: Final[str] = "dxf_parsing_completed"
    """DXF文件解析完成"""
    
    DXF_PARSING_ERROR: Final[str] = "dxf_parsing_error"
    """DXF文件解析错误"""
    
    HOLE_SELECTED: Final[str] = "hole_selected"
    """孔位被选中"""
    
    HOLE_DESELECTED: Final[str] = "hole_deselected"
    """孔位取消选中"""
    
    HOLE_DATA_UPDATED: Final[str] = "hole_data_updated"
    """孔位数据更新"""
    
    HOLE_STATUS_CHANGED: Final[str] = "hole_status_changed"
    """孔位状态变更"""
    
    WORKPIECE_LOADED: Final[str] = "workpiece_loaded"
    """工件加载完成"""
    
    WORKPIECE_UNLOADED: Final[str] = "workpiece_unloaded"
    """工件卸载"""
    
    DATA_EXPORT_STARTED: Final[str] = "data_export_started"
    """数据导出开始"""
    
    DATA_EXPORT_COMPLETED: Final[str] = "data_export_completed"
    """数据导出完成"""
    
    DATA_IMPORT_STARTED: Final[str] = "data_import_started"
    """数据导入开始"""
    
    DATA_IMPORT_COMPLETED: Final[str] = "data_import_completed"
    """数据导入完成"""
    
    # ===================
    # 检测流程事件 (Detection Process Events)
    # ===================
    
    DETECTION_STARTED: Final[str] = "detection_started"
    """检测流程开始"""
    
    DETECTION_PAUSED: Final[str] = "detection_paused"
    """检测流程暂停"""
    
    DETECTION_RESUMED: Final[str] = "detection_resumed"
    """检测流程恢复"""
    
    DETECTION_STOPPED: Final[str] = "detection_stopped"
    """检测流程停止"""
    
    DETECTION_COMPLETED: Final[str] = "detection_completed"
    """检测流程完成"""
    
    DETECTION_PROGRESS: Final[str] = "detection_progress"
    """检测进度更新"""
    
    DETECTION_ERROR: Final[str] = "detection_error"
    """检测过程出错"""
    
    HOLE_DETECTION_STARTED: Final[str] = "hole_detection_started"
    """单个孔位检测开始"""
    
    HOLE_DETECTION_COMPLETED: Final[str] = "hole_detection_completed"
    """单个孔位检测完成"""
    
    ALGORITHM_CHANGED: Final[str] = "algorithm_changed"
    """检测算法切换"""
    
    PARAMETERS_UPDATED: Final[str] = "parameters_updated"
    """检测参数更新"""
    
    # ===================
    # 视图更新事件 (View Update Events)
    # ===================
    
    VIEWPORT_CHANGED: Final[str] = "viewport_changed"
    """视口发生变化（缩放、平移等）"""
    
    VIEWPORT_ZOOM_CHANGED: Final[str] = "viewport_zoom_changed"
    """视口缩放变化"""
    
    VIEWPORT_PAN_CHANGED: Final[str] = "viewport_pan_changed"
    """视口平移变化"""
    
    VIEWPORT_SELECTION_CHANGED: Final[str] = "viewport_selection_changed"
    """视口选择变化"""
    
    SIDEBAR_UPDATED: Final[str] = "sidebar_updated"
    """侧边栏更新"""
    
    SIDEBAR_PANEL_TOGGLED: Final[str] = "sidebar_panel_toggled"
    """侧边栏面板切换"""
    
    FILTER_CHANGED: Final[str] = "filter_changed"
    """过滤器条件变化"""
    
    SORT_ORDER_CHANGED: Final[str] = "sort_order_changed"
    """排序方式变化"""
    
    DISPLAY_MODE_CHANGED: Final[str] = "display_mode_changed"
    """显示模式变化"""
    
    THEME_CHANGED: Final[str] = "theme_changed"
    """主题变化"""
    
    # ===================
    # 实时预览事件 (Real-time Preview Events)
    # ===================
    
    REALTIME_PREVIEW_STARTED: Final[str] = "realtime_preview_started"
    """实时预览开始"""
    
    REALTIME_PREVIEW_STOPPED: Final[str] = "realtime_preview_stopped"
    """实时预览停止"""
    
    REALTIME_DATA_UPDATED: Final[str] = "realtime_data_updated"
    """实时数据更新"""
    
    CAMERA_CONNECTED: Final[str] = "camera_connected"
    """摄像头连接"""
    
    CAMERA_DISCONNECTED: Final[str] = "camera_disconnected"
    """摄像头断开"""
    
    FRAME_CAPTURED: Final[str] = "frame_captured"
    """帧捕获"""
    
    # ===================
    # 报告生成事件 (Report Generation Events)
    # ===================
    
    REPORT_GENERATION_STARTED: Final[str] = "report_generation_started"
    """报告生成开始"""
    
    REPORT_GENERATION_COMPLETED: Final[str] = "report_generation_completed"
    """报告生成完成"""
    
    REPORT_GENERATION_FAILED: Final[str] = "report_generation_failed"
    """报告生成失败"""
    
    REPORT_TEMPLATE_CHANGED: Final[str] = "report_template_changed"
    """报告模板变更"""
    
    REPORT_EXPORTED: Final[str] = "report_exported"
    """报告导出"""
    
    # ===================
    # 系统事件 (System Events)
    # ===================
    
    APPLICATION_READY: Final[str] = "application_ready"
    """应用程序准备就绪"""
    
    APPLICATION_CLOSING: Final[str] = "application_closing"
    """应用程序关闭"""
    
    SETTINGS_CHANGED: Final[str] = "settings_changed"
    """设置变更"""
    
    CONFIGURATION_LOADED: Final[str] = "configuration_loaded"
    """配置加载"""
    
    CONFIGURATION_SAVED: Final[str] = "configuration_saved"
    """配置保存"""
    
    PLUGIN_LOADED: Final[str] = "plugin_loaded"
    """插件加载"""
    
    PLUGIN_UNLOADED: Final[str] = "plugin_unloaded"
    """插件卸载"""
    
    DATABASE_CONNECTED: Final[str] = "database_connected"
    """数据库连接"""
    
    DATABASE_DISCONNECTED: Final[str] = "database_disconnected"
    """数据库断开"""
    
    ERROR_OCCURRED: Final[str] = "error_occurred"
    """错误发生"""
    
    WARNING_OCCURRED: Final[str] = "warning_occurred"
    """警告发生"""
    
    INFO_MESSAGE: Final[str] = "info_message"
    """信息消息"""
    
    STATUS_MESSAGE: Final[str] = "status_message"
    """状态消息"""
    
    PROGRESS_UPDATE: Final[str] = "progress_update"
    """进度更新"""
    
    # ===================
    # 历史记录事件 (History Events)
    # ===================
    
    HISTORY_RECORD_ADDED: Final[str] = "history_record_added"
    """历史记录添加"""
    
    HISTORY_RECORD_UPDATED: Final[str] = "history_record_updated"
    """历史记录更新"""
    
    HISTORY_RECORD_DELETED: Final[str] = "history_record_deleted"
    """历史记录删除"""
    
    HISTORY_FILTER_CHANGED: Final[str] = "history_filter_changed"
    """历史记录过滤器变化"""
    
    HISTORY_EXPORT_STARTED: Final[str] = "history_export_started"
    """历史记录导出开始"""
    
    HISTORY_EXPORT_COMPLETED: Final[str] = "history_export_completed"
    """历史记录导出完成"""
    
    @classmethod
    def get_all_events(cls) -> list[str]:
        """
        获取所有事件类型列表
        
        Returns:
            list[str]: 所有事件类型常量的列表
        """
        return [
            value for name, value in cls.__dict__.items()
            if isinstance(value, str) and not name.startswith('_')
        ]
    
    @classmethod
    def get_events_by_category(cls, category: str) -> list[str]:
        """
        根据分类获取事件类型列表
        
        Args:
            category: 事件分类（navigation, data, detection, view, system等）
            
        Returns:
            list[str]: 指定分类的事件类型列表
        """
        category_mapping = {
            'navigation': [
                cls.NAVIGATE_TO_TAB, cls.NAVIGATE_TO_HOLE, cls.NAVIGATE_TO_REGION,
                cls.SWITCH_VIEW_MODE
            ],
            'data': [
                cls.DXF_FILE_LOADED, cls.DXF_PARSING_STARTED, cls.DXF_PARSING_PROGRESS,
                cls.DXF_PARSING_COMPLETED, cls.DXF_PARSING_ERROR, cls.HOLE_SELECTED,
                cls.HOLE_DESELECTED, cls.HOLE_DATA_UPDATED, cls.HOLE_STATUS_CHANGED,
                cls.WORKPIECE_LOADED, cls.WORKPIECE_UNLOADED, cls.DATA_EXPORT_STARTED,
                cls.DATA_EXPORT_COMPLETED, cls.DATA_IMPORT_STARTED, cls.DATA_IMPORT_COMPLETED
            ],
            'detection': [
                cls.DETECTION_STARTED, cls.DETECTION_PAUSED, cls.DETECTION_RESUMED,
                cls.DETECTION_STOPPED, cls.DETECTION_COMPLETED, cls.DETECTION_PROGRESS,
                cls.DETECTION_ERROR, cls.HOLE_DETECTION_STARTED, cls.HOLE_DETECTION_COMPLETED,
                cls.ALGORITHM_CHANGED, cls.PARAMETERS_UPDATED
            ],
            'view': [
                cls.VIEWPORT_CHANGED, cls.VIEWPORT_ZOOM_CHANGED, cls.VIEWPORT_PAN_CHANGED,
                cls.VIEWPORT_SELECTION_CHANGED, cls.SIDEBAR_UPDATED, cls.SIDEBAR_PANEL_TOGGLED,
                cls.FILTER_CHANGED, cls.SORT_ORDER_CHANGED, cls.DISPLAY_MODE_CHANGED,
                cls.THEME_CHANGED
            ],
            'realtime': [
                cls.REALTIME_PREVIEW_STARTED, cls.REALTIME_PREVIEW_STOPPED,
                cls.REALTIME_DATA_UPDATED, cls.CAMERA_CONNECTED, cls.CAMERA_DISCONNECTED,
                cls.FRAME_CAPTURED
            ],
            'report': [
                cls.REPORT_GENERATION_STARTED, cls.REPORT_GENERATION_COMPLETED,
                cls.REPORT_GENERATION_FAILED, cls.REPORT_TEMPLATE_CHANGED,
                cls.REPORT_EXPORTED
            ],
            'system': [
                cls.APPLICATION_READY, cls.APPLICATION_CLOSING, cls.SETTINGS_CHANGED,
                cls.CONFIGURATION_LOADED, cls.CONFIGURATION_SAVED, cls.PLUGIN_LOADED,
                cls.PLUGIN_UNLOADED, cls.DATABASE_CONNECTED, cls.DATABASE_DISCONNECTED,
                cls.ERROR_OCCURRED, cls.WARNING_OCCURRED, cls.INFO_MESSAGE,
                cls.STATUS_MESSAGE, cls.PROGRESS_UPDATE
            ],
            'history': [
                cls.HISTORY_RECORD_ADDED, cls.HISTORY_RECORD_UPDATED,
                cls.HISTORY_RECORD_DELETED, cls.HISTORY_FILTER_CHANGED,
                cls.HISTORY_EXPORT_STARTED, cls.HISTORY_EXPORT_COMPLETED
            ]
        }
        
        return category_mapping.get(category.lower(), [])
    
    @classmethod
    def is_valid_event(cls, event_type: str) -> bool:
        """
        验证事件类型是否有效
        
        Args:
            event_type: 事件类型字符串
            
        Returns:
            bool: 事件类型是否有效
        """
        return event_type in cls.get_all_events()
    
    @classmethod
    def validate_event_data(cls, event_type: str, data: dict) -> bool:
        """
        验证事件数据的基本结构
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            bool: 数据是否有效
        """
        # 基本验证：事件类型必须有效
        if not cls.is_valid_event(event_type):
            return False
        
        # 数据必须是字典类型
        if not isinstance(data, dict):
            return False
        
        # 可以在这里添加更多特定事件的数据验证逻辑
        return True