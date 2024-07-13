from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.request import Request
from django.shortcuts import render
from .models import UserDetails
from utility.views import APIException, get_url_or_named_url


class RedirectException(AuthenticationFailed):
    def __init__(self, detail, redirect_url):
        super().__init__(detail)
        self.redirect_url = redirect_url


class TokenAuthentication(BaseAuthentication):


    def authenticate(self, request: Request):
        
        auth_header = request.headers.get('Authorization', None)
        auth_cookie = request.COOKIES.get('Authorization', None)
        print(auth_header)
        print(auth_cookie)
        
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header.split(' ')[1]
            try:
                # Validate the token and get the user
                
                status, user_details = UserDetails.validate_token(auth_token)
                if not status or not isinstance(user_details, UserDetails):
                    self.authenticate_failed_response(request)

                request.user = user_details.user
                request.user_details = user_details
            
            except Exception:
                request.user = None
                request.user_details = None
                self.authenticate_failed_response(request)


        elif auth_cookie and auth_cookie.startswith('Bearer '):
            auth_token = auth_cookie.split(' ')[1]
            try:
                # Validate the token and get the user
                
                status, user_details = UserDetails.validate_token(auth_token)
                if not status or not isinstance(user_details, UserDetails):
                    self.authenticate_failed_response(request)

                request.user = user_details.user
                request.user_details = user_details
            
            except Exception:
                request.user = None
                request.user_details = None
                self.authenticate_failed_response(request)
        

        else:
            request.user = None
            request.user_details = None
            self.authenticate_failed_response(request)


    def authenticate_failed_response(self, request: Request, message="unauthorized access"):
        detail = APIException("Forbidden", message, status_code=403).get_response().data
        raise AuthenticationFailed(detail=detail)

