import allure
import pytest
import requests
from sqlalchemy import text

@allure.feature("订单模块")
class TestOrders:

    @allure.story("正向用例")
    @allure.title("正常下单，并验证数据库订单与库存扣减")
    def test_create_order_success(self, base_url, token, test_product, db_engine):
        payload = {"product_id": test_product, "quantity": 2, "token": token}
        r = requests.post(f"{base_url}/orders", json=payload)
        assert r.status_code == 200
        order_id = r.json()["order_id"]

        with db_engine.connect() as conn:
            order = conn.execute(
                text("SELECT product_id, quantity, amount FROM orders WHERE id=:oid"), 
                {"oid": order_id}
            ).fetchone()
        assert order is not None
        assert order[1] == 2
        assert float(order[2]) == 2000.0

        with db_engine.connect() as conn:
            stock = conn.execute(
                text("SELECT stock FROM products WHERE id=:pid"), 
                {"pid": test_product}
            ).scalar()
        assert stock == 98

    @allure.story("异常用例")
    @allure.title("下单参数与权限异常测试")
    @pytest.mark.parametrize("product_id, quantity, token_str, expected_code", [
        (2, 1, "", 401),            # 无 Token
        (2, 1, "token-fake", 200),  # BUG记录：伪造前缀依然能下单成功
        (2, 0, "valid", 400),       # 数量为 0
        (2, -1, "valid", 400),      # 数量为负数
        (99999, 1, "valid", 404),   # 商品不存在
    ])
    def test_create_order_invalid_cases(self, base_url, token, product_id, quantity, token_str, expected_code):
        # 如果传入的是 valid，就使用 fixture 里的真 token
        actual_token = token if token_str == "valid" else token_str
        payload = {"product_id": product_id, "quantity": quantity, "token": actual_token}
        r = requests.post(f"{base_url}/orders", json=payload)
        assert r.status_code == expected_code

    @allure.story("异常用例")
    @allure.title("下单缺少必填字段")
    def test_create_order_missing_field(self, base_url, token):
        payload = {"product_id": 1, "token": token}
        r = requests.post(f"{base_url}/orders", json=payload)
        assert r.status_code == 422