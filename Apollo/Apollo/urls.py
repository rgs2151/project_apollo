from django.contrib import admin
from django.urls import path, include


handler404 = 'UserManager.views.pagenotfound'


urlpatterns = [
    path('user/', include('UserManager.urls')),
    path('conversation/', include('Conversation.urls')),
]
