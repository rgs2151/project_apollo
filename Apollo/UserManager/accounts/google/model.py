
from UserManager.models import *
from UserManager.settings import USER_MANAGER_SETTINGS
from utility.views import get_url_or_named_url

import urllib.parse
import hashlib
import os
import requests


class Google(models.Model):

    RESPONSE_TYPE = 'code'

    SCOPE = 'openid email'

    ACCESS_TYPE = 'offline'

    PROMPT = "consent"

    GRANT_TYPE = "authorization_code"

    AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'

    TOKEN_URL = "https://oauth2.googleapis.com/token"

    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v2/tokeninfo"

    user_details = models.OneToOneField(UserDetails, models.DO_NOTHING, primary_key=True)
    google_id = models.CharField(max_length=55, blank=False, null=True)
    refresh_token = models.CharField(max_length=200, blank=False, null=True)

    class Meta:
        db_table = 'user_account_google'


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.login_type: LoginType = LoginType.make_sure_has("google", api_version="v2")


    @staticmethod
    def generate_state(): return hashlib.sha256(os.urandom(1024)).hexdigest()


    @classmethod
    def get_authentication_url(cls, request, login_hint=""):
        
        redirect_url = USER_MANAGER_SETTINGS.get("REDIRECT").get("GOOGLE")
        redirect_url = get_url_or_named_url(redirect_url, request)
        
        params = {
            'response_type': cls.RESPONSE_TYPE,
            'client_id': USER_MANAGER_SETTINGS.get("ACCOUNTS").get("GOOGLE").get("CLIENT_ID"),
            'scope': cls.SCOPE,
            'redirect_uri': redirect_url,
            'state': cls.generate_state(),
            'login_hint': login_hint,
            'access_type': cls.ACCESS_TYPE
        }

        return f"{cls.AUTH_URL}?{urllib.parse.urlencode(params)}", params['state']
    

    @classmethod
    def initialize_for_user_details(cls, user_details: UserDetails):
        
        if not isinstance(user_details, UserDetails):
            raise TypeError(f"user_details should be of type UserManagement.UserDetails")
        
        if not user_details.login_type != cls.login_type:
            raise ValueError(f"login type for the user_details is not google. Required LoginType[{cls.login_type.id}]")
        

        instance = cls(user_details = user_details)
        instance.save()
        return instance


    @staticmethod
    def get_redirect_data(request: Request):
        redirected_to_url = request.get_full_path()
        query = urllib.parse.urlsplit(redirected_to_url).query
        return dict(urllib.parse.parse_qsl(query))
    

    @classmethod
    def get_token(cls, request: Request):
        # requires redirected url from google
        # refresh token is returned here
        
        redirected_data = cls.get_redirect_data(request)
        redirect_url = USER_MANAGER_SETTINGS.get("REDIRECT").get("GOOGLE")
        redirect_url = get_url_or_named_url(redirect_url, request)

        payload = {
            "code": redirected_data.get("code", ""),
            "client_id": USER_MANAGER_SETTINGS.get("ACCOUNTS").get("GOOGLE").get("CLIENT_ID"),
            "client_secret": USER_MANAGER_SETTINGS.get("ACCOUNTS").get("GOOGLE").get("CLIENT_SECRET"),
            "redirect_uri": redirect_url,
            "grant_type": cls.GRANT_TYPE,
            "access_type": cls.ACCESS_TYPE,
            "prompt": cls.PROMPT
        }

        response = requests.post(cls.TOKEN_URL, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=payload)
        if response.status_code == 200: 
            return response.json()

        return {}
        

    @classmethod
    def create_google_token(cls, user_details: UserDetails, google_id: int, refresh_token: str):
        instance = cls(
            user_details = user_details,
            google_id = google_id,
            refresh_token = refresh_token,
        )
        instance.save()
        return instance


    @classmethod
    def get_user_info(cls, token: str):
        response = requests.get(cls.USER_INFO_URL, headers={'Authorization': f'Bearer {token}'})
        if response.status_code == 200:
            user_info = response.json()
            return user_info


    def issue_token(self, request, access_token: str) -> str:
        add_to_token = {
            "login_type": Google.login_type.name,
            "access_token": access_token
        }
        return self.user_details.issue_token(request, add_to_token=add_to_token)


    def refresh(self):

        if not self.refresh_token: return
        
        params = {
            'client_id': USER_MANAGER_SETTINGS.get("ACCOUNTS").get("GOOGLE").get("CLIENT_ID"),
            'client_secret': USER_MANAGER_SETTINGS.get("ACCOUNTS").get("GOOGLE").get("CLIENT_SECRET"),
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }

        response = requests.post(self.TOKEN_URL, data=params)

        if response.status_code == 200:
            return response.json().get("access_token")
        
        else:
            self.refresh_token = None
            self.save()


    @classmethod
    def validate_token(cls, access_token):
        response = requests.get(cls.USER_INFO_URL, headers={'Authorization': f'Bearer {access_token}'})
        return response.status_code == 200

        # token_info_url = cls.TOKEN_INFO_URL + f"?access_token={access_token}"
        # response = requests.get(token_info_url)


    @staticmethod
    def create_google_user(details: dict, request: Request) -> UserDetails:
        user = UserDetails.create_django_email_user(**details, set_password=False)
        user_details = UserDetails.initialize_user_details(user, request)
        login_type = LoginType.make_sure_has("google", "v2")
        user_details.login_type = login_type
        user_details.save()
        return user_details
    

    @classmethod
    def create_or_update_instance(cls, user_details: UserDetails, token_data: dict, user_info: dict):

        if not isinstance(user_details, UserDetails):
            raise TypeError("user_details should be of type UserManager.models.UserDetails")

        if not 'refresh_token' in token_data:
            raise ValueError("token_data does not contain refresh_token")
        
        if not 'id' in user_info:
            raise ValueError("user_info does not contain id")
        
        if Google.objects.filter(user_details=user_details).exists():
            google_token = Google.objects.filter(user_details=user_details).first()
            google_token.refresh_token = token_data['refresh_token']

            # just in case
            if not google_token.google_id == user_info['id']:
                google_token.google_id = user_info['id']

            google_token.save()
        
        else:
            # issue auth token from google
            google_token = Google.create_google_token(user_details, user_info['id'], token_data['refresh_token'])

        return google_token


    @classmethod
    def get_or_create_instance(cls, request):
        
        token_data = Google.get_token(request)

        access_token = token_data.get('access_token', None)

        if not access_token:
            # raise APIException("Internal Server Error", "something went wrong!", status_code=500)
            return None, access_token

        user_info = Google.get_user_info(access_token)
        if not user_info:
            # raise APIException("Internal Server Error", "something went wrong!", status_code=500)
            return None, access_token
        
        # try registering user
        try: 
            register_user = Google.user_info_split_to_user_details(user_info)
            user_details = Google.create_google_user(register_user, request)

        # user already exists
        except ValueError:
            user_details = UserDetails.objects.filter(user__email=register_user["email"]).first()

        return Google.create_or_update_instance(user_details, token_data, user_info), access_token


    @staticmethod
    def user_info_split_to_user_details(user_info):
        splits = user_info["name"].split(" ")
        first_name = splits[0]
        last_name = " ".join(splits[1:]) if len(splits) > 1 else ""
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": user_info["email"]
        }

