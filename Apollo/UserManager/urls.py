from django.urls import path
from django.shortcuts import render
from .views import *


handler404 = 'UserManager.views.pagenotfound'


urlpatterns = [
    path('register/', UserRegister.as_view(), name='user-register'),
    path('verify-email/<str:secret>', VerifyEmail.as_view(), name='user-verify-email'),
    path('login/', UserLogin.as_view(), name='user-login'),
    path('details/', UserDetailsView.as_view(), name='user-details'),
    path('resend-email-verification/', ResendVerificationMail.as_view(), name='user-resend-email-verification'),
    path('update/', UserUpdate.as_view(), name='user-update'),
    path("update-password/", UserChangePassword.as_view(), name='user-update-password'),
    path("logout/", LogOut.as_view(), name='user-logout'),

    # This view is copy of other
    # path('details/', UserGet.as_view(), name='user-details'),

    path('change-password/<str:secret>', UserChangePasswordRedirect.as_view(), name='user-password-change-redirect'),
    path('email-verified/', VerifyEmailRedirect.as_view(), name='user-verify-email-redirect'),

    # basic templates when enabled
    path('password-change/<str:secret>', UserPasswordChange.as_view(), name='user-password-change'),
    path('request-password-change/', UserPasswordChangeRequest.as_view(), name='user-request-password-change'),
    path("registration/", lambda request: render(request, template_name="user_registration.html"), name="user-registration-form"),
    path("signin/", lambda request: render(request, template_name="user_signin.html"), name="user-signin-form"),
    path("home/", lambda request: render(request, template_name="user_home.html"), name="user-default-home"),
    path("forgot-password/", lambda request: render(request, template_name="user_forgotpassword.html"), name="user-forgotpassword"),

    # admin dashboard apis
    path("admin-users/", UserDashboard.as_view(), name="user-admin-users"),
    path("admin-groups/", Groups.as_view(), name="user-admin-groups"),
    path("admin-groups-manager/", GroupManager.as_view(), name="user-admin-groups-manager"),
    path("admin-user-groups-manager/", UserGroupManager.as_view(), name="user-admin-user-groups-manager"),
    
    path("admin-dashboard/", lambda request: render(request, template_name="user_admin_dashboard.html"), name="user-admin-dashboard"),


]



