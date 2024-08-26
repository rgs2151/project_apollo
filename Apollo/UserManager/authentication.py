from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.request import Request
from django.shortcuts import render
from .models import UserDetails
from utility.views import APIException
from UserManager.accounts.google.auhentication import TokenAuthentication as GoogleTokenAuthentication


class BaseTokenAuthentication(BaseAuthentication):

    @staticmethod
    def get_token(request: Request):

        token = None

        auth_header = request.headers.get('Authorization', None)
        if auth_header: token = auth_header

        if not token:
            auth_cookie = request.COOKIES.get('Authorization', None)
            if auth_cookie: token = auth_cookie
        
        if token:
            splits = token.split(" ")
            if not len(splits) == 2: return None
            token = splits[-1]

        return token

    @staticmethod
    def get_refresh_token(request: Request):
        auth_header = request.headers.get('Refresh', None)
        if auth_header: return auth_header

        auth_cookie = request.COOKIES.get('Refresh', None)
        if auth_cookie: return auth_cookie
        

class RefreshTokenAuthentication(BaseTokenAuthentication):


    def authenticate(self, request: Request):
        
        refresh_token = self.get_refresh_token(request)
        
        if refresh_token and refresh_token.startswith('Bearer '):
            refresh_token = refresh_token.split(' ')[1]
          
        else:
            request.user = None
            request.user_details = None
            self.authenticate_failed_response(request)

        try:
            # Validate the token and get the user
            status, user_details = UserDetails.validate_refresh_token(refresh_token)
            if not status or not isinstance(user_details, UserDetails):
                self.authenticate_failed_response(request)

            request.user = user_details.user
            request.user_details = user_details
        
        except Exception:
            request.user = None
            request.user_details = None
            self.authenticate_failed_response(request)
    

    def authenticate_failed_response(self, request, message="unauthorized access"):
        raise AuthenticationFailed(detail=APIException("Forbidden", message, status_code=403).get_response().data)
    

class TokenAuthentication(BaseTokenAuthentication):


    def default_authentication(self, request: Request):

        auth_token = self.get_token(request)

        if not auth_token:
            request.user = None
            request.user_details = None
            self.authenticate_failed_response(request)

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
    

    def authenticate(self, request: Request):

        auth_token = self.get_token(request)

        if not auth_token:
            request.user = None
            request.user_details = None
            self.authenticate_failed_response(request)

        try: token_data = UserDetails.decrypt_token(auth_token)
        except Exception:
            request.user = None
            request.user_details = None
            self.authenticate_failed_response(request)

        if token_data and token_data.get("login_type"):

            if token_data.get("login_type") == "google":
                instance = GoogleTokenAuthentication()
                instance.authenticate(request)

            else:
                request.user = None
                request.user_details = None
                self.authenticate_failed_response(request)
                
        else: self.default_authentication(request)


    def authenticate_failed_response(self, request, message="unauthorized access"):
        raise AuthenticationFailed(detail=APIException("Forbidden", message, status_code=403).get_response().data)

