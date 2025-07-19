"""
数据模型使用示例
展示如何使用新创建的数据模型
"""

# 由于需要PyQt6环境，这里只展示使用方法，不实际运行

def example_usage():
    """展示数据模型的使用方法"""
    
    # 1. 使用EventTypes
    from .event_types import EventTypes
    
    # 获取所有事件类型
    all_events = EventTypes.get_all_events()
    print(f"Total events: {len(all_events)}")
    
    # 按分类获取事件
    data_events = EventTypes.get_events_by_category("data")
    print(f"Data events: {data_events}")
    
    # 验证事件类型
    is_valid = EventTypes.is_valid_event(EventTypes.DXF_FILE_LOADED)
    print(f"DXF_FILE_LOADED is valid: {is_valid}")
    
    # 2. 使用DetectionState
    from .detection_state import DetectionState, DetectionStateManager
    
    # 创建状态管理器
    state_manager = DetectionStateManager()
    
    # 检查当前状态
    current_state = state_manager.current_state
    print(f"Current state: {current_state.get_display_name()}")
    
    # 状态转换
    success = state_manager.transition_to(DetectionState.LOADING, "Loading workpiece")
    print(f"Transition to LOADING: {success}")
    
    # 获取有效转换
    valid_transitions = state_manager.get_valid_transitions()
    print(f"Valid transitions: {[s.value for s in valid_transitions]}")
    
    # 3. 使用ApplicationModel（需要PyQt6环境）
    """
    from .application_model import ApplicationModel
    
    # 创建应用模型
    app_model = ApplicationModel()
    
    # 连接信号
    app_model.workpiece_loaded.connect(lambda wid: print(f"Workpiece loaded: {wid}"))
    app_model.hole_data_changed.connect(lambda hid, data: print(f"Hole {hid} changed: {data}"))
    
    # 加载工件
    app_model.load_workpiece("WP-001", {"name": "Test Workpiece", "holes": 100})
    
    # 设置应用状态
    app_model.set_application_state("current_tab", "detection")
    
    # 获取检测摘要
    summary = app_model.get_detection_summary()
    print(f"Detection summary: {summary}")
    """

if __name__ == "__main__":
    example_usage()