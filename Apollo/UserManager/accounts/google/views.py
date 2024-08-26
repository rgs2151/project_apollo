from UserManager.views import *
from utility.views import Request
from UserManager.accounts.google.model import Google
from datetime import timedelta
from .auhentication import StateAuthentication
from UserManager.authentication import TokenAuthentication


class AuthenticationURL(APIView):


    @exception_handler()
    @request_schema_validation(query_dict_schema={
        "for": {"required": False, "type": 'string', "check_with": "email"}
    })
    def get(self, request: Request):
        
        data = request.GET

        url, state = Google.get_authentication_url(request)

        response = redirect(url, status=200)

        if USER_MANAGER_SETTINGS["ENABLE_COOKIES"]:
            expiery = timedelta(hours=1).total_seconds()
            response.set_cookie("State", state, expires=expiery, httponly=True, secure=True)
        
        return response


class Redirect(APIView):

    authentication_classes = [StateAuthentication]
    
    @exception_handler()
    def get(self, request: Request):
        
        redirected_data = Google.get_redirect_data(request)
        
        if not redirected_data.get("state", ""):
            raise APIException("Forbidden", "state is missing")
        
        elif redirected_data.get("state", "") != request.state:
            raise APIException("Forbidden", "state invalid")
        
        google_token, access_token = Google.get_or_create_instance(request)
        if not google_token:
            raise APIException("Internal Server Error", "something went wrong!", status_code=500)

        token = google_token.issue_token(request, access_token)

        response = redirect(reverse("user-default-home") + f"?auth_token=Bearer {token}")

        if USER_MANAGER_SETTINGS["ENABLE_COOKIES"]:

            if "TOKEN" in USER_MANAGER_SETTINGS["ENABLE_COOKIES"]:
                expiery = USER_MANAGER_SETTINGS["TOKEN"].get("TOKEN_EXPIERY_TIME").total_seconds()
                response.set_cookie("Authorization", f"Bearer {token}", expires=expiery, httponly=True, secure=True)

        return response


class Refresh(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    def get(self, request: Request):
        
        if not Google.objects.filter(user_details=request.user_details).exists():
            raise APIException("Invalid Google User", "google user not found", status_code=404)
        
        google_token = Google.objects.filter(user_details=request.user_details).first()

        access_token = google_token.refresh()
        if not access_token:
            # token expiered redirect to google login page
            return redirect("user-google-auth-url", status=200)
        
        else:

            token = google_token.issue_token(request, access_token)

            response = redirect(reverse("user-default-home") + f"?auth_token=Bearer {token}")

            if USER_MANAGER_SETTINGS["ENABLE_COOKIES"]:

                if "TOKEN" in USER_MANAGER_SETTINGS["ENABLE_COOKIES"]:
                    expiery = USER_MANAGER_SETTINGS["TOKEN"].get("TOKEN_EXPIERY_TIME").total_seconds()
                    response.set_cookie("Authorization", f"Bearer {token}", expires=expiery, httponly=True, secure=True)

            return response



