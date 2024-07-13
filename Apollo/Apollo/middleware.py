from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from Apollo.settings import ON403REDIRECT


class RedirectOn403Middleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code == 403 and request.method == 'GET':
            return HttpResponseRedirect(ON403REDIRECT)
        
        return response