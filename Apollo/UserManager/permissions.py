from typing import Any
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.request import Request


class UserPermissions(BasePermission):

    @staticmethod
    def permission(request: Request):
        raise NotImplemented("permission's not implemented")


    def has_permission(self, request: Request, view):
        status, message = self.permission(request)
        if not status: self.message = message
        return status
    

    def has_object_permission(self, request, view, obj):
        status, message = self.permission(request)
        if not status: self.message = message
        return status


class IsLoggedIn(UserPermissions):

    @staticmethod
    def permission(request: Request):

        message = None

        if not hasattr(request, 'user_details'):
            message = "unauthorized please login to continue"
            return False, message

        return True, message


class IsEmailVerified(UserPermissions):
    

    @staticmethod
    def permission(request: Request):
        
        message = None

        if not request.user_details.email_verified_at:
            message = "email not verified"
            return False , message
        
        return True, message


class IsSuperUser(UserPermissions):


    @staticmethod
    def permission(request: Request):

        if not hasattr(request, "user_details"):
            return False, "no user permissions"
        
        if not request.user_details.user.is_superuser:
            return False , "no superuser permissions"

        return True, None


class HasAdminPermissions(UserPermissions):

    @staticmethod
    def permission(request: Request):

        message = None

        status, message = IsSuperUser.permission(request)
        if status: return status, message

        if not request.user_details.user.is_staff:
            message = "unautorized"
            return False, message
        
        return True, message


class HasGroupPermissions(UserPermissions):
    

    def __init__(self, group_name) -> None:
        super().__init__()
        self.group_name = group_name


    @staticmethod
    def permission(request: Request):
        return True, None


    def has_permission(self, request: Request, view):
        if not hasattr(request, "user_details"): return False
        status = request.user_details.user.groups.filter(name=self.group_name).exists()
        if not status: self.message = "user group unautorized"
        return status
    

    def __call__(self) -> Any: return self


class UserGroupPermissions(UserPermissions):

    def __init__(self, group_name) -> None:
        self.group_name = group_name


    def has_permission(self, request: Request, view):
        
        permissions = [IsLoggedIn, IsEmailVerified, HasGroupPermissions(self.group_name)]
        for permission in permissions:
            permission = permission()
            status = permission.has_permission(request, view)
            if not status: return status

        return True
    

    def has_object_permission(self, request, view, obj):

        permissions = [IsLoggedIn, IsEmailVerified, HasGroupPermissions(self.group_name)]
        for permission in permissions:
            permission = permission()
            status = permission.has_object_permission(request, view, obj)
            if not status: return status

        return True


class UserAdminPermissions(UserPermissions):


    def has_permission(self, request: Request, view):
        
        permissions = [IsLoggedIn, IsEmailVerified, HasAdminPermissions]
        for permission in permissions:
            permission = permission()
            status = permission.has_permission(request, view)
            if not status: return status

        return True
    

    def has_object_permission(self, request, view, obj):

        permissions = [IsLoggedIn, IsEmailVerified, HasAdminPermissions]
        for permission in permissions:
            permission = permission()
            status = permission.has_object_permission(request, view, obj)
            if not status: return status

        return True

