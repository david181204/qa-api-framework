# BUG-002 用户密码明文存储

| 项 | 内容 |
|---|---|
| 缺陷编号 | BUG-002 |
| 模块 | 用户 / 安全 |
| 严重等级 | **P1**（安全，数据泄露后可直接登录所有账号） |
| 优先级 | 高 |
| 发现方式 | 数据库数据校验（测试数据准备时查看表结构） |
| 复现概率 | 必现 |
| 状态 | Open（未修复） |

## 环境信息

- MySQL 8.0（Docker，映射 3307）
- 库名：`qa_shop`

## 前置条件

- 数据库已初始化（执行过 `init.sql`）

## 复现步骤

```sql
SELECT username, password FROM users;
```

## 预期结果

密码以**加盐哈希**形式存储，例如：

```
$2b$12$KIXs3vJ9mQx...（bcrypt）
$argon2id$v=19$m=65536,t=3,p=4$...（argon2）
```

哈希不可逆，即使数据库泄露，攻击者也无法直接获取明文密码。

## 实际结果

```
username='david', password='123456'
```

密码以**明文**存储。同时 `init.sql` 中的种子数据也是明文写入。

## 根因分析

1. `init.sql` 建表语句：`password VARCHAR(100) NOT NULL`，字段本身可存哈希，无问题
2. 问题在写入逻辑：`init.sql` 直接 `INSERT ... VALUES ('david', '123456')`
3. `app/main.py` 的登录校验为明文比对：

```python
"SELECT username FROM users WHERE username=:u AND password=:p"
```

SQL 层直接比较明文，未做哈希比对。

## 影响范围

- 数据库一旦泄露（拖库、备份泄露、内部人员），**所有用户密码直接暴露**
- 用户在其他平台复用同一密码时，会引发撞库风险
- 违反通用的密码存储安全规范

## 修复建议

1. 引入 `passlib[bcrypt]` 或 `argon2-cffi`
2. 注册/改密时：`password_hash = hash(password)`，入库存哈希
3. 登录时：按 username 查出 hash，用 `verify(password, hash)` 比对，**不要用 SQL 比对密码**
4. 存量数据需要迁移（下次登录时重算哈希，或强制重置密码）

## 备注

该缺陷属于**代码审查 + 数据校验**发现，不是通过接口用例发现。
说明测试不能只做黑盒，必要时需要查看数据库和后端实现（灰盒测试）。
