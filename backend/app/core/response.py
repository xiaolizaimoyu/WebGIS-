"""统一返回格式（归属：后端 F）

全后端约定：{ "code": 0, "msg": "ok", "data": ... }
- code == 0    表示成功，data 放业务数据
- code != 0    表示失败，msg 放可直接展示给用户的提示文案

业务代码中：
- 成功：return ok(data)
- 失败：raise BizError(code, msg)   —— 由 main.py 全局异常处理器转成统一格式
"""
from typing import Any


def ok(data: Any = None, msg: str = "ok") -> dict:
    return {"code": 0, "msg": msg, "data": data}


def err(code: int, msg: str, data: Any = None) -> dict:
    return {"code": code, "msg": msg, "data": data}


class BizError(Exception):
    """业务异常：携带业务错误码与用户可读文案，会在接口返回中保留 code 与 msg。"""

    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(msg)
