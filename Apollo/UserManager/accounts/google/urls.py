from django.urls import path
from django.shortcuts import render
from .views import *




urlpatterns = [
    path('google-auth-url/', AuthenticationURL.as_view(), name='user-google-auth-url'),
    path('google-redirect/', Redirect.as_view(), name='user-google-redirect'),
    path('google-refresh/', Redirect.as_view(), name='user-google-refresh'),
]



