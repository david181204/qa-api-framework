import requests

def test_products_list(base_url):
    r = requests.get(f"{base_url}/products")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 2
    assert len(data["items"]) == data["total"]

def test_product_detail_exists(base_url):
    r = requests.get(f"{base_url}/products/2")
    assert r.status_code == 200
    assert r.json()["id"] == 2

def test_product_not_found(base_url):
    r = requests.get(f"{base_url}/products/999")
    assert r.status_code == 404

def test_product_invalid_id(base_url):
    r = requests.get(f"{base_url}/products/abc")
    assert r.status_code == 422