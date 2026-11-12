# Day4 缺陷记录

## BUG-001 订单接口伪造 Token 可下单
- 环境：本地 FastAPI + Docker MySQL
- 前置：商品1库存充足
- 步骤：
  1. 不登录，直接请求 POST /orders
  2. body: {"product_id":1,"quantity":1,"token":"token-fake"}
- 预期：401 未认证，拒绝下单
- 实际：200，返回 order_id=2，库存被扣减
- 根因：服务端只校验 token.startswith("token-")，未验证 token 是否由登录接口签发
- 严重程度：高（越权/鉴权绕过）
- 建议修复：登录时签发带签名的 token（如 JWT），下单时验签；或服务端维护已签发 token 白名单
- 状态：Open