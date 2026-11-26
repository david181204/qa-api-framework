"""接口层基类。

分层后的职责划分：
    config/   环境参数（地址、超时、数据库连接）
    api/      怎么发请求（URL 拼装、会话、超时、日志、鉴权）
    tests/    业务怎么断言（这个接口在这个场景下应该返回什么）

好处：
1. 接口签名变了，只改 api/ 层一处，不用动几十条用例。
2. requests 的细节（超时、会话复用）集中管理，不会有人忘记加 timeout。
3. 用例读起来像业务描述，不像 HTTP 调用说明书。
"""
import logging

import requests

from config.settings import BASE_URL, TIMEOUT

logger = logging.getLogger(__name__)


class BaseApi:
    """所有接口类的父类，提供统一的请求能力。"""

    def __init__(self, base_url: str = BASE_URL, timeout: float = TIMEOUT):
        # Session 会复用底层 TCP 连接，并自动保持 Cookie
        self.session = requests.Session()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        # 调用方没传 timeout 时用默认值，避免"忘了设超时导致 CI 挂死"
        kwargs.setdefault("timeout", self.timeout)
        logger.info("%s %s", method, url)
        return self.session.request(method, url, **kwargs)

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def close(self) -> None:
        self.session.close()
