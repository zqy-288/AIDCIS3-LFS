"""
P1页面异常处理模块
定义P1页面专用的异常类
"""


class BusinessControllerError(Exception):
    """业务控制器异常 - 兼容原有代码"""
    pass


class P1BusinessLogicError(Exception):
    """P1页面业务逻辑异常"""
    pass


class P1DataValidationError(Exception):
    """P1页面数据验证异常"""
    pass


class P1ComponentError(Exception):
    """P1页面组件异常"""
    pass


class P1ConfigurationError(Exception):
    """P1页面配置异常"""
    pass


# 为了兼容原有导入路径，创建一个main_exceptions模块别名
class MainExceptions:
    BusinessControllerError = BusinessControllerError


main_exceptions = MainExceptions()