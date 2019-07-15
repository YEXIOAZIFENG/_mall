from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class MyPage(PageNumberPagination):
    page_size = 5  # 默认每页数量
    max_page_size = 10  # 默认最多每页几个
    page_query_param = "page"
    page_size_query_param = "pagesize"

    def get_paginated_response(self, data):
        """
        构建响应对象，响应对象中构建返回数据格式
        :param data: 分页子集序列化的结果
        :return: 封装了具体数据格式响应对象
        """

        return Response({
            "counts": self.page.paginator.count,  # 数据总数
            "lists": data,  # 子集序列化结果
            "page": self.page.number,  # 当前页
            "pages": self.page.paginator.num_pages,  # 总页数
            "pagesize": self.page_size,  # 后端默认每页数量
        })
