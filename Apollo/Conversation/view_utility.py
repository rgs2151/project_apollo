# this is temperory stash for code that will go to UserManager.utility module
from rest_framework.request import Request
from rest_framework.pagination import PageNumberPagination
from utility.views import MongoFilteredListView


class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def set_page_size(self, size: int):
        if not isinstance(size, int): raise TypeError("size should be an integer")
        self.page_size = size


class UserManagerUtilityMixin:

    @staticmethod
    def get_user_id(request: Request):
        if not  hasattr(request, "user_details"): return
        return request.user_details.user.id


# class UserManagerFilteredListView(MongoFilteredListView):

#     @staticmethod
#     def get_user_id(request: Request):
#         if not  hasattr(request, "user_details"): return
#         return request.user_details.user.id
    




