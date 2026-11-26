import allure
import pytest


@allure.feature("登录模块")
class TestLogin:

    @allure.story("正向用例")
    @allure.title("使用正确的账号密码登录")
    def test_login_success(self, login_api):
        with allure.step("发送登录请求"):
            r = login_api.login("david", "123456")
        with allure.step("断言状态码和返回Token"):
            assert r.status_code == 200
            assert "token" in r.json()

    # 使用参数化，一次性扩充 6 条异常用例
    @allure.story("异常用例")
    @allure.title("登录参数校验与安全测试")
    @pytest.mark.parametrize("username, password, expected_code", [
        ("david", "wrong", 401),             # 错误密码
        ("", "123456", 401),                 # 用户名为空
        ("david", "", 401),                  # 密码为空
        ("测试用户", "123456", 401),           # 用户不存在（中文）
        ("david' OR '1'='1", "123456", 401), # SQL注入尝试
        ("a" * 100, "123456", 401),          # 超长用户名
    ])
    def test_login_invalid_params(self, login_api, username, password, expected_code):
        r = login_api.login(username, password)
        assert r.status_code == expected_code

    @allure.story("异常用例")
    @allure.title("缺少必填字段")
    def test_login_missing_field(self, login_api):
        # 只传 username、不传 password：用 raw 入口原样发送，验证服务端参数校验
        r = login_api.login_raw({"username": "david"})
        assert r.status_code == 422
