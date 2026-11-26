"""订单模块接口封装。"""
from api.base_api import BaseApi


class OrderApi(BaseApi):
    """只描述"订单接口有哪些操作"，不写断言。"""

    def create(self, product_id: int, quantity: int, token: str):
        """正常下单。返回 requests.Response，断言交给用例层。"""
        return self.post(
            "/orders",
            json={"product_id": product_id, "quantity": quantity, "token": token},
        )

    def create_raw(self, payload: dict):
        """原样发送 payload，用于字段缺失、类型错误等契约测试。"""
        return self.post("/orders", json=payload)
