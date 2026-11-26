"""登录模块接口封装。"""
from api.base_api import BaseApi


class LoginApi(BaseApi):
    """只描述"登录接口有哪些操作"，不写断言。"""

    def login(self, username: str, password: str):
        """正常登录。返回 requests.Response，断言交给用例层。"""
        return self.post("/login", json={"username": username, "password": password})

    def login_raw(self, payload: dict):
        """原样发送 payload。

        用于"字段缺失""类型错误"这类契约测试：这类场景必须能构造出
        不完整/不合法 的请求体，而结构化方法（login）永远会补齐字段，
        所以单独提供 raw 入口。
        """
        return self.post("/login", json=payload)
