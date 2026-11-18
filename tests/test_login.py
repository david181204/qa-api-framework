import pytest
import requests
import allure

@allure.feature("登录模块")
class TestLogin:
    
    @allure.story("正向用例")
    @allure.title("使用正确的账号密码登录")
    def test_login_success(self, base_url):
        with allure.step("发送登录请求"):
            r = requests.post(f"{base_url}/login", json={"username": "david", "password": "123456"})
        
        with allure.step("断言状态码和返回Token"):
            assert r.status_code == 200
            assert "token" in r.json()

    @allure.story("异常用例")
    @allure.title("错误密码登录失败")
    def test_login_wrong_password(self, base_url):
        r = requests.post(f"{base_url}/login", json={"username": "david", "password": "wrong"})
        assert r.status_code == 401

    @allure.story("异常用例")
    @allure.title("缺少必填字段")
    def test_login_missing_field(self, base_url):
        r = requests.post(f"{base_url}/login", json={"username": "david"})
        assert r.status_code == 422

    @allure.story("异常用例")
    @allure.title("密码为空")
    def test_login_empty_password(self, base_url):
        r = requests.post(f"{base_url}/login", json={"username": "david", "password": ""})
        assert r.status_code == 401