from django.conf import settings

import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .settings import USER_MANAGER_SETTINGS
from django.urls import reverse
from rest_framework.request import Request


from utility.secret import *
from utility.email import send_email, EmailSendException
from utility.views import get_request_ip


class UserDetails(models.Model):
    
    user = models.OneToOneField(User, models.DO_NOTHING, primary_key=True)
    email_verified_at = models.DateTimeField(blank=True, null=True, default=None)
    email_secret = models.CharField(max_length=200, blank=True, null=True)
    email_secret_generated_at = models.DateTimeField(blank=True, null=True, default=None)
    last_log_out = models.DateTimeField(blank=True, null=True, default=None)
    password_change_secret = models.CharField(max_length=200, blank=True, null=True, default=None)
    password_change_requested_at = models.DateTimeField(blank=True, null=True, default=None)
    last_password_change_at = models.DateTimeField(blank=True, null=True, default=None)
    tokens_issued = models.IntegerField(blank=True, null=True, default=0)
    archived = models.IntegerField(blank=True, null=True, default=0) # assure default

    class Meta:
        db_table = 'user_details'


    @staticmethod
    def create_django_email_user(email, password, first_name="", last_name="") -> User:
        
        if User.objects.filter(email=email).exists():
            raise ValueError("user with email already exists")
        
        user = User(email=email, first_name=first_name, last_name=last_name, username=email, is_active=1)
        user.set_password(password)
        user.save()
        return user


    @classmethod
    def initialize_user_details(cls, user: User, request: Request):
        
        if not isinstance(user, User):
            raise TypeError("user should be instance of django.contrib.auth.models.User")
        
        user_details = cls(user=user)

        user_details.save()

        return user_details
    
    
    @staticmethod
    def validate_generated_secret_for_user(secret: str):
        
        try:
            user_details_instance = None
            secret_data = None
            secret_data = UserDetails.decrypt_token(secret)
            
            if not 'user_id' in secret_data or not 'secret' in secret_data:
                return False, user_details_instance, secret_data
            
            if not UserDetails.objects.filter(user__id=secret_data['user_id'], user__is_active=1).exists():
                return False, user_details_instance, secret_data
            
            user_details_instance = UserDetails.objects.get(user__id=secret_data['user_id'])
            
            return True, user_details_instance, secret_data
            
        except Exception as err:
            return False, user_details_instance, secret_data
    
    
    @staticmethod
    def validate_email(secret: str):
        
        status, user_details_instance, secret_data = UserDetails.validate_generated_secret_for_user(secret)
        if not status:
            return status, user_details_instance
            
        if user_details_instance.email_verified_at or not validate_secret(secret_data['secret'], user_details_instance.email_secret, url_safe_base64encode=True):
            return False, user_details_instance
        
        user_details_instance.email_verified_at = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())
        user_details_instance.save()
        
        return True, user_details_instance

    
    @staticmethod
    def _generate_email_secret(user: User, request: Request, secret_type='email'):
        
        email_secret, email_secret_meta = generate_random_secret_meta(length=10, url_safe_base64encode=True)
        
        secret_data = {"secret": email_secret, "user_id": user.id}
        secret_token = encrypt_fernet_token(secret_data, USER_MANAGER_SETTINGS['TOKEN']["ENCRYPTION_KEY"]).decode('utf-8')
        
        email_sent = False
        
        email_settings = USER_MANAGER_SETTINGS["EMAIL"]
        smtp_username = email_settings["SMTP_USERNAME"]
        smtp_password = email_settings["SMTP_PASSWORD"]
        from_email = email_settings["FROM"]
        
        if secret_type == 'email':
            subject = email_settings["SUBJECT"]
            email_template = email_settings["TEMPLATE"]
            email_verification_link = request.build_absolute_uri(reverse('user-verify-email', kwargs={"secret": secret_token}))
        
        elif secret_type == 'password':
            password_settings = USER_MANAGER_SETTINGS["PASSWORD"]["EMAIL"]
            email_verification_link = request.build_absolute_uri(reverse('user-password-change', kwargs={"secret": secret_token}))
            if not password_settings['SEND']:
                return email_verification_link, False, email_secret_meta
            subject = password_settings["SUBJECT"]
            email_template = password_settings["TEMPLATE"]
            
        else: raise ValueError(f"secret_type: {secret_type} is not supported")
                        
        email_settings = USER_MANAGER_SETTINGS["EMAIL"]
        if email_settings["SEND"]:
            
            email_template = email_verification_link.join(email_template.split(r'{link}'))
            
            try:
                send_email(
                    smtp_username,
                    smtp_password,
                    from_email,
                    [user.email], [],
                    subject,
                    email_template
                )
                email_sent = True
            
            except EmailSendException: pass
            
        return email_verification_link, email_sent, email_secret_meta


    def issue_token(self, request=None):
        
        user_instanece: User = self.user
        
        if request: ip = get_request_ip(request)
        else: ip = {}
        
        token_data = {
            "user_id": user_instanece.id,
            "expiery_datetime": (datetime.datetime.now() + USER_MANAGER_SETTINGS['TOKEN']['TOKEN_EXPIERY_TIME']).strftime("%Y-%m-%d %H:%M:%S"),
            "ip": ip,
        }
        
        token = encrypt_fernet_token(token_data, USER_MANAGER_SETTINGS['TOKEN']["ENCRYPTION_KEY"]).decode('utf-8')
        
        return token
    
    
    def get_issue_email_secret_cooldown(self, date_now):
        if self.email_secret_generated_at:
            can_issue_secret_after = self.email_secret_generated_at + USER_MANAGER_SETTINGS["COOLDOWN"]["EMAIL_SECRET"]
            if can_issue_secret_after > date_now:
                return (can_issue_secret_after - date_now).seconds
            return 0


    def issue_email_secret(self, request=None):
        
        date_now = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())
        if self.get_issue_email_secret_cooldown(date_now):
            return None, False
            
        email_verification_link, email_sent, email_secret_meta = self._generate_email_secret(self.user, request)
        self.email_secret = email_secret_meta
        self.email_secret_generated_at = date_now
        self.save()
        return email_verification_link, email_sent


    @staticmethod
    def decrypt_token(token: str):
        if isinstance(token, str): token = token.encode()
        return decrypt_fernet_token(token, USER_MANAGER_SETTINGS["TOKEN"]["ENCRYPTION_KEY"])


    @staticmethod
    def validate_token(token: str):
        
        try:
            
            user_details = None
            
            token_data = UserDetails.decrypt_token(token)
            
            if ('user_id' not in token_data) or ('expiery_datetime' not in token_data): return False, user_details
            
            if not UserDetails.objects.filter(user=token_data['user_id'], user__is_active=True).exists():
                return False, user_details
        
            user_details = UserDetails.objects.get(user=token_data['user_id'], user__is_active=True)
            
            return True, user_details
        
        except Exception as err:
            return False, user_details
            

    def update_user(self, update_details: dict):
        """
        first
        last
        email: new email verification will be done
        """
        
        user = User.objects.get(id=self.user.id)
                
        if "first_name" in update_details: user.first_name =  update_details["first_name"]
        if "last_name" in update_details: user.last_name = update_details["last_name"]
        if "email" in update_details:
            
            if UserDetails.objects.filter(user__email=update_details["email"], user__is_active=True).exists():
                raise ValueError("user with email already exists")
            
            user.email = update_details["email"]
        
        user.save()
    
        
    def get_issue_password_change_cooldown(self, date_now: datetime.datetime):
        if self.password_change_requested_at:
            can_issue_secret_after = self.password_change_requested_at + USER_MANAGER_SETTINGS["COOLDOWN"]["PASSWORD_CHANGE_SECRET_REQUEST"]
            if can_issue_secret_after > date_now:
                return (can_issue_secret_after - date_now).seconds    
            
            return 0


    def issue_password_change(self, request: Request):
        date_now = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())
        if self.get_issue_password_change_cooldown(date_now):
            return None, False
        
        password_change_link, email_sent, password_change_secret_meta = self._generate_email_secret(self.user, request, secret_type="password")
        
        self.password_change_secret = password_change_secret_meta
        self.password_change_requested_at = date_now
        self.save()
        
        return password_change_link, email_sent


    @staticmethod
    def validate_secret(secret: str):
        user_details_instance = None

        secret_data = UserDetails.decrypt_token(secret)
        
        if not 'user_id' in secret_data or not 'secret' in secret_data:
            return False, user_details_instance
        
        if not UserDetails.objects.filter(user__id=secret_data['user_id']).exists():
            return False, user_details_instance
        
        user_details_instance = UserDetails.objects.get(user__id=secret_data['user_id'])
        return user_details_instance, secret_data
        

    @staticmethod
    def check_password_change_secret(secret: str):
        
        status, user_details_instance, secret_data = UserDetails.validate_generated_secret_for_user(secret)
        if not status: return status, user_details_instance

        status = validate_secret(secret_data['secret'], user_details_instance.password_change_secret, url_safe_base64encode=True)

        return status, user_details_instance


    @staticmethod
    def change_password(secret: str, new_password: str):
        
        # status, user_details_instance, secret_data = UserDetails.validate_generated_secret_for_user(secret)
        # if not status: return status, user_details_instance
        # status = validate_secret(secret_data['secret'], user_details_instance.password_change_secret, url_safe_base64encode=True)
        
        status, user_details_instance = UserDetails.check_password_change_secret(secret)
        if not status: return status, user_details_instance

        if not user_details_instance.password_change_requested_at or not status:
            return False, user_details_instance
        
        user_details_instance.user.set_password(new_password)
        user_details_instance.user.save()
        user_details_instance.password_change_requested_at = None
        user_details_instance.password_change_secret = None
        user_details_instance.last_password_change_at = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())
        user_details_instance.save()
        
        return True, user_details_instance



