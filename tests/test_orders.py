import allure
import requests
from sqlalchemy import text

@allure.feature("订单模块")
class TestOrders:

    @allure.story("正向用例")
    @allure.title("正常下单，并验证数据库订单与库存扣减")
    def test_create_order_success(self, base_url, token, test_product, db_engine):
        # 使用 conftest 里造出来的测试商品，quantity=2
        payload = {"product_id": test_product, "quantity": 2, "token": token}
        r = requests.post(f"{base_url}/orders", json=payload)
        
        assert r.status_code == 200
        order_id = r.json()["order_id"]

        # 数据库断言 1：检查 orders 表是否有这条订单，金额是否正确（1000 * 2 = 2000）
        with db_engine.connect() as conn:
            order = conn.execute(
                text("SELECT product_id, quantity, amount FROM orders WHERE id=:oid"), 
                {"oid": order_id}
            ).fetchone()
        
        assert order is not None, "数据库中没有生成对应订单"
        assert order[0] == test_product
        assert order[1] == 2
        assert float(order[2]) == 2000.0

        # 数据库断言 2：检查商品库存是否从 100 扣到了 98
        with db_engine.connect() as conn:
            stock = conn.execute(
                text("SELECT stock FROM products WHERE id=:pid"), 
                {"pid": test_product}
            ).scalar()
        assert stock == 98, "库存扣减不正确"

    @allure.story("异常用例")
    @allure.title("无 Token 下单被拒绝")
    def test_create_order_no_token(self, base_url, test_product):
        # 用测试商品ID
        payload = {"product_id": test_product, "quantity": 1, "token": ""}
        r = requests.post(f"{base_url}/orders", json=payload)
        assert r.status_code == 401

    @allure.story("异常用例")
    @allure.title("下单数量为 0")
    def test_create_order_quantity_zero(self, base_url, token, test_product):
        payload = {"product_id": test_product, "quantity": 0, "token": token}
        r = requests.post(f"{base_url}/orders", json=payload)
        assert r.status_code == 400

    @allure.story("异常用例")
    @allure.title("下单商品不存在")
    def test_create_order_product_not_found(self, base_url, token):
        payload = {"product_id": 99999, "quantity": 1, "token": token}
        r = requests.post(f"{base_url}/orders", json=payload)
        assert r.status_code == 404

    @allure.story("异常用例")
    @allure.title("下单缺少必填字段")
    def test_create_order_missing_field(self, base_url, token):
        # 缺少 quantity 字段
        payload = {"product_id": 1, "token": token}
        r = requests.post(f"{base_url}/orders", json=payload)
        assert r.status_code == 422