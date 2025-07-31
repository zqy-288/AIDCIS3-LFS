"""
页面通用异常处理模块
定义所有页面共用的异常类
"""


class PageException(Exception):
    """页面基础异常"""
    pass


class PageInitializationError(PageException):
    """页面初始化异常"""
    pass


class PageDataError(PageException):
    """页面数据异常"""
    pass


class PageUIError(PageException):
    """页面UI异常"""
    pass