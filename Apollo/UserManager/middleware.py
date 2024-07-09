from django.utils.deprecation import MiddlewareMixin
from utility.views import APIException

from .models import UserDetails


# This logic will be moved to restframework authenticator class
class TokenAuthMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header.split(' ')[1]
            try:
                # Validate the token and get the user
                
                status, user_details = UserDetails.validate_token(auth_token)
                if not status or not isinstance(user_details, UserDetails):
                    return APIException("FORBIDDEN", "NOT Authorization", status_code=405).get_response()

                request.user = user_details.user
                request.user_details = user_details
            
            except Exception:
                request.user = None
                request.user_details = None
        
        else:
            request.user = None
            request.user_details = None
