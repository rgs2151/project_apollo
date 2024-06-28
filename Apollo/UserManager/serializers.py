from rest_framework.serializers import ModelSerializer, SerializerMethodField
from .models import *

class LimitedUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        
        
class UserDetailsSerializer(ModelSerializer):
    user = LimitedUserSerializer()
    onboarding_status = SerializerMethodField()
    cooldowns = SerializerMethodField()
    
    class Meta:
        model = UserDetails
        fields = ['user', 'onboarding_status', 'cooldowns']
        
    def get_onboarding_status(self, model_instance: UserDetails):
        
        onboarding_status = {}
        
        onboarding_status["email_verificataion"] = False if not model_instance.email_verified_at else True
        
        onboarding_status["user_valid"] = all(onboarding_status[key] for key in onboarding_status)
        
        return onboarding_status
    
    
    def get_cooldowns(self, model_instance: UserDetails):
        
        cooldowns = {}
        
        date_now = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())
        
        email_secret_cooldown = model_instance.get_issue_email_secret_cooldown(date_now)
        cooldowns['email_secret_cooldown'] = email_secret_cooldown

        password_change_cooldown = model_instance.get_issue_password_change_cooldown(date_now)
        cooldowns['request_password_change_cooldown'] = password_change_cooldown

        return cooldowns

