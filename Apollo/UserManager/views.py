from typing import Any
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.exceptions import NotFound
from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth.models import Group
from .settings import USER_MANAGER_SETTINGS
# from django.http import Http404

from utility.views import *
from .models import *
from .serializers import *
from .authentication import TokenAuthentication
from .permissions import UserAdminPermissions
from .pagination import *

from django.db import models
from rest_framework.serializers import ModelSerializer
from rest_framework.pagination import PageNumberPagination


def pagenotfound(request, exception):
    return render(request, "user_404.html", status=404)


class UserRegister(APIView):
    
    @exception_handler()
    @request_schema_validation(schema={
        "first_name": {"type": "string", "required": False, "empty": False, "nullable": True, "minlength": 3, "maxlength": 20},
        "last_name": {"type": "string", "required": False, "empty": False, "nullable": True, "minlength": 1, "maxlength": 20},
        "email": {"type": "string", "required": True, "empty": False, "nullable": True, "minlength": 5, "maxlength": 75, "check_with": "email"},
        "password": {"type": "string", "required": True, "empty": False, "nullable": False, "minlength": 8, "maxlength": 36, "check_with": "password"},
    })
    def post(self, request: Request):
        
        _request = request.data
        
        try:
            user = UserDetails.create_django_email_user(**_request)
        except ValueError:
            raise APIException("AlreadyExists", "user with email already exists", status_code=400)
        
        # email_secret send through email handled here if EMAIL.SENT = True
        
        user_details = UserDetails.initialize_user_details(user, request)

        email_verification_link, email_sent = user_details.issue_email_secret(request)
        
        user_details_serialized = UserDetailsSerializer(user_details).data
        
        token = user_details.issue_token(request)
        
        response = {"auth_token": token, 'user_details': user_details_serialized, "verification_email_sent": email_sent}
        
        # on testing mode email_verification_link is to be sent in response because EMAIL.SENT = False
        if USER_MANAGER_SETTINGS.get("TESTING_MODE", False):
            response['email_verification_link'] = email_verification_link
        

        response = Response(response)

        if USER_MANAGER_SETTINGS["ENABLE_COOKIES"]:
            expiery = USER_MANAGER_SETTINGS["TOKEN"].get("TOKEN_EXPIERY_TIME").total_seconds()
            response.set_cookie("Authorization", f"Bearer {token}", expires=expiery)


        return response
    

class UserLogin(APIView):
    
    @exception_handler()
    @request_schema_validation(schema={
        "email": {"type": "string", "required": True, "empty": False, "nullable": True, "minlength": 5, "maxlength": 75, "check_with": "email"},
        "password": {"type": "string", "required": True, "empty": False, "nullable": False, "minlength": 6, "maxlength": 36, "check_with": "password"}
    })
    
    def post(self, request: Request):
        
        request_ = request.data
        
        if not UserDetails.objects.filter(user__email = request_['email']).exists():
            raise APIException("InvalidEmail", "email not registered", status_code=404)
            
        user_details_instance: UserDetails = UserDetails.objects.get(user__email = request_['email'])
        
        if not user_details_instance.user.check_password(request_['password']):
            raise APIException("InvalidPassword", "password incorrect", status_code=405)
        
        token = user_details_instance.issue_token(request)
        
        response = Response({"auth_token": token})

        if USER_MANAGER_SETTINGS["ENABLE_COOKIES"]:
            expiery = USER_MANAGER_SETTINGS["TOKEN"].get("TOKEN_EXPIERY_TIME").total_seconds()
            response.set_cookie("Authorization", f"Bearer {token}", expires=expiery)

        return response


class UserDetailsView(APIView):
    
    authentication_classes = [TokenAuthentication]
    
    @exception_handler()
    def get(self, request: Request):
        return Response({"user_details": UserDetailsSerializer(request.user_details).data})


class VerifyEmailRedirect(APIView):
    
    @exception_handler()
    def get(self, request: Request):
        return render(request, "user_email_verified.html")


class VerifyEmail(APIView):
    
    @exception_handler()
    def get(self, request: Request, secret: str):
        
        status, user_details_instance = UserDetails.validate_email(secret)
        
        if not status: raise Http404(request)
        
        # will go to a public page! user will have to login if not logged in!
        
        # done in order to avoid django testserver url
        url = USER_MANAGER_SETTINGS["REDIRECT"]["EMAIL_VERIFICATION"]
        url = get_url_or_named_url(url, request)
        url = url.split("//")[-1]
        url = "/" + "/".join(url.split("/")[1:])

        return redirect(url)


class ResendVerificationMail(APIView):
    
    authentication_classes = [TokenAuthentication]
    
    @exception_handler()
    def post(self, request: Request):
        
        user_details: UserDetails = request.user_details
        
        email_verification_link, email_sent = user_details.issue_email_secret(request)
        
        if not email_verification_link:
            raise APIException("OnCooldown", "email verification cooldown", status_code=200)
        
        return Response({"status": "success"})


class UserUpdate(APIView):
    
    authentication_classes = [TokenAuthentication]
    
    @exception_handler()
    @request_schema_validation(schema={
        "first_name": {"type": "string", "required": False, "empty": False, "nullable": True, "minlength": 3, "maxlength": 20},
        "last_name": {"type": "string", "required": False, "empty": False, "nullable": True, "minlength": 1, "maxlength": 20},
        "email": {"type": "string", "required": False, "empty": False, "nullable": True, "minlength": 5, "maxlength": 20, "check_with": "email"},
    })
    def put(self, request: Request):

        request_ = request.data
        if not request.data:
            raise APIException("RequestValidationFailed", "request cannot be empty", status_code=400)
        
        try:
            request.user_details.update_user(request_)
            user_detials_instance = UserDetails.objects.get(user__id=request.user_details.user.id)
            response = {"user_details": UserDetailsSerializer(user_detials_instance).data}
            
            if "email" in request_:
                email_verification_link, email_sent = user_detials_instance.issue_email_secret(request)
                response['email_sent'] = email_sent
                if USER_MANAGER_SETTINGS.get("TESTING_MODE", False):
                    response['email_verification_link'] = email_verification_link
                
            
            return Response(response)
            
        except ValueError:
            raise APIException("InvalidEmail", "email already exists", status_code=400)


class UserGet(APIView):
    
    authentication_classes = [TokenAuthentication]
    
    @exception_handler()
    def get(self, request: Request): 
        return Response({"user_details": UserDetailsSerializer(request.user_details).data})


class UserPasswordChangeRequest(APIView):
    
    # authentication_classes = [TokenAuthentication]
    
    @exception_handler()
    @request_schema_validation(schema={
        "email": {"type": "string", "required": True, "empty": False, "nullable": True, "minlength": 5, "maxlength": 75, "check_with": "email"},
    })
    def post(self, request: Request):
        
        req = request.data
        if not UserDetails.objects.filter(user_id__email = req["email"], archived=0).exists():
            raise APIException("NotFound", "user with email not found", status_code=404)

        user_details = UserDetails.objects.filter(user_id__email = req["email"], archived=0).get()
        
        password_change_link, email_sent = user_details.issue_password_change(request)
        
        if not password_change_link:
            raise APIException("OnCooldown", "password change request on cooldown", status_code=200)
        
        return Response({"status": "success"})


class UserPasswordChange(APIView):
    
    @exception_handler()
    def get(self, request: Request, secret: str):
        
        # will go to a public page! user will have to login if not logged in!
        
        status, user_details_instance = UserDetails.check_password_change_secret(secret)
        if not status: raise Http404(request)

        url = USER_MANAGER_SETTINGS["REDIRECT"]["PASSWORD_CHANGE"]
        # temperorily done here !!
        url = get_url_or_named_url(url, request, kwargs={"secret": secret})
        url = url.split("//")[-1]
        url = "/" + "/".join(url.split("/")[1:])
        
        return redirect(f"{url}")


class UserChangePasswordRedirect(APIView):

    @exception_handler()
    def get(self, request: Request, secret: str):
        return render(request, 'user_passwordchange.html')


class UserChangePassword(APIView):
    
    @exception_handler()
    @request_schema_validation({
        "secret": {"type": "string", "required": True, "empty": False, "nullable": False, "minlength": 36, "maxlength": 524},
        "new_password": {"type": "string", "required": True, "empty": False, "nullable": False, "minlength": 6, "maxlength": 36, "check_with": "password"}
    })
    def post(self, request: Request):
        
        request = request.data
        
        status, user_details_instance = UserDetails.change_password(request.get("secret"), request.get("new_password"))
        if not status:
            raise APIException("UnAuthorized", "password change failed", status_code=403)
        
        return Response({"status": "success"})


class LogOut(APIView):

    authentication_classes=[TokenAuthentication]

    @exception_handler()
    def post(self, request: Request):
        
        response = Response({"status": False})
        if request.COOKIES and request.COOKIES.get("Authorization", False):
            response = Response({"status": True})
            response.delete_cookie("Authorization")
        
        return response


# Admin Routes for Dashboard

class UserDashboard(FilteredListView):

    authentication_classes=[TokenAuthentication]
    permission_classes = [UserAdminPermissions]

    model = UserDetails
    serializer = UserDetailsAdminDashboardSerializer
    pagination = DefaultPagination()

    allow_filters = {
        "user__username": {"type": "string", "required": False, "empty": False}
    }


class Groups(FilteredListView):

    authentication_classes=[TokenAuthentication]
    permission_classes = [UserAdminPermissions]

    model = Group
    serializer = GroupSerializer
    pagination = DefaultPagination()

    allow_filters = {
        "name": {"type": "string", "required": False, "empty": False}
    }


class GroupManager(APIView):


    @exception_handler()
    @request_schema_validation({
        "name": {"type": "string", "required": True, "empty": False}
    })
    def post(self, request: Request):

        req = request.data
        name=req.get("name", "")
        if Group.objects.filter(name=name).exists():
            raise APIException("Already Exists", "group with the name already exists", status_code=400)
        
        group_instance = Group(name=name)
        group_instance.save()

        return Response({"group": GroupSerializer(group_instance).data})


    @exception_handler()
    @request_schema_validation({
        "id": {"type": "integer", "required": True, "empty": False, 'min': 0},
        "name": {"type": "string", "required": True, "empty": False}
    })
    def put(self, request: Request):

        req = request.data
        group_id = req.get("id")
        group_name = req.get("name")

        if not Group.objects.filter(id=group_id).exists():
            raise APIException("Not Found", "group not found", status_code=404)
        
        group_instance = Group.objects.filter(id=group_id).first()
        
        if group_instance.name == group_name:
            raise APIException("Bad Request", "group already has the name", status_code=404)
        
        group_instance.name = group_name
        group_instance.save()

        return Response({"group": GroupSerializer(group_instance).data})


    @exception_handler()
    @request_schema_validation({
        "id": {"type": "integer", "required": True, "empty": False, 'min': 0},
        "name": {"type": "string", "required": True, "empty": False}
    })
    def delete(self, request: Request):

        req = request.data
        group_id = req.get("id")
        group_name = req.get("name")

        if not Group.objects.filter(id=group_id).exists():
            raise APIException("Not Found", "group not found", status_code=404)
        
        group_instance = Group.objects.filter(id=group_id).first()
        
        if group_instance.name != group_name:
            raise APIException("Bad Request", "confirmation group name invalid", status_code=400)

        group_instance.delete()

        return Response({"group": GroupSerializer(group_instance).data})


class UserGroupManager(APIView):


    @exception_handler()
    @request_schema_validation({
        "user_id": {"type": "integer", "required": True, "min": 0},
        "group_ids": {
            "type": "list", "required": True, "empty": False, "schema": {
                "type": "integer", "min": 0
            }
        }
    })
    def post(self, request: Request):

        req = request.data
        user_id = req.get("user_id")
        group_ids = req.get("group_ids")

        
        if not UserDetails.objects.filter(user__id=user_id).exists():
            raise APIException("Not Found", "user with id not found", status_code=404)
        
        user_details_instance = UserDetails.objects.filter(user__id=user_id).first()


        for _id in group_ids:
            if not Group.objects.filter(id=_id).exists():
                raise APIException("Not Found", f"group with id: {_id} not found", status_code=404)
                    

        if user_details_instance.user.groups.filter(id__in=group_ids).exists():
            raise APIException("Already Exists", f"group already assigned to user", status_code=400)

        
        for _id in group_ids:
            group_instance = Group.objects.filter(id=_id).first()
            user_details_instance.user.groups.add(group_instance)

        user_details_instance.user.save()

        user_detail_instance = UserDetails.objects.filter(user__id=user_id).first()
        return Response({"user_details": UserDetailsAdminDashboardSerializer(user_detail_instance).data})


    @exception_handler()
    @request_schema_validation({
        "user_id": {"type": "integer", "required": True, "min": 0},
        "groups": {
            "type": "list", "required": True, "empty": False, "schema": {
                "type": "dict", "schema": {

                    "id": {"type": "integer", "required": True, "min": 0},
                    "name": {"type": "string", "required": True, "empty": False},
                
                }
            }
        }
    })
    def delete(self, request: Request):

        req = request.data
        user_id = req.get("user_id")
        groups = req.get("groups")


        if not UserDetails.objects.filter(user__id=user_id).exists():
            raise APIException("Not Found", "user with id not found", status_code=404)
        
        user_details_instance = UserDetails.objects.filter(user__id=user_id).first()

        for group_data in groups:
            if not user_details_instance.user.groups.filter(id=group_data["id"]).exists():
                raise APIException("Not Found", f"group with id: {group_data['id']} not found", status_code=404)
            
        removed = []
        for group_data in groups:
            group_instance = user_details_instance.user.groups.filter(id=group_data["id"]).first()
            user_details_instance.user.groups.remove(group_instance)
            removed.append(GroupSerializer(group_instance).data)

        return Response({"groups": removed})

