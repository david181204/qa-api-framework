# BUG-004 下单接口无幂等，重复提交导致重复扣库存

| 项 | 内容 |
|---|---|
| 缺陷编号 | BUG-004 |
| 模块 | 订单 |
| 严重等级 | **P1**（重复扣库存，影响数据与资损） |
| 优先级 | 高 |
| 发现方式 | 业务规则分析 + 重复请求验证 |
| 复现概率 | 必现 |
| 状态 | Open（未修复） |

## 环境信息

- MySQL 8.0（Docker，映射 3307）
- FastAPI 0.162.5
- 复现脚本：`scripts/verify_defects.py`（D5 用例）

## 前置条件

- 商品库存 100
- 已登录，持有有效 token

## 复现步骤

1. 用完全相同的请求体连续提交 **2 次**（模拟网络重试、用户双击、前端重复触发）：

```http
POST /orders
{"product_id": <pid>, "quantity": 1, "token": "<valid>"}
```

2. 查询订单与库存：

```sql
SELECT COUNT(*) FROM orders WHERE product_id = <pid>;
SELECT stock FROM products WHERE id = <pid>;
```

## 预期结果

同一笔业务只应成功处理一次。第二次请求应被识别为重复请求，返回相同结果（或 `409 Conflict`），
**库存只扣 1**，订单只生成 1 条。

## 实际结果

**两条请求都返回 200，生成 2 条独立订单，库存被扣 2 次（100 → 98）。**

```
请求1: HTTP 200  order_id=27
请求2: HTTP 200  order_id=28
订单表实际条数: 2
最终库存: 98（初始 100）
```

## 根因分析

`POST /orders` 接口**没有任何幂等机制**：

1. 无幂等键（如客户端生成的 `request_id` / `idempotency-key`）
2. 无唯一约束（`orders` 表没有业务唯一索引）
3. 无重复请求检测（未使用 Redis 去重、未做请求指纹校验）

因此服务端把第二个请求当作一次全新的业务处理。

## 影响范围

- **用户重复下单**：网络抖动重试、前端连点、移动端弱网重发，都会导致重复订单
- **库存重复扣减**：实际只买 1 件，库存扣了 2 件，长期累积导致库存虚减
- **资金风险**：若接入支付，可能造成重复扣款

## 修复建议

1. **客户端**：下单前生成 `request_id`（UUID），随请求一起提交
2. **服务端**：`orders` 表增加 `request_id` 唯一索引；插入冲突时返回已有订单
3. **或改用 Redis**：`SET request_id NX EX 300`，设置失败即判定为重复请求
4. **前端**：按钮提交后置灰 + 防抖，但**这只是缓解，不能替代服务端幂等**

> 注意：前端防抖不是修复方案。真正的幂等必须在服务端实现，
> 因为攻击者或脚本可以直接调接口，绕过前端。

## 关联用例

当前自动化用例未覆盖"重复提交"场景，建议补充：

```python
def test_create_order_duplicate_submit(self, order_api, token, test_product, db_engine):
    """同一请求提交两次，只应生成一条订单"""
    r1 = order_api.create(test_product, 1, token)
    r2 = order_api.create(test_product, 1, token)
    assert r1.status_code == 200
    # 修复后 r2 应不产生新订单
    with db_engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE product_id=:pid"),
            {"pid": test_product},
        ).scalar()
    assert count == 1, f"重复提交生成了 {count} 条订单"
```

该用例在缺陷修复前会失败，可作为回归验证依据。
