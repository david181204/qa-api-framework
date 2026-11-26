# BUG-003 库存扣减非原子，并发下单导致超卖

| 项 | 内容 |
|---|---|
| 缺陷编号 | BUG-003 |
| 模块 | 订单 / 库存 |
| 严重等级 | **P0**（数据一致性 + 超卖导致资损与履约失败） |
| 优先级 | 高 |
| 发现方式 | 并发场景验证（多线程同时下单） |
| 复现概率 | 偶现（需并发窗口命中，约 2-3 轮可复现一次） |
| 状态 | Open（未修复） |

## 环境信息

- Windows 11 / Python 3.12.5
- MySQL 8.0（Docker，映射 3307），默认隔离级别 REPEATABLE READ
- FastAPI 0.162.5（uvicorn 单 worker，同步路由跑在线程池中，请求可并发）

## 前置条件

- 商品库存为 **10**
- 已登录，持有有效 token
- 复现脚本：`scripts/verify_defects.py`（D4 用例）

## 复现步骤

1. 新建一个库存为 10 的商品
2. 启动 **4 个线程**，用 `threading.Barrier` 让它们尽可能同时发出下单请求，每个请求购买数量 **10**：

```http
POST /orders
{"product_id": <pid>, "quantity": 10, "token": "<valid>"}
```

3. 所有请求结束后查询库存：`SELECT stock FROM products WHERE id=<pid>;`

## 预期结果

只有 1 个请求成功（库存恰好扣完），其余 3 个返回 `400 库存不足`，最终库存为 `0`。

## 实际结果

第 2 轮复现：**4 个请求全部返回 200**，最终库存为 **-30**（超卖 30 件）。

```
第1轮: 1 个请求成功(200)，状态码=[200, 400, 400, 400]，最终库存=0
第2轮: 4 个请求成功(200)，状态码=[200, 200, 200, 200]，最终库存=-30
```

## 根因分析

`app/main.py` 下单逻辑：

```python
p = conn.execute(text("SELECT id, name, price, stock FROM products WHERE id=:id")).fetchone()
if p["stock"] < req.quantity:
    raise HTTPException(status_code=400, detail="库存不足")

conn.execute(text("UPDATE products SET stock=stock-:q WHERE id=:id"))
```

**问题在于"检查"和"扣减"是两个独立操作，且 `SELECT` 未加锁。**

1. 多个事务的 `SELECT` 是**快照读**（REPEATABLE READ 下不加锁），4 个事务都读到了 `stock=10`
2. 都通过了 `stock < quantity` 的校验（10 < 10 为假）
3. 随后各自执行 `UPDATE stock=stock-10`。`UPDATE` 是当前读、会加行锁，但因为前面的校验已经放行，
   4 次扣减依次生效：`10 → 0 → -10 → -20 → -30`

即典型的 **check-then-act 竞态条件（TOCTOU）**。

## 影响范围

- **超卖**：卖出数量超过实际库存，导致无法发货
- **库存数据错误**：库存变为负数，后续所有库存计算、报表全部失真
- 高并发场景（秒杀、限量抢购）下问题会被放大

## 修复建议

### 方案一：条件更新（推荐，最简洁）

把校验和扣减合并成一条原子语句，用**影响行数**判断是否成功：

```python
result = conn.execute(
    text("UPDATE products SET stock = stock - :q WHERE id = :id AND stock >= :q"),
    {"q": req.quantity, "id": req.product_id},
)
if result.rowcount == 0:
    raise HTTPException(status_code=400, detail="库存不足")
```

### 方案二：行锁

```sql
SELECT stock FROM products WHERE id = :id FOR UPDATE;
```

在事务内先锁住行，再判断、再更新。

### 方案三：乐观锁

给 `products` 加 `version` 字段，更新时校验版本号，失败则重试或报错。

## 验证方式

修复后重新运行 `python scripts/verify_defects.py`，D4 部分应显示：
**只有 1 个请求返回 200，其余 400，最终库存 0**。

## 备注

这是本项目**最能体现测试价值**的缺陷之一：它不是靠"点界面"发现的，
而是通过**构造并发场景**发现的。说明异常场景测试不只看输入是否合法，还要看**时序**。
