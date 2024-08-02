from .views import *
from UserManager.serializers import UserDetailsSerializer
from UserManager.models import UserDetails
from .serializers import *

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

class Goals(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request):
        return render(request, template_name="goals.html", context=template_get_context(request))

class UserDocuments(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request):
        return render(request, template_name="documents.html", context=template_get_context(request))

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

class DrEvents(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request): 
        return render(request, template_name="dr_events.html", context=template_get_context(request))


class ConfirmedEventsView(APIView):
    authentication_classes = [TokenAuthentication]
    @exception_handler()
    def get(self, request: Request, event):

        this_event = Events.objects(id=event).first()

        # user_data = UserDetailsSerializer(request.user_details).data
        client_user_id = this_event.session.user_id
        client_data = UserDetails.objects.filter(user=client_user_id).first()
        client_name = client_data.user.first_name + " " + client_data.user.last_name

        doctor_data = DoctorsWithFaissSupportSchema.objects(id=this_event.doctor_id).first()
        doctor_name = doctor_data.dr_name

        context = {
            "client_name": client_name,
            "doctor_name": doctor_name,
            "event_time": this_event.event_time,
            "event_date": this_event.event_date,
            "event_id": event,
            "client_user_id": client_user_id
        }

        return render(request, template_name="confirmed_events.html", context=context)

