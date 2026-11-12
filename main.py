from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text

app = FastAPI()

# Docker MySQL 映射在 3307
DB_URL = "mysql+pymysql://root:123456@127.0.0.1:3307/qa_shop?charset=utf8mb4"
engine = create_engine(DB_URL, pool_pre_ping=True)

class LoginRequest(BaseModel):
    username: str
    password: str

class OrderRequest(BaseModel):
    product_id: int
    quantity: int
    token: str

@app.post("/login")
def login(req: LoginRequest):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT username FROM users WHERE username=:u AND password=:p"),
            {"u": req.username, "p": req.password},
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"token": f"token-{req.username}"}

@app.get("/products")
def list_products():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, price, stock FROM products")).mappings().all()
    items = [dict(r) for r in rows]
    return {"total": len(items), "items": items}

@app.get("/products/{product_id}")
def get_product(product_id: int):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name, price, stock FROM products WHERE id=:id"),
            {"id": product_id},
        ).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="商品不存在")
    return dict(row)

@app.post("/orders")
def create_order(req: OrderRequest):
    if not req.token.startswith("token-"):
        raise HTTPException(status_code=401, detail="未登录")
    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="数量必须大于0")

    with engine.begin() as conn:
        p = conn.execute(
            text("SELECT id, name, price, stock FROM products WHERE id=:id"),
            {"id": req.product_id},
        ).mappings().fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="商品不存在")
        if p["stock"] < req.quantity:
            raise HTTPException(status_code=400, detail="库存不足")

        conn.execute(
            text("UPDATE products SET stock=stock-:q WHERE id=:id"),
            {"q": req.quantity, "id": req.product_id},
        )
        result = conn.execute(
            text("INSERT INTO orders (product_id, quantity, amount, status) VALUES (:pid, :q, :amt, 'PAID')"),
            {"pid": req.product_id, "q": req.quantity, "amt": float(p["price"]) * req.quantity},
        )
        order_id = result.lastrowid

    return {"order_id": order_id, "product_id": req.product_id, "quantity": req.quantity, "status": "PAID"}