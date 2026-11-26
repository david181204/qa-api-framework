# 电商核心链路 API 自动化测试框架

![API Automation Tests](https://github.com/david181204/qa-api-framework/actions/workflows/ci.yml/badge.svg)

基于 FastAPI + MySQL 自建被测服务，使用 **pytest + requests + Allure** 搭建分层接口自动化测试框架，
通过 **GitHub Actions** 实现每次提交自动回归，并配套测试用例设计、缺陷跟踪与环境重置能力。

---

## 一、项目背景

自学软件测试时，市面上大部分练手项目只能"发请求、断状态码"，
无法覆盖真实工作里的三个问题：

1. **测试数据互相污染** —— 用例跑第二遍就挂
2. **只断 HTTP 200** —— 接口没崩，但业务数据是错的
3. **没有 CI** —— 只能本地手点，回归不可重复

所以我自建了一个被测服务，并围绕它把接口自动化"做完整"：
从用例设计、框架分层、数据治理、CI 集成到缺陷跟踪，走完一个测试工程师的完整闭环。

> 服务的 4 个接口（登录 / 商品列表 / 商品详情 / 下单）业务复杂度不高，
> 但**方法论是完整的**——换成几十个接口的系统，做法一样，只是模块拆分更细。

---

## 二、技术栈

| 分类 | 技术 |
|---|---|
| 被测服务 | FastAPI、SQLAlchemy、Pydantic |
| 数据库 | MySQL 8.0（Docker 部署） |
| 测试框架 | pytest（fixture / 参数化 / hook） |
| 请求层 | requests（Session 复用） |
| 报告 | Allure |
| 持续集成 | GitHub Actions（service container + artifact） |
| 代码托管 | Git + GitHub |

---

## 三、框架分层

```
tests/            用例层：只写业务断言，不出现 requests
    ↑
conftest.py       fixture 层：组装 api 对象与测试数据（造 + 清）
    ↑
api/              接口层：每个模块一个类，只做参数 → 请求的翻译
    ↑             BaseApi 统一处理会话复用、超时、日志
config/           配置层：环境地址、数据库连接、超时时间
```

**分层的三个收益：**

1. **接口变更只改一处** —— 新增接口只需改 `api/xxx_api.py` + `tests/`，`conftest.py` 和 `config/` 不动
2. **横切逻辑集中** —— 超时、会话、日志统一在 `BaseApi`，不会有用例漏加 `timeout` 导致 CI 挂死
3. **用例可读** —— 从"HTTP 调用说明书"变成业务描述：`order_api.create(product_id, 2, token)`

```
├── api/
│   ├── base_api.py       # 父类：Session 复用、统一超时、日志
│   ├── login_api.py      # 登录接口
│   ├── product_api.py    # 商品接口
│   └── order_api.py      # 订单接口
├── config/settings.py    # 环境配置（支持环境变量覆盖）
├── tests/
│   ├── test_login.py
│   ├── test_products.py
│   └── test_orders.py
├── conftest.py           # fixture：api 对象、登录态、测试数据
├── app/main.py           # 被测服务
├── init.sql              # 建表 + 种子数据
└── scripts/reset_db.py   # 一键重置测试环境
```

---

## 四、测试设计

共设计 **26 条**用例，自动化落地 **22 条**（其中 16 条由参数化展开）。

| 模块 | 用例数 | 覆盖维度 |
|---|---|---|
| 登录 | 8 | 正向登录、错误密码、空值、不存在用户、SQL 注入、超长输入、字段缺失 |
| 商品 | 7 | 列表、详情、ID 边界（0 / 负数 / 超大 / 浮点 / 字符串类型） |
| 订单 | 7 | 正常下单（含数据库断言）、无 token、伪造 token、数量 0 / 负数、商品不存在、字段缺失 |

**断言分两层：**

- **HTTP 层**：状态码、关键字段
- **数据层**：查数据库确认订单落库、金额计算正确、库存扣减正确

> 为什么要有数据层断言：HTTP 200 只说明接口没崩。订单有没有真落库、金额算得对不对、
> 库存有没有扣——只有查库才知道。

---

## 五、关键实践

### 1. 测试数据治理（fixture 造 + 清）

每个用例使用自己的数据，`yield` 前置插入、后置删除，保证用例可重复执行、互不污染。

> **踩过的坑（flaky test）**：最初只给正向用例做了数据隔离，异常用例直接用了种子商品。
> 而"伪造 token 仍能下单成功"（BUG-001）那条用例每跑一次就真的扣一次库存，
> 跑约 50 次后库存耗尽，接口返回 400「库存不足」——**这是完全正确的业务行为**，
> 但用例期望 200，于是变红。
>
> 最坑的是：一开始以为是系统坏了。**异常用例的输入是异常的，但副作用是真实的**，
> 所以异常用例同样必须使用隔离数据。

### 2. 已知缺陷用 xfail 标记，而不是改断言迁就

```python
pytest.param(
    1, "token-fake", 401,   # 断言正确行为：401
    marks=pytest.mark.xfail(reason="BUG-001 未修复", strict=True),
)
```

断言写的是**正确**的业务行为，用 `xfail(strict=True)` 标记为"预期失败"。
开发修复后该用例会变成 `XPASS` 并报错，提醒移除标记——**让缺陷修复能被自动感知**。

### 3. 环境可重复构建

- 配置通过环境变量覆盖：本地 MySQL 映射 3307，CI 里是 3306，**代码零改动**
- `scripts/reset_db.py` 一键重置数据库（`TRUNCATE` 会重置自增 id，保证种子数据 id 稳定）

### 4. CI 流水线

每次 push 自动执行：

```
启动 MySQL 服务容器 → 等待 health check → 执行 init.sql →
拉起 uvicorn → 执行全量用例 → 生成 Allure 报告 → 上传 artifact
```

---

## 六、缺陷记录

### 缺陷汇总

| 编号 | 标题 | 严重等级 | 状态 | 复现 |
|---|---|---|---|---|
| [BUG-001](notes/defects/BUG-001-token-bypass.md) | 伪造 token 可越权下单 | P0 | Open | 必现 |
| [BUG-003](notes/defects/BUG-003-concurrent-oversell.md) | 库存扣减非原子，并发超卖 | P0 | Open | 偶现（并发窗口） |
| [BUG-002](notes/defects/BUG-002-plaintext-password.md) | 用户密码明文存储 | P1 | Open | 必现 |
| [BUG-004](notes/defects/BUG-004-no-idempotency.md) | 下单无幂等，重复扣库存 | P1 | Open | 必现 |

4 条均为**实际复现并留证**，复现脚本：[`scripts/verify_defects.py`](scripts/verify_defects.py)

### 重点缺陷：BUG-003 并发超卖

初始库存 10，4 个并发请求各下单 10：

```
第1轮: 1 个请求成功(200)，状态码=[200, 400, 400, 400]，最终库存=0
第2轮: 4 个请求成功(200)，状态码=[200, 200, 200, 200]，最终库存=-30   ← 超卖 30 件
```

根因：`SELECT` 校验与 `UPDATE` 扣减是两个独立操作（check-then-act 竞态），
且 `SELECT` 未加锁，多个事务都读到同一库存值并通过校验。
修复建议：改为 `UPDATE ... SET stock = stock - :q WHERE id = :id AND stock >= :q`，
用影响行数判断是否扣减成功。

### 已识别但未复现的风险点

阅读代码发现、但**未能稳定复现**的问题，**不作为已确认缺陷提交**：

| 编号 | 问题 | 说明 |
|---|---|---|
| D3 | 订单金额用 `float` 计算 | 已写脚本验证：`orders.amount` 为 `DECIMAL(10,2)`，浮点误差被数据库四舍五入抵消，**未复现为数据错误**，故降级为代码风险 |
| D6 | 商品列表无分页 | 需构造大量数据，验证收益低 |
| D7 | token 无过期时间 | 需等待过期，无法在测试周期内验证 |
| D8 | 登录无限流 | 需高频压测，易污染环境 |
| D9 | 数据库口令硬编码 | 代码审查即可确认，属配置问题 |

---

## 七、快速开始

### 1. 启动数据库

```bash
docker start mysql-test          # 端口映射 3307 -> 3306（本地 3306 已被占用）
docker ps                        # 确认状态 Up
```

### 2. 初始化数据（首次或需要重置时）

```bash
python scripts/reset_db.py
```

### 3. 启动被测服务

```bash
# 终端 A
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### 4. 执行测试

```bash
# 终端 B
pytest tests -v                                        # 全量
pytest tests/test_orders.py -v                         # 单个文件
pytest tests -v --alluredir=./allure-results           # 生成报告数据
allure serve ./allure-results                          # 预览报告
```

---

## 八、已知限制与后续计划

诚实记录当前不足，避免误判项目能力边界：

| 限制 | 计划 |
|---|---|
| 被测服务仅 4 个接口，业务复杂度有限 | 补充订单查询 / 取消、库存回滚等链路 |
| token 为简单字符串，未做 JWT | 改造为 JWT，并补充过期 / 篡改 / 越权用例（修复 BUG-001） |
| CI 用 `sleep 5` 等服务启动，机器慢时偶发失败 | 改为轮询 `/products` 直到返回 200 |
| 未做性能测试 | 用 Locust 压 `/products` 与 `/orders`，定位瓶颈 |
| 未做并发场景（超卖验证） | 多线程并发下单，验证 D4 |
| `requirements.txt` 为 `pip freeze` 全量导出 | 拆分为直接依赖，传递依赖交给 pip 解析 |
| 无 UI 自动化 | 可补充 Selenium + PageObject 覆盖核心链路 |

---

## 九、说明

本项目为个人学习项目，被测服务（`app/`）与测试代码（`tests/`、`api/`、`config/`）均由本人编写，
用于系统练习接口自动化测试的完整流程。欢迎交流指正。
