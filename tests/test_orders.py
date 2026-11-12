import requests

def test_create_order_success(base_url, token):
    r = requests.post(f"{base_url}/orders", json={"product_id": 2, "quantity": 1, "token": token})
    assert r.status_code == 200
    assert "order_id" in r.json()

def test_create_order_no_token(base_url):
    r = requests.post(f"{base_url}/orders", json={"product_id": 2, "quantity": 1, "token": ""})
    assert r.status_code == 401

def test_create_order_quantity_zero(base_url, token):
    r = requests.post(f"{base_url}/orders", json={"product_id": 2, "quantity": 0, "token": token})
    assert r.status_code == 400

def test_create_order_product_not_found(base_url, token):
    r = requests.post(f"{base_url}/orders", json={"product_id": 999, "quantity": 1, "token": token})
    assert r.status_code == 404

def test_create_order_missing_field(base_url, token):
    r = requests.post(f"{base_url}/orders", json={"product_id": 2, "token": token})
    assert r.status_code == 422