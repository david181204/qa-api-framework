# 接口测试用例

## 登录 POST /login

| 编号 | 标题 | 前置 | 请求 | 预期 |
|---|---|---|---|---|
| L01 | 正确账号密码登录 | 用户david存在 | {"username":"david","password":"123456"} | 200，返回token |
| L02 | 错误密码 | 用户david存在 | {"username":"david","password":"wrong"} | 401，用户名或密码错误 |
| L03 | 用户不存在 | 无 | {"username":"nobody","password":"123456"} | 401 |
| L04 | 用户名为空 | 无 | {"username":"","password":"123456"} | 401 或 400 |
| L05 | 密码为空 | 无 | {"username":"david","password":""} | 401 或 400 |
| L06 | 缺字段 | 无 | {"username":"david"} | 422 参数校验失败 |
| L07 | 超长用户名 | 无 | username 300字符 | 422 或 400 |
| L08 | SQL注入字符 | 无 | username: "' OR '1'='1" | 401，不能登录成功 |

## 商品列表 GET /products

| 编号 | 标题 | 请求 | 预期 |
|---|---|---|---|
| P01 | 正常列表 | GET /products | 200，total>=2 |
| P02 | 字段完整性 | GET /products | 每条含id/name/price/stock |

## 商品详情 GET /products/{id}

| 编号 | 标题 | 请求 | 预期 |
|---|---|---|---|
| D01 | 存在商品 | /products/1 | 200，id=1 |
| D02 | 不存在商品 | /products/999 | 404 |
| D03 | id非数字 | /products/abc | 422 |
| D04 | id为负数 | /products/-1 | 404 |
| D05 | id为0 | /products/0 | 404 |

## 下单 POST /orders

| 编号 | 标题 | 请求 | 预期 |
|---|---|---|---|
| O01 | 正常下单 | product_id=1, quantity=1, 有效token | 200，返回order_id |
| O02 | 库存扣减 | 下单后查/products/1 | stock 减1 |
| O03 | 库存不足 | quantity=9999 | 400，库存不足 |
| O04 | 数量为0 | quantity=0 | 400 |
| O05 | 数量为负 | quantity=-1 | 400 |
| O06 | 商品不存在 | product_id=999 | 404 |
| O07 | 无token | token="" | 401 |
| O08 | 伪造token | token="fake" | 401 |
| O09 | 缺字段 | 只传product_id | 422 |
| O10 | 边界：买光库存 | quantity=stock | 200，stock=0 |
| O11 | 超卖：买库存+1 | quantity=stock+1 | 400 |