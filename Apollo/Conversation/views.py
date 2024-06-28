from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from Apollo.settings import MONGO_INSTANCE

from UserManager.authentication import TokenAuthentication
from store.mongoengine import MongoHistoryWithFAISS

from turbochat.gptprompts import *

from .serializers import *
from .converse.core import Message
from .converse.prompts import *
from .converse.tools import *

import numpy as np
import pandas as pd
import datetime

from utility.views import *


APETITE = 30
RELEVANCE = 20


SAVE_CONVERSATION_HISTORY = True


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


class ConversationHistory(APIView):

    authentication_classes = [TokenAuthentication]

    def get(self, request):
        instances = ConvHistory.objects(user_id=request.user_details.user.id)
        return Response({"data": ConvHistorySerializer(instances, many=True).data})


def collected_health_information_entries(entries):
    df = pd.DataFrame(entries)
    df.columns = ["i_parameter_label", "parameter_type", "parameter_value"]
    return df


CONVERSE_TOOLS = Tools([
    {
        "name": "collected_health_information_entries",
        "function": collected_health_information_entries,
        "definition": EXTRACT_USER_RELATED_INFO
    }
])


class Converse(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    @request_schema_validation(schema={
        "message": {"type": "string", "required": True, "empty": False},
    })
    def post(self, request: Request):
        
        req = request.data

        history_instances = ConvHistory.objects.order_by('timestamp').limit(APETITE * 2)
        history_messages = []
        for instance in history_instances:
            if instance.role == 'user':
                history_messages.append(User(instance.content))
            elif instance.role == 'assistant':
                history_messages.append(Assistant(instance.content))
        history_messages = Messages(history_messages)


        # loading history
        faiss_history = MongoHistoryWithFAISS(
            request.user_details.user.id, 
            MONGO_INSTANCE, 
            ConversationHistoryWithFaissSupportSchema, 
            ConversationHistoryWithFaissSupportSchemaSerializer
        )
        history_data = faiss_history.get(req["message"], k=RELEVANCE)


        # doctors
        faiss_doctors = MongoHistoryWithFAISS(
            0,
            MONGO_INSTANCE, 
            DoctorsWithFaissSupportSchema,
            DoctorsWithFaissSupportSchemaSerializer
        )
        doctors = faiss_doctors.get(req["message"], k=10)

        # services
        faiss_services = MongoHistoryWithFAISS(
            0,
            MONGO_INSTANCE, 
            ServiceWithFaissSupportSchema,
            ServiceWithFaissSupportSchemaSerializer
        )
        services = faiss_services.get(req["message"], k=10)

        context = {
            "message": req["message"],
            "assistant_instructions": "Using the context above if relevant, answer the user's query or ask a follow up question.",
            "history": json.dumps(history_data.to_dict("records"), indent=2) if not history_data.empty else "",
            "goals": "",
            "services": json.dumps(services.to_dict("records"), indent=2) if not services.empty else "",
            "doctors": json.dumps(doctors.to_dict("records"), indent=2) if not doctors.empty else ""
        }


        # conversation state
        conversation_state = ConversationState.objects(user_id=request.user_details.user.id).first()
        if not conversation_state:
            conversation_state = ConversationState(user_id=request.user_details.user.id, conversation_state="DEFAULT")
        

        if SAVE_CONVERSATION_HISTORY: ConvHistory(user_id=request.user_details.user.id, role="user", content=req["message"]).save()
        
        message = Message(USER_PROMPT_DEFAULT, context, SYSTEM_MESSAGE, history=history_messages.to_text(), tools=CONVERSE_TOOLS)
        reply, tool_calls = message.get_results()

        if SAVE_CONVERSATION_HISTORY: ConvHistory(user_id=request.user_details.user.id, role="assistant", content=reply).save()


        # updating index
        history = []
        if tool_calls and "collected_health_information_entries" in tool_calls:
            history = tool_calls["collected_health_information_entries"][0]
            faiss_history.update(history)


        # updating conversation state
        conversation_state.last_updated_at = datetime.datetime.now()
        conversation_state.save()


        return Response({"response": reply, "message": message.make_message().get_entries()})
        

