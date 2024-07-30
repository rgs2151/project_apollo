from django.urls import path
from .views_templates import *


# class Test(APIView):

#     authentication_classes = [TokenAuthentication]

#     def get(self, request: Request):
#         return render(request, "test.html")

urlpatterns = [
    # Post APIs

    path("history/", History.as_view(), name="conversation-history"),
    path("keyinformation/", ConversationHistoryWithFaissSupportView.as_view(), name="conversation-keyinformation"),
    path("converse/", ChatView.as_view(), name="conversation-chat"),
    path("reset-chat-session/", ResetChatSession.as_view(), name="conversation-reset-chat-session"),
    path("chathistory/", ChatHistoryView.as_view(), name="conversation-converse-history"),
    path("doctor-events-dashboard/", DoctorEventDashboardView.as_view(), name="conversation-doctor-events-dashboard"),
    path("doctor-events/", DoctorEventView.as_view(), name="conversation-doctor-events"),
    path("doctors/", DoctorView.as_view(), name="conversation-doctors"),
    path("user-goals/", GoalsView.as_view(), name="conversation-user-goals"),
    path("user-events-dashboard/", UserEventDashboardView.as_view(), name="conversation-user-events-dashboard"),
    path("user-documents-uploaded-dashboard/", DocumentUploadedDashboardView.as_view(), name="conversation-user-documents-uploaded-dashboard"),
    path("user-documents-get/", DocumentGet.as_view(), name="conversation-user-documents-get"),
    path("shared-documents-get/", SharedDocuments.as_view(), name="conversation-shared-documents"),
    path("share-document/", DocumentUploadedView.as_view(), name="conversation-share-document"),

    # Get and Template APIs
    path("confirmed-events/<event>", ConfirmedEventsView.as_view(), name="conversation-confirmed-events"),
    
    # For Users
    path("profile/", UserProfile.as_view(), name="conversation-profile"),

    path("dashboard/", Dashboard.as_view(), name="conversation-dashboard"),
    path("chat/", Chat.as_view(), name="conversation-chat"),
    path("connect/", Connect.as_view(), name="conversation-connect"),
    path("document-record/", UserDocuments.as_view(), name="conversation-documents"),
    path("goals/", Goals.as_view(), name="conversation-goals"),
    
    # For Doctors
    path("dr_dashboard/", DrDashboad.as_view(), name="conversation-dr-dashboard"),
    path("dr_calander/", DrCalander.as_view(), name="conversation-dr-calander"),
    path("dr_circle/", DrCircle.as_view(), name="conversation-dr-chat"),
    path("dr_events/", DrEvents.as_view(), name="conversation-dr-chat"),

    # path("test/", Test.as_view(), name="test"),

    # admin apis
    path("admin-reset-fiass-store-key-information-store/", AdminResetKeyInformationFiassStore.as_view(), name="admin-reset-fiass-store-key-information-store"),
    path("admin-reset-user/", AdminResetUser.as_view(), name="admin-reset-user"),
    path("admin-user-counts/", AdminUserCounts.as_view(), name="admin-user-counts"),
]
