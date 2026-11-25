import allure
import pytest
import requests

@allure.feature("商品模块")
class TestProducts:

    @allure.story("正向用例")
    @allure.title("获取商品列表")
    def test_products_list(self, base_url):
        r = requests.get(f"{base_url}/products")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 2
        assert len(data["items"]) == data["total"]

    @allure.story("正向用例")
    @allure.title("获取存在的商品详情")
    def test_product_detail_exists(self, base_url):
        r = requests.get(f"{base_url}/products/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    @allure.story("异常用例")
    @allure.title("商品 ID 边界值与类型测试")
    @pytest.mark.parametrize("product_id, expected_code", [
        (0, 404),       # 边界值 0
        (-1, 404),      # 负数
        (99999, 404),   # 超大 ID，不存在
        (1.5, 422),     # 浮点数，FastAPI 拦截
        ("abc", 422),   # 字符串，FastAPI 拦截
    ])
    def test_product_invalid_ids(self, base_url, product_id, expected_code):
        r = requests.get(f"{base_url}/products/{product_id}")
        assert r.status_code == expected_code