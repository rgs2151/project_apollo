from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes

from Apollo.settings import MONGO_INSTANCE, GPT_KEY

from UserManager.authentication import TokenAuthentication
from UserManager.permissions import UserGroupPermissions, UserAdminPermissions
from store.mongoengine import MongoHistoryWithFAISS, IndexDocumentSchema

# from turbochat.gptprompts import *
from turbochat.v1.prompt import GPTMsgPrompt

from utility.views import ModelManagerView, DefaultPagination

from .serializers import *
from .converse.sessionmanagers.chatsession import ChatSession
from .converse.sessionmanagers.documentuploadsession import DocumentUploadSession

from Conversation.converse.documents import PDF

from .view_utility import UserManagerUtilityMixin

import numpy as np
import pandas as pd
import base64
import time
from io import BytesIO
import logging
logger = logging.getLogger("converse")

from utility.views import *


APETITE = 20

RELEVANCE = 20

SAVE_CONVERSATION_HISTORY = True


class ConversationValidator(DefaultValidator):

    def _check_with_user_prompt(self, field, value):
        try: GPTMsgPrompt(value)
        except ValueError: self._error(field, "should be valid gpt user_prompt")

    def _check_with_base64_string(self, field, value):
        try: base64.b64encode(value.encode())
        except Exception: self._error(field, "should be base64 string")


# depricated
class History(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    @request_schema_validation(schema={
        "type": {"type": "string", "required": True, "empty": False, "allowed": ["history"]},
        "k": {"type": "integer", "required": False, "nullable": True, "min": 1, "default": None},
        "context": {"type": "string", "required": False, "empty": False, "nullable": True, "default": None},
    })
    def post(self, request: Request):
        
        req = request.data

        user_id = request.user_details.user.id

        history = None
        if req.get("type", "") == "history":
            history = MongoHistoryWithFAISS(
                user_id, 
                MONGO_INSTANCE, 
                ConversationHistoryWithFaissSupportSchema, 
                ConversationHistoryWithFaissSupportSchemaSerializer
            )

        data = None
        if "k" in req and "context" in req and req["context"]:
            data = history.get(req["context"], req["k"])

        else:
            data = history.retrieve()

        data = data.replace({np.nan: None})

        return Response({"data": data.to_dict("records"), "data_columns": data.columns.tolist()})


class ConversationHistorySummary(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    def post(self, request: Request):
        if Session.objects(user_id=request.user_details.user_id).count():
            sessions = Session.objects(user_id=request.user_details.user_id).all()
            history = ConversationHistoryWithFaissSupportSchema.objects(session__in=sessions)
            df = pd.DataFrame(ConversationHistoryWithFaissSupportSchemaSerializer(history, many=True).data)
            graph = df[["id", "parameter_type"]].groupby("parameter_type").count().reset_index().rename(columns={"id": "count"}).to_dict("records")
            return Response(graph)



class ConversationHistoryWithFaissSupportView(MongoFilteredListView, UserManagerUtilityMixin):

    authentication_classes = [TokenAuthentication]

    model = ConversationHistoryWithFaissSupportSchema
    serializer = ConversationHistoryWithFaissSupportSchemaSerializer
    pagination = DefaultPagination()

    static_filters = {
        "history_id": UserManagerUtilityMixin.get_user_id
    }

    allow_filters = {
        "session": {"required": False, "type": "string", "empty": False}
    }


    def get(self, request: Request, *args, **kwargs):
        req = request.N_Payload
        if "session_id" in req:
            if Session.objects(id=req["session_id"]).count():
                session = Session.objects(id=req["session_id"]).first()
                if session.user_id != request.user_details.user.id: raise Http404(request)
            else: raise Http404(request)
        return super().get(request, *args, **kwargs)

    

# confirmed
class ChatHistoryView(MongoFilteredListView, UserManagerUtilityMixin):

    authentication_classes = [TokenAuthentication]

    model = ChatHistory
    serializer = ConvHistorySerializer
    pagination = DefaultPagination()


    @staticmethod
    def get_user_sessions(request: Request):
        session_types = SessionType.objects(name="chat").all()
        return Session.objects(user_id=request.user_details.user.id, session_type__in=session_types).all()

    static_filters = {
        "session__in": get_user_sessions
    }


class ChatView(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    @request_schema_validation(schema={
        "message": {"type": "dict", "required": True, "empty": False, "check_with": "user_prompt"},
    }, validator=ConversationValidator())
    def post(self, request: Request):
        
        req = request.N_Payload

        sessions = Session.objects(user_id=request.user_details.user.id, archived=False).all()
        chat_sessions = [session for session in sessions if session.session_type.name == "chat"]
        
        if chat_sessions:
            user_session = chat_sessions[0]

            # just in case any non archived chat states found archive them
            if len(chat_sessions) > 1:
                for session in chat_sessions[1:]:
                    session: Session
                    session.archive()
        
        else: user_session = ChatSession.get_session(request.user_details.user.id)

        chat_session = ChatSession.get_chatsession(MONGO_INSTANCE, GPT_KEY, user_session, req["message"])
        reply, goal_extracted, event_extracted = chat_session.execute_session_procedures(req["message"])

        if goal_extracted or event_extracted: 
            chat_session.session.archive()
            user_session = ChatSession.get_session(request.user_details.user.id)
            
            



            if goal_extracted:
                # formatting = "This was the goal created:\n"
                # for k, v in goal_extracted.items():
                #     formatting += f"{k}: {v}\n"
                #     formatting += "acknowledge that goal with above information was created. Inform the user and start a new conversation."
                
                user_prompt = {
                    "role":"user",
                    "content": [
                        {
                            "type": "text", "text": "System special msg: Acknowledge that a goal was created. Inform the user and start a new conversation."
                        }
                    ]
                }



            if event_extracted:
                # formatting = "This was the event created:\n"
                # for k, v in event_extracted.items():
                #     formatting += f"{k}: {v}\n"
                #     formatting += "acknowledge that event with above information was created. Inform the user and start a new conversation."
                
                user_prompt = {
                    "role":"user",
                    "content": [
                        {
                            "type": "text",
                            "text": "System special msg: Acknowledge that an event was created. Inform the user and start a new conversation."
                        }
                    ]
                }

            chat_session = ChatSession.get_chatsession(MONGO_INSTANCE, GPT_KEY, user_session, user_prompt)
            
            reply, _, _ = chat_session.execute_session_procedures(user_prompt)

        summary = chat_session._get_gpt_call_summary()
        
        response = {
            "mode": chat_session.session.session_type.session_state.name,
            "message": {
                "role": "assistant",
                "content": reply
            },
            "goal_extracted": GoalsSerializer(goal_extracted).data if goal_extracted else {},
            "event_extracted": EventsSerializer(event_extracted).data if event_extracted else {},
            "summary": summary
        }
        
        return Response(response)


class ResetChatSession(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    def post(self, request: Request):
        
        response = {"status": False}
        if Session.objects(user_id=request.user_details.user.id, archived=False).count():
            session_instance: Session = Session.objects(user_id=request.user_details.user.id, archived=False).first()
            session_instance.archive()
            response["status"] = True

        return Response(response)


class Documents(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    def post(self, request: Request):
        pdfIO = BytesIO(request.FILES["attachment"].read())
        
        sessions = Session.objects(user_id=request.user_details.user.id, archived=False).all()
        document_upload_sessions = [session for session in sessions if session.session_type.name == "document_upload"]

        if document_upload_sessions:
            user_session = document_upload_sessions[0]
        else: user_session = DocumentUploadSession.get_session(request.user_details.user.id)
        
        pdf = PDF(pdfIO)
        
        document_upload_session = DocumentUploadSession(MONGO_INSTANCE, GPT_KEY, user_session)

        document_upload_session.execute_session_procedures(pdf)

        document_uploaded = DocumentUploaded.from_pdf_document(user_session, pdf)

        user_session.archive()  
        
        return Response(DocumentUploadedSerializer(document_uploaded).data)


class DocumentUploadedView(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    @request_schema_validation({
        "id": {"required": True, "type": "string", "empty": False},
        "shared_globaly": {"required": True, "type": "boolean"},
    })
    def put(self, request: Request):
        
        req = request.N_Payload

        if not DocumentUploaded.objects(id=req["id"]).count():
            raise APIException("Not Found", "document with id not found", status_code=404)
        
        document_upload_instance: DocumentUploaded = DocumentUploaded.objects(id=req["id"]).first()

        if document_upload_instance.session.user_id != request.user_details.user.id:
            raise APIException("Not Found", "document with id not found", status_code=404)
        
        if req["shared_globaly"]: document_upload_instance.share()
        else: document_upload_instance.unshare()

        return Response(DocumentUploadedSerializer(document_upload_instance).data)


class DocumentUploadedDashboardView(MongoFilteredListView, UserManagerUtilityMixin):
    
    authentication_classes = [TokenAuthentication]

    model = DocumentUploaded
    serializer = DocumentUploadedSerializer
    pagination = DefaultPagination()

    @staticmethod
    def get_user_sessions(request: Request):
        session_state = SessionState.objects(name="upload").first()
        session_type = SessionType.objects(name="document_upload", session_state=session_state).first()
        # return [s.id for s in Session.objects(user_id=request.user_details.user.id, session_type=session_type).all()]
        return Session.objects(user_id=request.user_details.user.id, session_type=session_type).all()

    static_filters = {"session__in": get_user_sessions}


class DocumentGet(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    @request_schema_validation({
        "id": {"required": True, "type": "string", "empty": False}
    })
    def post(self, request: Request):

        req = request.N_Payload

        if not DocumentUploaded.objects(id = req["id"]).count():
            raise APIException("Not Found", "document not found", status_code=404)
        
        document = DocumentUploaded.objects(id = req["id"]).first()

        if document.session.user_id != request.user_details.user.id:
            raise APIException("Not Found", "document not found", status_code=404)
        
        return Response({"document": document.file_bytes})


class DoctorView(MongoModelManagerView, UserManagerUtilityMixin):
    
    authentication_classes = [TokenAuthentication]

    allow_methods = ["GET", "PUT"]

    model = DoctorsWithFaissSupportSchema

    serializer = DoctorsWithFaissSupportSchemaSerializer

    unique_primaries = ["id", "user_id"]

    GET_inject = {
        "user_id": UserManagerUtilityMixin.get_user_id 
    }

    PUT_filter = {
        "dr_name": {"required": False, "type": "string", "empty": False},
        "dr_specialist": {"required": False, "type": "string", "empty": False},
        "dr_days": {"required": False, "type": "string", "empty": False},
        "dr_time_start": {"required": False, "type": "string", "empty": False},
        "dr_time_end": {"required": False, "type": "string", "empty": False},
    }

    PUT_inject = {
        "user_id": UserManagerUtilityMixin.get_user_id,
    }


class SharedDocuments(APIView):
    
    authentication_classes = [TokenAuthentication]

    @exception_handler()
    @request_schema_validation({
        "user_id": {"type": "integer", "required": True, "min": 0}
    })
    def post(self, request: Request):
        
        req = request.N_Payload
        
        session_state = SessionState.objects(name="upload").first()
        session_type = SessionType.objects(name="document_upload", session_state=session_state).first()
        users_document_sessions = Session.objects(user_id=req["user_id"], session_type=session_type).all()

        document_uploaded_instances = DocumentUploaded.objects(session__in=users_document_sessions, shared_globaly=True)

        return Response(DocumentUploadedSerializer(document_uploaded_instances, many=True).data)


class GoalsView(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    def get(self, request: Request):
        instances = Goals.objects(user_id=request.user_details.user.id)
        return Response({"data": GoalsSerializer(instances, many=True).data})


# confirmed
class DoctorEventDashboardView(MongoFilteredListView, UserManagerUtilityMixin):

    authentication_classes = [TokenAuthentication]

    permission_classes = [UserGroupPermissions("Doctor")]

    model = Events
    serializer = EventsSerializer
    pagination = DefaultPagination()

    allow_filters = {
        "event_status": {"coerce": lambda x: x.strip().lower() == "true", "required": False, "type": "boolean"}
    }

    static_filters = {
        "event_type": "appointment",
        "doctor_id": lambda request: f"{request.doctor_id}"
    }
    
    def get(self, request: Request, *args, **kwargs):

        doctor_id = None
        if DoctorsWithFaissSupportSchema.objects(user_id=request.user_details.user.id).count():
            instance = DoctorsWithFaissSupportSchema.objects(user_id=request.user_details.user.id).first()
            doctor_id = instance.id

        request.doctor_id = doctor_id

        return super().get(request, *args, **kwargs)



class DoctorEventView(MongoModelManagerView, UserManagerUtilityMixin):

    authentication_classes = [TokenAuthentication]

    permission_classes = [UserGroupPermissions("Doctor")]

    allow_methods = ["PUT"]

    model = Events

    serializer = EventsSerializer

    unique_primaries = ["id"]

    PUT_filter = {
        "id": {"required": True, "type": "string", "empty": False},
        "event_status": {"required": True, "type": "boolean"}
    }

    PUT_inject = {
        "event_type": "appointment",
        "event_contact_id": lambda request: f"{request.doctor_id}"
    }


    def put(self, request: Request, *args, **kwargs):
        
        doctor_id = None
        if DoctorsWithFaissSupportSchema.objects(user_id=request.user_details.user.id).count():
            instance = DoctorsWithFaissSupportSchema.objects(user_id=request.user_details.user.id).first()
            doctor_id = instance.id 

        request.doctor_id = doctor_id

        return super().put(request, *args, **kwargs)



class UserEventDashboardView(MongoFilteredListView, UserManagerUtilityMixin):

    authentication_classes = [TokenAuthentication]

    model = Events
    serializer = EventsSerializer
    pagination = DefaultPagination()

    @staticmethod
    def get_user_sessions(request: Request):
        session_state = SessionState.objects(name="appointment_or_service_purchase").first()
        session_type = SessionType.objects(name="chat", session_state=session_state).first()
        return Session.objects(user_id=request.user_details.user.id, session_type=session_type).all()

    static_filters = {
        "event_type": "appointment",
        "session__in": get_user_sessions
    }


# confirmed
class GoalsView(MongoFilteredListView, UserManagerUtilityMixin):

    authentication_classes = [TokenAuthentication]

    model = Goals
    serializer = GoalsSerializer
    pagination = DefaultPagination()

    @staticmethod
    def get_user_sessions(request: Request):
        session_state = SessionState.objects(name="goal").first()
        session_type = SessionType.objects(name="chat", session_state=session_state).first()
        return Session.objects(user_id=request.user_details.user.id, session_type=session_type).all()

    static_filters = {
        "session__in": get_user_sessions 
    }


# admin apis


class AdminResetKeyInformationFiassStore(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [UserAdminPermissions]

    @exception_handler()
    def post(self, request: Request):

        tick = time.time()
        store = MongoHistoryWithFAISS(
            request.user_details.user.id,
            MONGO_INSTANCE,
            ConversationHistoryWithFaissSupportSchema, 
            ConversationHistoryWithFaissSupportSchemaSerializer   
        )
        tock = time.time() - tick

        store.reset()

        return Response({"status": True, "time": tock})


class AdminResetUser(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [UserAdminPermissions]

    @exception_handler()
    @request_schema_validation({
        "user_id": {"type": "integer", "required": True, "min": 0, "nullable": False}
    })
    def post(self, request: Request):

        req = request.N_Payload
        user_id = req["user_id"]

        user_sessions = Session.objects(user_id=user_id).all()

        response = {
            "Session": Session.objects(user_id=user_id).count(),
            "IndexDocumentSchema": IndexDocumentSchema.objects(history_id=req["user_id"]).count(),
            "GPTCallHistory": GPTCallHistory.objects(session__in=user_sessions).count(),
            "ChatHistory": ChatHistory.objects(session__in=user_sessions).count(),
            "ConversationHistoryWithFaissSupportSchema": ConversationHistoryWithFaissSupportSchema.objects(session__in=user_sessions).count(),
            "Goals": Goals.objects(session__in=user_sessions).count(),
            "Events": Events.objects(session__in=user_sessions).count(),
        }

        GPTCallHistory.objects(session__in=user_sessions).delete()
        IndexDocumentSchema.objects(history_id=req["user_id"]).delete()
        ChatHistory.objects(session__in=user_sessions).delete()
        ConversationHistoryWithFaissSupportSchema.objects(session__in=user_sessions).delete()
        Goals.objects(session__in=user_sessions).delete()
        Events.objects(session__in=user_sessions).delete()
        Session.objects(user_id=user_id).delete()

        return Response(response)


class AdminUserCounts(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [UserAdminPermissions]

    @exception_handler()
    @request_schema_validation({
        "user_id": {"type": "integer", "required": True, "min": 0, "nullable": False}
    })
    def post(self, request: Request):

        req = request.N_Payload
        user_id = req["user_id"]

        user_sessions = Session.objects(user_id=user_id).all()

        response = {
            "total": {
                "Session": Session.objects(user_id=user_id).count(),
                "GPTCallHistory": GPTCallHistory.objects(session__in=user_sessions).count(),
                "ChatHistory": ChatHistory.objects(session__in=user_sessions).count(),
                "ConversationHistoryWithFaissSupportSchema": ConversationHistoryWithFaissSupportSchema.objects(session__in=user_sessions).count(),
                "IndexDocumentSchema": IndexDocumentSchema.objects(history_id=req["user_id"]).count(),
                "Goals": Goals.objects(session__in=user_sessions).count(),
                "Events": Events.objects(session__in=user_sessions).count()
            }
        }

        return Response(response)


