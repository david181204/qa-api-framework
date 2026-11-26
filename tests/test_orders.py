import allure
import pytest
from sqlalchemy import text


@allure.feature("订单模块")
class TestOrders:

    @allure.story("正向用例")
    @allure.title("正常下单，并验证数据库订单与库存扣减")
    def test_create_order_success(self, order_api, token, test_product, db_engine):
        # 先记录下单前库存，避免把 fixture 里的 100 硬编码进断言
        with db_engine.connect() as conn:
            stock_before = conn.execute(
                text("SELECT stock FROM products WHERE id=:pid"), {"pid": test_product}
            ).scalar()

        # 用例层只表达业务：用这个商品、这个数量、这个 token 下单
        # URL 怎么拼、超时多少，都由 api 层负责，这里看不到
        r = order_api.create(test_product, 2, token)
        assert r.status_code == 200
        order_id = r.json()["order_id"]

        # 断言 1：订单真的落库，且金额算对了
        with db_engine.connect() as conn:
            order = conn.execute(
                text("SELECT product_id, quantity, amount FROM orders WHERE id=:oid"),
                {"oid": order_id},
            ).fetchone()
        assert order is not None, "接口返回下单成功，但数据库里查不到这条订单"
        assert order[1] == 2, f"订单数量应为 2，实际 {order[1]}"
        assert float(order[2]) == 2000.0, f"订单金额应为 2000.0，实际 {order[2]}"

        # 断言 2：库存真的扣减了（验证副作用，而不只是验证 HTTP 200）
        with db_engine.connect() as conn:
            stock_after = conn.execute(
                text("SELECT stock FROM products WHERE id=:pid"), {"pid": test_product}
            ).scalar()
        assert stock_after == stock_before - 2, \
            f"库存应为 {stock_before - 2}，实际 {stock_after}"

    @allure.story("异常用例")
    @allure.title("下单参数与权限异常测试")
    @pytest.mark.parametrize("quantity, token_str, expected_code", [
        (1, "", 401),               # 无 Token
        pytest.param(
            1, "token-fake", 401,
            marks=pytest.mark.xfail(
                reason="BUG-001：服务端仅校验 token 前缀，伪造 token 仍可下单成功（未修复）",
                strict=True,
            ),
        ),
        (0, "valid", 400),          # 数量为 0
        (-1, "valid", 400),         # 数量为负数
    ])
    def test_create_order_invalid_cases(self, order_api, order_case_product, token,
                                        quantity, token_str, expected_code):
        # 如果传入的是 valid，就使用 fixture 里的真 token
        actual_token = token if token_str == "valid" else token_str
        payload = {"product_id": order_case_product, "quantity": quantity, "token": actual_token}
        r = order_api.create_raw(payload)
        assert r.status_code == expected_code

    @allure.story("异常用例")
    @allure.title("下单商品不存在")
    def test_create_order_product_not_found(self, order_api, token):
        r = order_api.create(99999999, 1, token)
        assert r.status_code == 404

    @allure.story("异常用例")
    @allure.title("下单缺少必填字段")
    def test_create_order_missing_field(self, order_api, order_case_product, token):
        # 不传 quantity，验证服务端参数校验
        r = order_api.create_raw({"product_id": order_case_product, "token": token})
        assert r.status_code == 422
