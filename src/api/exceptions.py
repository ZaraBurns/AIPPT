"""
自定义异常类
"""


class PPTException(Exception):
    """PPT生成异常"""
    pass


class ConversionException(Exception):
    """PPTX转换异常"""
    pass


class FileServiceException(Exception):
    """文件服务异常"""
    pass


class ValidationException(Exception):
    """验证异常"""
    pass
