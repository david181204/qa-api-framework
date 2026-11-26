# BUG-001 伪造 token 可越权下单

| 项 | 内容 |
|---|---|
| 缺陷编号 | BUG-001 |
| 模块 | 订单 |
| 严重等级 | **P0**（越权 + 影响库存与资金） |
| 优先级 | 高 |
| 发现方式 | 接口测试用例设计 + 阅读服务端源码 |
| 复现概率 | 必现 |
| 状态 | **Open（未修复）** |
| 发现版本 | qa-api-framework @ aeffb4a |

## 环境信息

- Windows 11 / Python 3.12.5
- MySQL 8.0（Docker，映射 3307）
- FastAPI 0.162.5

## 前置条件

- 商品 `id=2` 库存充足（≥ 1）
- 不需要登录，不需要任何有效凭证

## 复现步骤

1. 不调用 `/login`，不获取任何真实 token
2. 直接请求下单接口：

```http
POST /orders
Content-Type: application/json

{"product_id": 2, "quantity": 1, "token": "token-fake"}
```

3. 查询数据库：`SELECT stock FROM products WHERE id=2;`

## 预期结果

返回 `401 Unauthorized`，拒绝下单，库存不变。

## 实际结果

返回 `200 OK`，成功生成订单并扣减库存 1。

```json
{"order_id": 2, "product_id": 2, "quantity": 1, "status": "PAID"}
```

## 根因分析

`app/main.py` 第 52 行：

```python
if not req.token.startswith("token-"):
    raise HTTPException(status_code=401, detail="未登录")
```

服务端**仅校验 token 是否为 `token-` 开头的前缀字符串**，未校验：

1. 该 token 是否由登录接口签发
2. token 是否在有效期内
3. token 对应的用户身份

因此任意以 `token-` 开头的字符串（如 `token-fake`、`token-abc`）均可通过校验，
未登录用户可以任意下单并扣减库存。

## 影响范围

- **越权**：未认证用户可执行写操作
- **数据**：库存被恶意扣减
- **业务**：可伪造任意金额/数量的订单，造成资损风险

## 修复建议

1. 登录成功时签发 JWT（包含 `sub`、`exp`、签名），不返回明文 token
2. 下单接口校验：签名有效性 + 过期时间 + 用户身份
3. 订单记录绑定 token 中的 `user_id`，防止 A 用户操作 B 用户的订单
4. 补充异常用例：篡改 payload、过期 token、他人订单

## 关联自动化用例

`tests/test_orders.py::TestOrders::test_create_order_invalid_cases[1-token-fake-401]`

该用例断言**正确行为 401**，并用 `xfail(strict=True)` 标记为"已知缺陷导致预期失败"。
开发修复后，该用例会转为 `XPASS` 并报错，提醒移除 `xfail` 标记 —— 使缺陷修复可被自动感知。
