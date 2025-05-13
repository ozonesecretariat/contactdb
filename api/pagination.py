import rest_framework.pagination


class PageNumberPagination(rest_framework.pagination.PageNumberPagination):
    page_size_query_param = "page_size"
