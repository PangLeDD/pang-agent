from typing import Any


def success(data: Any = None, message: str = "ok", code: int = 200) -> dict[str, Any]:
    # 统一正常响应，后续会话、分页、Agent 结果都放进 data。
    return {"code": code, "message": message, "data": data}


def error_payload(code: int, message: str) -> dict[str, Any]:
    # 统一异常响应，避免各处手写结构导致字段不一致。
    return {"code": code, "message": message, "data": None}
