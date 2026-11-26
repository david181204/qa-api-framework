"""商品模块接口封装。"""
from api.base_api import BaseApi


class ProductApi(BaseApi):
    """只描述"商品接口有哪些操作"，不写断言。"""

    def list_all(self):
        """获取商品列表。

        命名用 list_all 而不是 list：list 是 Python 内置类型名，
        用它当方法名会被部分 lint 工具报 redefined-builtin。
        """
        return self.get("/products")

    def detail(self, product_id):
        """获取商品详情。

        注意：product_id 是 path 参数，必须用 f-string 拼进 URL；
        如果将来接口加分页（query 参数），则写成 self.get("/products", params={...})。
        """
        return self.get(f"/products/{product_id}")
