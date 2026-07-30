"""统一响应格式"""


def success(data=None, message="成功"):
    """成功响应"""
    return {"code": 10000, "data": data, "message": message}


def error(message="请求失败", code=-1):
    """失败响应"""
    return {"code": code, "data": None, "message": message}


def token_error(message="token异常，请重新登录"):
    """token 错误响应"""
    return {"code": -2, "data": None, "message": message}
