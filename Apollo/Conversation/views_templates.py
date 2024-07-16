from .views import *
from UserManager.serializers import UserDetailsSerializer

def template_get_context(request):
    '''{'user': {'id': 1, 'email': 'rudramani.singha@gmail.com', 'first_name': 'Rudra', 'last_name': 'Singha', 'is_staff': True, 'groups': [{'id': 3, 'name': 'doctor'}, {'id': 4, 'name': 'user'}]}, 'onboarding_status': {'email_verificataion': True, 'user_valid': True}, 'cooldowns': {'email_secret_cooldown': 0, 'request_password_change_cooldown': None}}'''

    user_data = UserDetailsSerializer(request.user_details).data
    user_groups = [x['name'] for x in user_data["user"]['groups']]

    user_name = user_data["user"]["first_name"] + " " + user_data["user"]["last_name"]

    return {"user_groups": user_groups, "user_name": user_name, "user_details": user_data["user"]}


class UserProfile(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request): 
        return render(request, template_name="profile.html", context=template_get_context(request))

class Dashboard(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request): 
        return render(request, template_name="dashboard.html", context=template_get_context(request))

class Chat(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request): 
        return render(request, template_name="chat.html", context=template_get_context(request))

class Connect(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request): 
        return render(request, template_name="connect.html", context=template_get_context(request))



class DrDashboad(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request): 
        return render(request, template_name="dr_dashboard.html", context=template_get_context(request))

class DrCalander(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request): 
        return render(request, template_name="dr_calander.html", context=template_get_context(request))

class DrCircle(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request): 
        return render(request, template_name="dr_circle.html", context=template_get_context(request))




