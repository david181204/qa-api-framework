import allure
import requests

@allure.feature("商品模块")
class TestProducts:

    @allure.story("正向用例")
    def test_products_list(self, base_url):
        r = requests.get(f"{base_url}/products")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 2
        assert len(data["items"]) == data["total"]

    @allure.story("正向用例")
    def test_product_detail_exists(self, base_url):
        r = requests.get(f"{base_url}/products/2")
        assert r.status_code == 200
        assert r.json()["id"] == 2

    @allure.story("异常用例")
    def test_product_not_found(self, base_url):
        r = requests.get(f"{base_url}/products/999")
        assert r.status_code == 404

    @allure.story("异常用例")
    def test_product_invalid_id(self, base_url):
        r = requests.get(f"{base_url}/products/abc")
        assert r.status_code == 422