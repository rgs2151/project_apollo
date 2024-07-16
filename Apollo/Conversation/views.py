from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes

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
import logging
logger = logging.getLogger("converse")

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


def collected_health_information_entries(entries):
    df = pd.DataFrame(entries)
    df.columns = ["i_parameter_label", "parameter_type", "parameter_value"]
    return df


def collect_events(event_type, event_description, event_contact, event_date, event_time):
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
        user_message = GPTMsgPrompt(req["message"]).get_text_content()
        logger.info(f"user[id={request.user_details.user.id}] message length: {len(user_message)}")


        history_messages = self.load_conversation_history(request.user_details.user.id)
        logger.info(f"history_messages loaded: {len(history_messages)}")


        PM = PromptMaker({
            "user_prompt": {"label": "user prompt"},
            "services": {"label": "Available services"},
            "doctors": {"label": "Available doctors"},
            "history": {"label": "User related information"},
            "instructions": {"label": "Special system instructions"}
        })
        logger.info(f"prompt maker intialized")


        # conversation state
        logger.info(f"conversationState fetched")
        conversation_state = ConversationState.objects(user_id=request.user_details.user.id).first()
        if not conversation_state:
            logger.info(f"initializing conversationState for user")
            conversation_state = ConversationState(user_id=request.user_details.user.id, conversation_state="normal")

        conversation_mode = "normal"
        if conversation_state.reset_state: conversation_state.reset()
        else: conversation_mode = conversation_state.conversation_state

        logger.info(f"conversation state was: {conversation_mode}")
        if conversation_mode == "normal":
            conversation_mode = self.get_user_mode(PM, user_message)
            if conversation_mode == "advice": conversation_mode = "normal"
            if conversation_mode != "normal": conversation_state.set_mode(conversation_mode)
        logger.info(f"conversation state is: {conversation_mode}")
            
        
        faiss_history = self.get_key_information_store(request.user_details.user.id)
        logger.info(f"faiss_history key information")
        

        context = self.get_context(conversation_mode, request.user_details.user.id, user_message, faiss_history)
        logger.info(f"get context for mode: {conversation_mode}")

        
        system_prompt = [{
            "role": "system",
            "content": DEFAULT_SYSTEM_PROMPT
        }]


        model="gpt-4o"
        gpt = GPT(GPT_KEY, model=model)
        logger.info(f"initialized gpt: {model}")

        
        reply_entry = self.get_reply(PM, context, system_prompt, history_messages, request.user_details.user.id, req["message"], gpt)
        logger.info(f"reply generated: {len(GPTMsgPrompt(reply_entry).get_text_content())}")


        h_res = self.extract_key_points(PM, user_message, faiss_history)
        logger.info(f"key value pairs extracted: {len(h_res)}")


        tool_called_successfully, created = self.call_tools(request.user_details.user.id, conversation_mode, PM, context, history_messages)
        logger.info(f"tools were called: {tool_called_successfully}")
        if tool_called_successfully:
            conversation_state.conversation_state = "normal"
            # conversation_state.reset_state = True
            conversation_state.save()
            logger.info(f"conversation_state mode set to normal")


        # updating conversation state
        conversation_state.last_updated_at = datetime.datetime.now()
        conversation_state.save()
        logger.info(f"updated conversation state")

        return Response({"message": reply_entry, "history": h_res, "created": created, "conversation_state": conversation_mode, "context": context})


    def call_tools(self, user_id, mode, prompt_maker, context, history_messages):

        tool_called_successfully = False
        created = {}
        if mode == "goal":
            goal = self.get_goal(prompt_maker, context, history_messages)
            if goal:
                Goals(user_id=user_id, **goal).save()
                created = { "goal": [goal] }
                tool_called_successfully = True

        elif mode == 'appointment_or_service_purchase':
            event = self.get_event(prompt_maker, context, history_messages)
            if event:
                Events(user_id=user_id, **event).save()
                created = { "event": [event] }
                tool_called_successfully = True


        return tool_called_successfully, created
    

    def get_event(self, prompt_maker, context, history_messages):
        messages = GPTMsges(history_messages + [{ "role":"user", "content": prompt_maker.get(context) }])
        tool = ToolRegistry.get_tool("extract_event", messages)
        response_extract_event, tool_prompt_extract_event, results_extract_event = tool.call()
        status, result = results_extract_event
        if status:
            return result.get('extract_appointment_or_purchase_service_details', [None])[0]


    def get_goal(self, prompt_maker, context, history_messages):
        messages = GPTMsges(history_messages + [{ "role":"user", "content": prompt_maker.get(context) }])
        tool = ToolRegistry.get_tool("extract_goal", messages)
        response_extract_goals, tool_prompt_extract_goals, results_extract_goals = tool.call()
        status, result = results_extract_goals
        if status:
            return result.get('extract_goal_details', [None])[0]
        

    def extract_key_points(self, prompt_maker, user_message, faiss_history):
        tool_messages = self.get_basic_user_messages(prompt_maker, user_message)
        tool = ToolRegistry.get_tool("extract_user_related_information", tool_messages)
        _, resp_entry, results = tool.call()
        status, result = results
        if status:
            result = result.get('extract_user_health_information_entry', [pd.DataFrame()])[0]
            faiss_history.update(result)
            return result.to_dict("records")
        
        return []


    def get_reply(self, prompt_maker, context, system_prompt, history_messages, user_id, original_user_prompt, gpt):
        
        user_prompt = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt_maker.get(context)
                }
            ]
        }
        
        messages = system_prompt + history_messages + [user_prompt]
        messages = GPTMsges(messages)

        if SAVE_CONVERSATION_HISTORY: ChatHistory(user_id=user_id, prompt=original_user_prompt).save()

        response, reply_entry, reply = Msg(gpt, messages).call()

        if SAVE_CONVERSATION_HISTORY: ChatHistory(user_id=user_id, prompt=reply_entry).save()

        return reply_entry


    def get_context(self, mode, user_id, context, faiss_history):
        
        
        context = self.default_context(user_id, context, faiss_history)
        
        if mode == "normal": return context

        elif mode == "appointment_or_service_purchase":
            context.update(self.appointment_or_service_purchase_context(context))

        elif mode == "goal":
            context.update(self.goal_context())
        
        return context


    def goal_context(self):
        special_instructions_goal = """
        Keep asking these questions natruallly in the conversation until you have all these required information about the goal:

        - confirm the goal description
        - confirm the goal milestones
        - Has there been some goal progress already?
        - confirm the goal target date

        You have the ability to use tools.
        Once you have collected all the information described above and the user has confirmed the goal details,
        Use Extract_goal_details tool to set the goal and confirm to the user that you have set it.
        """

        context_goal = {}
        context_goal['instructions'] = special_instructions_goal
        return context_goal

    
    def appointment_or_service_purchase_context(self, context):
        special_instructions_event = """
        Keep asking these questions natruallly in the conversation until you have all these required information about the appointment or service purchase:

        - confirm the exact doctor or service package
        - confirm the appointment/purchase date and appointment/purchase time
        - ensure that the appointment/service request matches the doctor/service provider's availability.
        - confirm the appointment/purchase details with the user.

        You have the ability to use tools. 
        Once you have collected all the information described above and the user has confirmed the appointment/purchase details,
        Use Extract_appointment_or_purchase_service_details tool to set the appointment/purchase and confirm to the user that you have set it.
        """

        doctors = self.get_doctors(context)

        services = self.get_services(context)

        context_event = {}
        context_event["doctors"] = json.dumps(doctors.to_dict("records"), indent=2) if not doctors.empty else "",
        context_event["services"] = json.dumps(services.to_dict("records"), indent=2) if not services.empty else "",
        context_event['instructions'] = special_instructions_event
        return context_event


    def get_services(self, context):
        # RAG services
        faiss_services = MongoHistoryWithFAISS(
            0,
            MONGO_INSTANCE, 
            ServiceWithFaissSupportSchema,
            ServiceWithFaissSupportSchemaSerializer
        )
        return faiss_services.get(context, k=10)


    def get_doctors(self, context):
        # RAG doctors
        faiss_doctors = MongoHistoryWithFAISS(
            0,
            MONGO_INSTANCE, 
            DoctorsWithFaissSupportSchema,
            DoctorsWithFaissSupportSchemaSerializer
        )
        return faiss_doctors.get(context, k=10)
        

    def default_context(self, user_id, context, faiss_history):

        history_data = self.get_key_information(faiss_history, context)

        return {
            "history": json.dumps(history_data.to_dict("records"), indent=2) if not history_data.empty else "",
            "user_prompt": context
        }

    
    def get_user_mode(self, prompt_maker, user_message):
        tool_messages = self.get_basic_user_messages(prompt_maker, user_message)
        tool = ToolRegistry.get_tool("mode_selector", tool_messages)
        _, resp_entry, results = tool.call()
        status, result = results
        if status:
            return result.get('detect_conversation_intent_mode', ["normal"])[0]
        return "normal"


    def get_basic_user_messages(self, prompt_maker, context):
        context = { "user_prompt": context }
        text_content = prompt_maker.get(context)
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text_content
                    }
                ]
            }
        ]
        return GPTMsges(messages)


    def get_key_information(self, faiss_history, context):
        return faiss_history.get(context, k=RELEVANCE)


    def get_key_information_store(self, user_id):
        # RAG Key value pairs
        return MongoHistoryWithFAISS(
            user_id,
            MONGO_INSTANCE,
            ConversationHistoryWithFaissSupportSchema, 
            ConversationHistoryWithFaissSupportSchemaSerializer
        )


    def load_conversation_history(self, user_id):
        # loading chat history for user
        history_instances = ChatHistory.objects(user_id=user_id).order_by('timestamp').limit(APETITE * 2)
            
        history_messages = []
        for instance in history_instances:
            try: prompt = GPTMsgPrompt(instance.prompt)
            except ValueError: continue
            history_messages.append(prompt.get_prompt())

        return history_messages


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


class DoctorsView(APIView):

    @exception_handler()
    def get(self, request: Request):
        instances = DoctorsWithFaissSupportSchema.objects.all()
        return Response({"data": DoctorsWithFaissSupportSchemaSerializer(instances, many=True).data})


class GoalsView(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    def get(self, request: Request):
        instances = Goals.objects(user_id=request.user_details.user.id)
        return Response({"data": GoalsSerializer(instances, many=True).data})
    

class EventsView(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    def get(self, request: Request):
        instances = Events.objects(user_id=request.user_details.user.id)
        return Response({"data": EventsSerializer(instances, many=True).data})