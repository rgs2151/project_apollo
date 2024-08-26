from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from UserManager.accounts.google.model import Google
from UserManager.models import UserDetails
from utility.views import APIException


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
        

class StateAuthentication(BaseAuthentication):

    @staticmethod
    def get_state(request: Request):
        state_header = request.headers.get('State', None)
        state_cookie = request.COOKIES.get('State', None)
        return state_header if state_header else state_cookie
    
    def authenticate(self, request: Request):
        
        state = self.get_state(request)

        if state: 
            request.state = state
            return
    
        self.authenticate_failed_response(request, "state missing")


    def authenticate_failed_response(self, request, message="unauthorized access"):
        raise AuthenticationFailed(detail=APIException("Forbidden", message, status_code=403).get_response().data)


class TokenAuthentication(BaseTokenAuthentication):


    def authenticate(self, request):
        
        auth_token = self.get_token(request)

        try: token_data = UserDetails.decrypt_token(auth_token)
        except Exception:
            request.user = None
            request.user_details = None
            self.authenticate_failed_response(request)

        access_token = token_data.get("access_token", None)

        status, user_details = UserDetails.validate_token(auth_token)

        if (not status) or (not access_token) or (not Google.validate_token(access_token)):
            request.user = None
            request.user_details = None
            self.authenticate_failed_response(request)

        else:
            request.user = user_details.user
            request.user_details = user_details
            
    
    def authenticate_failed_response(self, request, message="unauthorized access"):
        raise AuthenticationFailed(detail=APIException("Forbidden", message, status_code=403).get_response().data)



