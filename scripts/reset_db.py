"""把测试数据库重置回 init.sql 定义的干净基线。

用途：
    测试跑久了，种子数据会被测试用例改掉（库存被扣、订单堆积），
    导致「同一份代码时绿时红」。这个脚本让环境可以一键回到初始状态，
    保证任何人、任何时间跑测试，起点都一样。

用法：
    .\\.venv\\Scripts\\python.exe scripts\\reset_db.py
"""
import os

from sqlalchemy import create_engine, text

DB_URL = os.getenv(
    "DB_URL",
    "mysql+pymysql://root:123456@127.0.0.1:3307/qa_shop?charset=utf8mb4",
)


def reset() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        # TRUNCATE 会同时把 AUTO_INCREMENT 归零，保证种子数据 id 稳定为 1、2
        conn.execute(text("TRUNCATE TABLE orders"))
        conn.execute(text("TRUNCATE TABLE products"))
        conn.execute(text("TRUNCATE TABLE users"))

        conn.execute(text("INSERT INTO users (username, password) VALUES ('david', '123456')"))
        conn.execute(text("INSERT INTO products (name, price, stock) VALUES ('iPhone', 5999.00, 100)"))
        conn.execute(text("INSERT INTO products (name, price, stock) VALUES ('MacBook', 12999.00, 50)"))
    engine.dispose()
    print("数据库已重置：users=1，products=2（iPhone 100 / MacBook 50），orders=0")


if __name__ == "__main__":
    reset()
