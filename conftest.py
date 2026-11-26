import os
import pytest
import requests
from sqlalchemy import create_engine, text

BASE_URL = "http://127.0.0.1:8000"
DB_URL = os.getenv("DB_URL", "mysql+pymysql://root:123456@127.0.0.1:3307/qa_shop?charset=utf8mb4")

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def token(base_url):
    r = requests.post(f"{base_url}/login", json={"username": "david", "password": "123456"})
    assert r.status_code == 200
    return r.json()["token"]

@pytest.fixture(scope="session")
def db_engine():
    """提供数据库连接"""
    engine = create_engine(DB_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()  # 测试结束后释放连接

@pytest.fixture
def test_product(base_url, token, db_engine):
    """
    造数据：每次执行前，新增一个库存为100的专属测试商品
    清理：每次执行后，删除这个商品和它的订单，保证环境干净
    """
    # 1. 前置：插入测试商品
    with db_engine.begin() as conn:
        conn.execute(text("INSERT INTO products (name, price, stock) VALUES ('TestPhone', 1000.00, 100)"))
        # 获取刚插入的id
        product_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    
    yield product_id  # 把 product_id 传给测试用例用

    # 2. 后置：清理数据（删订单 -> 删商品）
    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM orders WHERE product_id=:pid"), {"pid": product_id})
        conn.execute(text("DELETE FROM products WHERE id=:pid"), {"pid": product_id})


@pytest.fixture
def order_case_product(db_engine):
    """
    异常用例专用商品：库存小（10），每次执行后连订单一起删除。

    为什么需要它：
    test_create_order_invalid_cases 里有一条「伪造 token 仍能下单成功」(BUG-001)，
    它每跑一次就会真的扣一次库存。如果直接用种子商品 id=2，库存会被测试慢慢吃光，
    跑到第 N 次时这条用例就会因为「库存不足」变成 400，用例莫名变红 —— 也就是 flaky test。
    所以异常用例也必须使用自己的数据，不能碰公共数据。
    """
    with db_engine.begin() as conn:
        conn.execute(text("INSERT INTO products (name, price, stock) VALUES ('OrderCasePhone', 100.00, 10)"))
        product_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    yield product_id

    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM orders WHERE product_id=:pid"), {"pid": product_id})
        conn.execute(text("DELETE FROM products WHERE id=:pid"), {"pid": product_id})