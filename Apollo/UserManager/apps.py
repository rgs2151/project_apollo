from typing import Any
from django.apps import AppConfig
from django.conf import settings
from django.urls import get_resolver, get_callable
from rest_framework.test import APIRequestFactory
from .settings import USER_MANAGER_SETTINGS


class UsermanagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "UserManager"

    def ready(self):

        try: settings_defined = settings.__getattr__('USER_MANAGER_SETTINGS')
        except AttributeError: settings_defined = {}
        
        for k, v in settings_defined.items():
            USER_MANAGER_SETTINGS.update({k: v})

        # for k, v in USER_MANAGER_SETTINGS.items():
        #     settings_defined.update({k: v})
        
        stash = self.validate_app_settings()
        for msg in stash: print(msg)

    

    @staticmethod
    def validate_app_settings():
        stash = []
        stash += UsermanagerConfig.validate_email_settings()
        stash += UsermanagerConfig.validate_password_email()
        UsermanagerConfig.validate_redirect()
        return stash


    @staticmethod    
    def validate_email_settings():
        
        email_stash = []
        
        # when TESTING_MODE is set to True EMAIL.SEND is set False and the secret is returned in the response
        if USER_MANAGER_SETTINGS.get("TESTING_MODE", False):
            email_stash.append(f"WARNIGN: TESTING_MODE is enabled EMAIL.SENT will be set to False")
            USER_MANAGER_SETTINGS["EMAIL"]["SEND"] = False
            return email_stash


        email_settings = USER_MANAGER_SETTINGS.get('EMAIL', {})
        email_setting_valid = True
        
        if email_settings:
        
            # import when app is ready
            from utility.email import check_smtp_credentials, check_email
            
            if email_settings.get("SEND", False):
                
                for key in ["TEMPLATE", "SUBJECT", "FROM", "SMTP_USERNAME", "SMTP_PASSWORD"]:

                    if not key in email_settings:
                        email_stash.append(f"WARNING: UserManage.settings.EMAIL.SEND is True. EMAIL.{key} is not set")
                        email_setting_valid = False
                    
                    if key in email_settings:
                        
                        value = email_settings.get(key, "")
                        if not value:
                            email_stash.append(f"WARNING: UserManage.settings.EMAIL.SEND is True. EMAIL.{key} is set empty")
                            email_setting_valid = False
                            
                        if key in ["SMTP_USERNAME", "FROM"]:
                            if not check_email(email_settings[key]):
                                email_stash.append(f"WARNING: UserManage.settings.EMAIL.{key} should match valid email pattern")
                                email_setting_valid = False


                template = email_settings.get("TEMPLATE", "")
                if not '{link}' in template:
                    email_stash.append(f"WARNING: UserManage.settings.EMAIL.SEND is True. EMAIL.TEMPLATE does not have secret link.")
                    email_stash.append("EMAIL.TEMPLATE should include \"link\" E.G. \"Please click the following link to verify your account: {link}\"")
                    email_setting_valid = False

        
        if email_setting_valid:
            
            # email checks
            if not check_email(email_settings["SMTP_USERNAME"]):
                email_stash.append(f"\033[93mWARNING: UserManager.settings.EMAIL SMTP USER LOGIN FAILED\033[0m")  
            
            email_user = email_settings["SMTP_USERNAME"]
            email_user_password = email_settings["SMTP_PASSWORD"]
            error = check_smtp_credentials(email_user, email_user_password)
            if error:
                email_setting_valid = False
                email_stash.append(f"\033[93mWARNING: UserManager.settings.EMAIL SMTP USER LOGIN FAILED\n{error}\033[0m") 

        
        if not email_setting_valid:
            email_settings["SEND"] = False
            email_stash.append("\033[91mWARNING: UserManage.settings.EMAIL is INVALID. EMAIL VERIFICATION MAIL IS SET OFF !!\033[0m")


        if email_setting_valid:
            email_stash.append("UserManager: email verification enalbled")
            email_stash.append(f"UserManager.EMAIL.SMTP_USERNAME: {email_settings['SMTP_USERNAME']}")
            email_stash.append(f"UserManager.EMAIL.FROM: {email_settings['FROM']}")
            
        return email_stash
    
    
    @staticmethod
    def validate_password_email():
        
        password_stash = []
        
        password_settings = USER_MANAGER_SETTINGS.get('PASSWORD', {})
        
        password_email_setting_valid = True
        if not "EMAIL" in password_settings:
            password_stash.append("\033[91mWARNING: PASSWORD.EMAIL is not set password chanage will be disabled\033[0m")
            
        else:
            password_email_settings = password_settings["EMAIL"]
            
            for key in ["TEMPLATE", "SUBJECT"]:

                if not key in password_email_settings:
                    password_stash.append(f"WARNING: UserManage.settings.PASSWORD.EMAIL.SEND is True. EMAIL.{key} is not set")
                    password_email_setting_valid = False
                
                if key in password_email_settings:
                    
                    value = password_email_settings.get(key, "")
                    if not value:
                        password_stash.append(f"WARNING: UserManage.settings.PASSWORD.EMAIL.SEND is True. EMAIL.{key} is set empty")
                        password_email_setting_valid = False


            template = password_email_settings.get("TEMPLATE", "")
            if not '{link}' in template:
                password_stash.append(f"WARNING: UserManage.settings.PASSWORD.EMAIL.SEND is True. PASSWORD.EMAIL.TEMPLATE does not have secret link.")
                password_stash.append("PASSWORD.EMAIL.TEMPLATE should include \"link\" E.G. \"Please click the following link to verify your account: {link}\"")
                password_email_setting_valid = False
                
            if not password_email_setting_valid:
                password_stash.append("\033[91mPASSWORD.EMAIL not valid request password mail will be disabled\033[0m")
                
            USER_MANAGER_SETTINGS['PASSWORD'] = USER_MANAGER_SETTINGS.get('PASSWORD', {})
            USER_MANAGER_SETTINGS['PASSWORD']['EMAIL'] = USER_MANAGER_SETTINGS['PASSWORD'].get('EMAIL', {})
            USER_MANAGER_SETTINGS['PASSWORD']['EMAIL']["SEND"] = password_email_setting_valid

        return password_stash


    @staticmethod
    def validate_redirect():
        
        from utility.views import get_url_or_named_url
        
        if "REDIRECT" not in USER_MANAGER_SETTINGS:
            raise ValueError("REDIRECT urls not found please configer USER_MANAGER_SETTINGS.REDIRECT")
        
        required = ["EMAIL_VERIFICATION", "PASSWORD_CHANGE"]
        for key in required:
            if key not in USER_MANAGER_SETTINGS["REDIRECT"]:
                raise ValueError(f"USER_MANAGER_SETTINGS.REDIRECT missing key {key}")
            
            url = str(USER_MANAGER_SETTINGS["REDIRECT"][key])
            
            kwargs={}
            if 'password' in key.lower(): kwargs['secret'] = "somesecret"
            
            request = APIRequestFactory().get('some-route')

            # USER_MANAGER_SETTINGS["REDIRECT"][key] = get_url_or_named_url(url, request, kwargs=kwargs)
            try:
                _ = get_url_or_named_url(url, request, kwargs=kwargs)
            except ValueError as err:
                raise Exception(f"invalid url route encountered in USER_MANAGER_SETTINGS.REDIRECT.{key}")
                
