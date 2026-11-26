"""pytest 全局 fixture。

分层后的职责：
    config/   环境参数
    api/      怎么发请求
    conftest  把 api 对象、测试数据组装成 fixture 提供给用例
    tests/    业务断言（只依赖 fixture，不关心 HTTP 细节）
"""
import pytest
from sqlalchemy import create_engine, text

from api.login_api import LoginApi
from api.order_api import OrderApi
from api.product_api import ProductApi
from config.settings import DB_URL


# ---------------- 接口对象（整个会话复用，内部复用 TCP 连接） ----------------

@pytest.fixture(scope="session")
def login_api():
    api = LoginApi()
    yield api
    api.close()


@pytest.fixture(scope="session")
def product_api():
    api = ProductApi()
    yield api
    api.close()


@pytest.fixture(scope="session")
def order_api():
    api = OrderApi()
    yield api
    api.close()


# ---------------- 登录态 ----------------

@pytest.fixture(scope="session")
def token(login_api):
    """登录一次，全用例集复用。

    风险提示：如果 token 有过期时间，跑长用例集时会失效，导致后续用例集体 401。
    当前服务端签发的 token 永不过期（见缺陷 D7），所以这个坑暂时暴露不出来。
    """
    r = login_api.login("david", "123456")
    assert r.status_code == 200
    return r.json()["token"]


# ---------------- 数据库 ----------------

@pytest.fixture(scope="session")
def db_engine():
    """提供数据库连接。pool_pre_ping 会在取连接前 ping 一次，丢弃已断开的死连接。"""
    engine = create_engine(DB_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()  # 测试结束后释放连接


# ---------------- 测试数据（造 + 清，保证用例可重复执行） ----------------

@pytest.fixture
def test_product(db_engine):
    """正向用例专用商品：库存 100，用完连订单一起删除。"""
    with db_engine.begin() as conn:
        conn.execute(text("INSERT INTO products (name, price, stock) VALUES ('TestPhone', 1000.00, 100)"))
        product_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    yield product_id

    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM orders WHERE product_id=:pid"), {"pid": product_id})
        conn.execute(text("DELETE FROM products WHERE id=:pid"), {"pid": product_id})


@pytest.fixture
def order_case_product(db_engine):
    """异常用例专用商品：库存 10，用完连订单一起删除。

    为什么异常用例也要隔离数据：
    里面有一条「伪造 token 仍能下单成功」(BUG-001)，它每跑一次就真的扣一次库存。
    如果用公共种子商品，库存会被测试慢慢吃光，跑到第 N 次时这条用例会因为
    「库存不足」返回 400 而变红 —— 也就是 flaky test（用例自己制造的不稳定）。
    """
    with db_engine.begin() as conn:
        conn.execute(text("INSERT INTO products (name, price, stock) VALUES ('OrderCasePhone', 100.00, 10)"))
        product_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    yield product_id

    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM orders WHERE product_id=:pid"), {"pid": product_id})
        conn.execute(text("DELETE FROM products WHERE id=:pid"), {"pid": product_id})
