from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

USERS = {"david": "123456"}
PRODUCTS = [
    {"id": 1, "name": "iPhone", "price": 5999.0, "stock": 100},
    {"id": 2, "name": "MacBook", "price": 12999.0, "stock": 50},
]

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(req: LoginRequest):
    if USERS.get(req.username) != req.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"token": f"token-{req.username}"}

@app.get("/products")
def list_products():
    return {"total": len(PRODUCTS), "items": PRODUCTS}

@app.get("/products/{product_id}")
def get_product(product_id: int):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="商品不存在")