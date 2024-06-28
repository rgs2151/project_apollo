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
        
        if request.user_details.email_verified_at:
            message = "email not verified"
            return False , message
        
        return True, message


class IsUserValid(BasePermission):

    @staticmethod
    def permission(request: Request):

        message = None

        permissions = [IsLoggedIn, IsEmailVerified]
        for permission in permissions:
            status, message = permission.permission(request)
            if not status: return status, message

        return True, message


class HasAdminPermissions(BasePermission):

    @staticmethod
    def permission(request: Request):

        message = None

        status, message = IsUserValid.permission(request)
        if not status: return status, message

        if not request.user_details.user.is_staff:
            message = "unautorized"
            return False, message
        
        return True, message



