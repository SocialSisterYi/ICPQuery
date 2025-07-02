class ICPQueryError(Exception):
    "ICP查询调用错误"


class ICPHTTPError(ICPQueryError):
    "ICP查询HTTP错误"


class APIError(ICPQueryError):
    "ICP查询接口调用异常"

    def __init__(self, code: int, msg: str) -> None:
        super().__init__()
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return f"{self.code}:{self.msg}"


class FuckCaptchaFail(ICPQueryError):
    """验证码识别失败"""
