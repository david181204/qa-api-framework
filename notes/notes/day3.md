# Day3 FastAPI 被测服务

## 服务
- 文件：main.py
- 启动：uvicorn main:app --reload --port 8000
- 端口：8000

## 接口
- POST /login：正确返回 token，错误返回 401
- GET /products：返回 total + items
- GET /products/{id}：存在返回商品，不存在返回 404

## curl 测试结果
- 正确登录 → {"token":"token-david"}
- 错误密码 → {"detail":"用户名或密码错误"}
- 商品列表 → total=2
- 不存在商品 → {"detail":"商品不存在"}

## 排障记录
- Docker 拉镜像超时：dial tcp registry-1.docker.io:443 failed to respond
  → 配镜像加速器/用梯子解决
- Docker daemon 未启动：failed to connect to the docker API
  → 启动 Docker Desktop，等 Engine running