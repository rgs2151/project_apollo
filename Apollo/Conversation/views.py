from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from Apollo.settings import MONGO_INSTANCE, GPT_KEY

from UserManager.authentication import TokenAuthentication
from store.mongoengine import MongoHistoryWithFAISS

from turbochat.gptprompts import *
from turbochat.v1.prompt import GPTMsgPrompt, GPTMsges
from turbochat.v1.gpt import GPT, Msg

from .serializers import *
from .converse.prompts.user import PromptMaker
from .converse.prompts.system import DEFAULT as DEFAULT_SYSTEM_PROMPT
from .converse.toolregistry import Registery as ToolRegistry
from .converse.documents import DocumentExtract, PDF
from .converse.prompts.tool import EXTRACT_USER_RELATED_INFO
from .converse.toolcallables import *

import numpy as np
import pandas as pd
import datetime
import base64
from io import BytesIO

from utility.views import *


APETITE = 30

RELEVANCE = 20

SAVE_CONVERSATION_HISTORY = True


class ConversationValidator(DefaultValidator):

    def _check_with_user_prompt(self, field, value):
        try: GPTMsgPrompt(value)
        except ValueError: self._error(field, "should be valid gpt user_prompt")

    def _check_with_base64_string(self, field, value):
        try: base64.b64encode(value.encode())
        except Exception: self._error(field, "should be base64 string")



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


def collect_events(event_type,event_description,event_contact,event_date,event_time):
    return {"event_type": event_type, "i_event_description": event_description, "event_contact": event_contact, "event_date": event_date, "event_time": event_time}


# TOOL_EVENTS = Tools([
#     {
#         "name": "collect_events",
#         "function": collect_events,
        # "definition": APPOINTMENT_SERVICE_PURCHASE_EVENT
#     }
# ])


DEFAULT_PROMPT = {
    "user_prompt": {"label": "user prompt"},
    "services": {"label": "Available services"},
    "doctors": {"label": "Available doctors"},
    "history": {"label": "User related information"},
}


class Converse(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    @request_schema_validation(schema={
        "message": {"type": "dict", "required": True, "empty": False, "check_with": "user_prompt"},
    }, validator=ConversationValidator())
    def post(self, request: Request):
        
        req = request.data

        # loading chat history for user
        history_instances = ChatHistory.objects.order_by('timestamp').limit(APETITE * 2)
            
        history_messages = []
        for instance in history_instances:
            try: prompt = GPTMsgPrompt(instance.prompt)
            except ValueError: continue
            history_messages.append(prompt.get_prompt())


        # RAG Key value pairs
        faiss_history = MongoHistoryWithFAISS(
            request.user_details.user.id, 
            MONGO_INSTANCE,
            ConversationHistoryWithFaissSupportSchema, 
            ConversationHistoryWithFaissSupportSchemaSerializer
        )
        history_data = faiss_history.get(req["message"], k=RELEVANCE)


        # RAG doctors
        faiss_doctors = MongoHistoryWithFAISS(
            0,
            MONGO_INSTANCE, 
            DoctorsWithFaissSupportSchema,
            DoctorsWithFaissSupportSchemaSerializer
        )
        doctors = faiss_doctors.get(req["message"], k=10)


        # RAG services
        faiss_services = MongoHistoryWithFAISS(
            0,
            MONGO_INSTANCE, 
            ServiceWithFaissSupportSchema,
            ServiceWithFaissSupportSchemaSerializer
        )
        services = faiss_services.get(req["message"], k=10)


        # conversation state
        conversation_state = ConversationState.objects(user_id=request.user_details.user.id).first()
        if not conversation_state:
            conversation_state = ConversationState(user_id=request.user_details.user.id, conversation_state="DEFAULT")


        original_user_prompt = GPTMsgPrompt(req["message"])


        system_prompt = GPTMsgPrompt({
            "role": "system",
            "content": DEFAULT_SYSTEM_PROMPT
        })

        
        prompt = PromptMaker(DEFAULT_PROMPT)


        gpt = GPT(GPT_KEY)


        prompt_content_text = prompt.get({
            "doctors": json.dumps(doctors.to_dict("records"), indent=2) if not doctors.empty else "",
            "services": json.dumps(services.to_dict("records"), indent=2) if not services.empty else "",
            "history": json.dumps(history_data.to_dict("records"), indent=2) if not history_data.empty else "",
            "user_prompt": original_user_prompt.get_text_content(),
        })

        
        user_prompt_for_chat = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt_content_text
                }
            ]
        }


        messages_for_chat = [system_prompt.get_prompt()] + history_messages.copy()
        messages_for_chat.append(user_prompt_for_chat)
        messages_for_chat = GPTMsges(messages_for_chat)

        
        if SAVE_CONVERSATION_HISTORY: ChatHistory(user_id=request.user_details.user.id, prompt=original_user_prompt.get_prompt()).save()

        response, reply_entry, reply = Msg(gpt, messages_for_chat).call()

        if SAVE_CONVERSATION_HISTORY: ChatHistory(user_id=request.user_details.user.id, prompt=reply_entry).save()


        tool_results = {}


        tool_prompt_content_text = prompt.get({
            "user_prompt": original_user_prompt.get_text_content()
        })

        user_prompt_for_tool_call = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": tool_prompt_content_text
                }
            ]
        }

        messages_for_tool_call = [user_prompt_for_tool_call]
        messages_for_tool_call = GPTMsges(messages_for_tool_call)
        tool = ToolRegistry.get_tool("extract_user_related_information", messages_for_tool_call)
        response, response_entry, result = tool.call()

        # updating history
        h_res = []
        status, stash = result
        if status:
            result = stash["extract_user_health_information_entry"][0]
            h_res = result.to_dict("records")
            faiss_history.update(result)


        # updating events
        # event = {}
        # if tool_calls and "collect_events" in tool_calls:
        #     event = tool_calls["collect_events"]
        #     event_instance = EventsData(user_id=request.user_details.user.id, **event)
        #     event_instance.save()


        # updating conversation state
        conversation_state.last_updated_at = datetime.datetime.now()
        conversation_state.save()


        return Response({"message": reply_entry, "history": h_res})
        # return Response({"response": reply, "events": event, "message": message.make_message().get_entries()})


    def get_rag_context(self, context):
        pass


class Events(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    def get(self, request: Request):

        req = request.data
        instances = EventsData.objects(user_id=request.user_details.user.id)
        event_data = EventsDataSerializer(instances, many=True).data

        return Response({"data": event_data})


class Documents(APIView):


    @exception_handler()
    @request_schema_validation(schema={
        "file": {"type": "string", "required": True, "empty": False, "check_with": "base64_string"},
    }, validator=ConversationValidator)
    def post(self, request: Request):

        req = request.data
        
        io_ = BytesIO(req['file'])
        io_.seek(0)
        pdf = PDF(io_)

        DE = DocumentExtract(pdf, GPT_KEY, EXTRACT_USER_RELATED_INFO, get_callable_df_with_columns(["i_parameter_label", "parameter_type", "parameter_value"]))
        results = DE.extract()
        
        ret_results = []
        if isinstance(results, pd.DataFrame) and not results.empty:
            ret_results = results.to_dict("records")

            faiss_history = MongoHistoryWithFAISS(
                request.user_details.user.id, 
                MONGO_INSTANCE,
                ConversationHistoryWithFaissSupportSchema, 
                ConversationHistoryWithFaissSupportSchemaSerializer
            )
            faiss_history.update(results)

        return Response({"extracted": ret_results})


