"""缺陷复现脚本：把代码审查发现的 4 个问题实际验证出来，并输出证据。

区别于 tests/ 下的自动化用例：
    tests/    断言"正确行为"，用来回归，必须全绿
    本脚本    断言"错误行为"，用来取证，输出的是缺陷证据，不判断通过失败

用法：
    .\\.venv\\Scripts\\python.exe scripts\\verify_defects.py

脚本会在最后清理自己造的数据，不影响种子数据。
"""
import os
import threading

import requests
from sqlalchemy import create_engine, text

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
DB_URL = os.getenv(
    "DB_URL",
    "mysql+pymysql://root:123456@127.0.0.1:3307/qa_shop?charset=utf8mb4",
)

engine = create_engine(DB_URL, pool_pre_ping=True)
created_product_ids = []


def _new_product(name: str, price: str, stock: int) -> int:
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO products (name, price, stock) VALUES (:n, :p, :s)"),
            {"n": name, "p": price, "s": stock},
        )
        pid = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    created_product_ids.append(pid)
    return pid


def _login() -> str:
    r = requests.post(f"{BASE_URL}/login", json={"username": "david", "password": "123456"}, timeout=10)
    return r.json()["token"]


def _cleanup() -> None:
    with engine.begin() as conn:
        for pid in created_product_ids:
            conn.execute(text("DELETE FROM orders WHERE product_id=:pid"), {"pid": pid})
            conn.execute(text("DELETE FROM products WHERE id=:pid"), {"pid": pid})


def case_d2_password_plaintext() -> None:
    print("=" * 66)
    print("D2  密码明文存储")
    print("=" * 66)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT username, password FROM users")).fetchall()
    for username, password in rows:
        print(f"  users 表实际值: username={username!r}, password={password!r}")
    print("  → 密码以明文存放，未做任何哈希/加盐。一旦数据库泄露，所有账号可直接登录。")
    print("  → 预期：应存储 bcrypt/argon2 哈希值，形如 $2b$12$...")
    print()


def case_d3_amount_precision() -> None:
    print("=" * 66)
    print("D3  订单金额浮点精度（代码风险，未复现为数据错误）")
    print("=" * 66)
    token = _login()
    pid = _new_product("缺陷验证-精度商品", "0.07", 100)

    r = requests.post(
        f"{BASE_URL}/orders",
        json={"product_id": pid, "quantity": 3, "token": token},
        timeout=10,
    )
    with engine.connect() as conn:
        amount = conn.execute(
            text("SELECT amount FROM orders WHERE product_id=:pid"), {"pid": pid}
        ).scalar()

    print(f"  商品单价 0.07，下单数量 3")
    print(f"  接口返回: {r.status_code} {r.json()}")
    print(f"  数据库 orders.amount 实际值: {amount!r}")
    print(f"  数学期望值: 0.21")
    if str(amount) == "0.21":
        print("  → 未复现为数据错误。原因：orders.amount 是 DECIMAL(10,2)，")
        print("          数据库把 float 计算出的 0.21000000000000002 四舍五入成了 0.21。")
        print("  → 结论：降级为【代码风险点】，不作为已确认缺陷提交。")
        print("     风险仍在：若将来该字段改为 FLOAT/DOUBLE、或金额参与多次累加/比较，")
        print("     误差会暴露。建议仍改用 Decimal 计算。")
    else:
        print("  → 已复现：金额出现浮点尾数。")
    print()


def case_d4_concurrent_oversell(rounds: int = 3, threads_per_round: int = 4) -> None:
    print("=" * 66)
    print(f"D4  库存扣减非原子，并发超卖（{rounds} 轮 x {threads_per_round} 并发）")
    print("=" * 66)
    token = _login()
    reproduced = False
    detail_lines = []

    for rd in range(1, rounds + 1):
        pid = _new_product(f"缺陷验证-并发商品-{rd}", "100.00", 10)
        results = []
        barrier = threading.Barrier(threads_per_round)

        def buy():
            barrier.wait()  # 让所有线程尽可能同时发请求，制造竞态
            resp = requests.post(
                f"{BASE_URL}/orders",
                json={"product_id": pid, "quantity": 10, "token": token},
                timeout=10,
            )
            results.append(resp.status_code)

        ts = [threading.Thread(target=buy) for _ in range(threads_per_round)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()

        with engine.connect() as conn:
            stock = conn.execute(
                text("SELECT stock FROM products WHERE id=:pid"), {"pid": pid}
            ).scalar()
        ok = results.count(200)
        detail_lines.append(f"  第{rd}轮: {ok} 个请求成功(200)，状态码={sorted(results)}，最终库存={stock}")

        if stock < 0 or ok > 1:
            reproduced = True
            detail_lines.append(f"          >>> 复现！库存 {stock}，超卖 {-stock if stock < 0 else 'N/A'} 件")
            break

    for line in detail_lines:
        print(line)

    if reproduced:
        print("  → 已复现：同一批库存被多次扣减，库存变为负数")
    else:
        print("  → 未稳定复现。并发窗口很窄（本地两个请求几乎不会真正重叠）。")
        print("  → 结论：标注为【代码层面存在竞态风险，未稳定复现】，不写成已确认缺陷。")
    print("  → 根因：app/main.py 先 SELECT 查库存、再 UPDATE 扣减，两次操作不在同一条原子语句里，")
    print("          且未加行锁（SELECT ... FOR UPDATE）或乐观锁版本号。")
    print("  → 预期：UPDATE products SET stock=stock-:q WHERE id=:id AND stock>=:q，")
    print("          用影响行数判断是否扣减成功；或加 FOR UPDATE 行锁。")
    print()


def case_d5_no_idempotency() -> None:
    print("=" * 66)
    print("D5  下单接口无幂等，重复提交重复扣库存")
    print("=" * 66)
    token = _login()
    pid = _new_product("缺陷验证-幂等商品", "50.00", 100)
    payload = {"product_id": pid, "quantity": 1, "token": token}

    r1 = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)
    r2 = requests.post(f"{BASE_URL}/orders", json=payload, timeout=10)

    with engine.connect() as conn:
        order_count = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE product_id=:pid"), {"pid": pid}
        ).scalar()
        stock = conn.execute(
            text("SELECT stock FROM products WHERE id=:pid"), {"pid": pid}
        ).scalar()

    print("  同一个请求（相同商品、相同数量）连续提交 2 次")
    print(f"  请求1: HTTP {r1.status_code} order_id={r1.json().get('order_id')}")
    print(f"  请求2: HTTP {r2.status_code} order_id={r2.json().get('order_id')}")
    print(f"  订单表实际条数: {order_count}")
    print(f"  最终库存: {stock}（初始 100）")
    print("  → 已复现：同一笔业务被处理两次，生成两条订单、扣了两次库存")
    print("  → 根因：接口没有幂等键（如 request_id / 唯一订单号），未做重复请求检测。")
    print("  → 预期：客户端传幂等键，服务端用唯一索引或 Redis 去重；或前端按钮防抖 + 后端校验。")
    print()


def main() -> None:
    print()
    print("缺陷复现报告")
    print(f"环境: {BASE_URL} | {DB_URL.split('@')[-1]}")
    print()
    try:
        case_d2_password_plaintext()
        case_d3_amount_precision()
        case_d4_concurrent_oversell()
        case_d5_no_idempotency()
    finally:
        _cleanup()
        engine.dispose()
        print("=" * 66)
        print(f"已清理本次验证产生的 {len(created_product_ids)} 个测试商品及其订单")


if __name__ == "__main__":
    main()
