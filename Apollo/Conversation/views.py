from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from Apollo.settings import MONGO_INSTANCE, GPT_KEY

from UserManager.authentication import TokenAuthentication
from UserManager.permissions import UserGroupPermissions
from store.mongoengine import MongoHistoryWithFAISS

from turbochat.gptprompts import *
from turbochat.v1.prompt import GPTMsgPrompt, GPTMsges
from turbochat.v1.gpt import GPT, Msg

from utility.views import ModelManagerView, DefaultPagination

from .serializers import *
from .converse.prompts.user import PromptMaker
from .converse.prompts.system import DEFAULT as DEFAULT_SYSTEM_PROMPT
from .converse.toolregistry import Registery as ToolRegistry
from .converse.documents import PDFDocumentExtract, PDF, ImageDocumentExtract
from .converse.prompts.tool import EXTRACT_USER_RELATED_INFO
from .converse.toolcallables import *

from .view_utility import UserManagerUtilityMixin

import numpy as np
import pandas as pd
import datetime
import base64
import time
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


class ConversationHistoryWithFaissSupportView(MongoFilteredListView, UserManagerUtilityMixin):

    authentication_classes = [TokenAuthentication]

    model = ConversationHistoryWithFaissSupportSchema
    serializer = ConversationHistoryWithFaissSupportSchemaSerializer
    pagination = DefaultPagination()

    static_filters = {
        "history_id": UserManagerUtilityMixin.get_user_id 
    }


# confirmed
class ChatHistoryView(MongoFilteredListView, UserManagerUtilityMixin):

    authentication_classes = [TokenAuthentication]

    model = ChatHistory
    serializer = ConvHistorySerializer
    pagination = DefaultPagination()

    static_filters = {
        "user_id": UserManagerUtilityMixin.get_user_id 
    }


DEFAULT_PROMPT = {
    "user_prompt": {"label": "user prompt"},
    "services": {"label": "Available services"},
    "doctors": {"label": "Available doctors"},
    "history": {"label": "User related information"},
}


class Conversation:


    __PROMPT_MAKER_CONFIG = {
        "user_prompt": {"label": "user prompt"},
        "services": {"label": "Available services"},
        "doctors": {"label": "Available doctors"},
        "history": {"label": "User related information"},
    }


    __PROMPT_MAKER = PromptMaker(__PROMPT_MAKER_CONFIG)


    __VALID_MODES = ["normal", "goal", "appointment_or_service_purchase"]

    
    def __init__(self, user_prompt: GPTMsgPrompt, user_id: int):
        
        self.context = {}
        logger.debug(f"context was initialized")
        
        self.set_user_prompt(user_prompt)
        
        self.set_user_id(user_id)

        self.update_context_for_conversation_state()

        self.set_gpt()


    def get_event(self):
        
        messages = self.get_message(list(self.context.keys()), self.user_message_history)
        
        tool = ToolRegistry.get_tool("extract_event", messages)
        response_extract_event, tool_prompt_extract_event, results_extract_event = tool.call()

        logger.info("too called registry -> extract_event")

        status, result = results_extract_event
        if status:
            event = result.get('extract_appointment_or_purchase_service_details', [None])[0]
            logger.debug(f"tool detected event: {event}")
            return event


    def get_goal(self):
        
        messages = self.get_message(list(self.context.keys()), self.user_message_history)
        
        tool = ToolRegistry.get_tool("extract_goal", messages)
        response_extract_goals, tool_prompt_extract_goals, results_extract_goals = tool.call()

        logger.info("too called registry -> extract_goal")

        status, result = results_extract_goals
        if status:
            goal = result.get('extract_goal_details', [None])[0]
            logger.debug(f"tool detected goal: {goal}")
            return goal


    def call_tools(self):
        
        if self.user_conversation_state.conversation_state == 'appointment_or_service_purchase':
            event = self.get_event()
            if event:
                event_instance = Events(user_id=self.user_id, **event)
                event_instance.save()
                logger.debug(f"event created: {event_instance.id}")
                return { "event": [event] }
            
        if self.user_conversation_state.conversation_state == 'appointment_or_service_purchase':
            goal = self.get_goal()
            if goal:
                goal_instance = Goals(user_id=self.user_id, **goal)
                goal_instance.save()
                logger.debug(f"goal created: {goal_instance.id}")
                return { "goal": [goal] }


    def get_reply(self):
        
        messages = self.get_message(list(self.context.keys()), include_history=self.user_message_history, include_system_prompt=True)

        logger.info("gpt called for reply")

        response, reply_entry, reply = Msg(self.gpt, messages).call()

        gpt_reply_text_length = len(GPTMsgPrompt(reply_entry).get_text_content())
        logger.info(f"reply generated length: {gpt_reply_text_length}")

        return reply_entry


    def set_gpt(self):
        model="gpt-4o"
        self.gpt = GPT(GPT_KEY, model=model)
        logger.info(f"using gpt: {model}")


    def get_system_prompt(self):
        return GPTMsgPrompt({
            "role": "system",
            "content": DEFAULT_SYSTEM_PROMPT
        }).get_prompt()


    @staticmethod
    def load_fiass_store_services(history_id=0):
        return MongoHistoryWithFAISS(
            history_id,
            MONGO_INSTANCE, 
            ServiceWithFaissSupportSchema,
            ServiceWithFaissSupportSchemaSerializer
        )
        

    @staticmethod
    def load_fiass_store_doctors(history_id=0):
        return MongoHistoryWithFAISS(
            history_id,
            MONGO_INSTANCE, 
            DoctorsWithFaissSupportSchema,
            DoctorsWithFaissSupportSchemaSerializer
        )


    def update_context_for_conversation_state(self):

        self.doctor_store = None

        self.service_store = None
        

        if self.user_conversation_state.conversation_state == "appointment_or_service_purchase":
            
            tick = time.time()
            self.doctor_store = self.load_fiass_store_doctors()
            tock = time.time() - tick
            logger.info(f"doctor store loaded in: {tock} sec")

            tick = time.time()
            self.service_store = self.load_fiass_store_services()
            tock = time.time() - tick
            logger.info(f"service store loaded in: {tock} sec")

            doctors = self.doctor_store.get(context=self.user_prompt.get_text_content(), k=10)
            req_doctor_cols = ["user_id","dr_name","dr_specialist","i_dr_description","dr_days","dr_time_start","dr_time_end"]
            logger.debug(f"doctor store entries loaded: {doctors.shape[0]}")
            self.context["doctors"] = json.dumps(doctors[req_doctor_cols].to_dict("records"), indent=2) if not doctors.empty else ""
            logger.debug(f"context[doctors] set")

            services = self.service_store.get(context=self.user_prompt.get_text_content(), k=10)
            req_service_cols = ["service_name","service_provider","i_service_description","service_cost","service_duration"]
            logger.debug(f"service store entries loaded: {services.shape[0]}")
            self.context["services"] = json.dumps(services[req_service_cols].to_dict("records"), indent=2) if not services.empty else ""
            logger.debug(f"context[services] set")

            self.context["instructions"] = "Ask the user each of the following questions to get the required information about the appointment or service purchase.\n- confirm the exact doctor or service package\n- confirm the appointment/purchase date and appointment/purchase time\n- lastly confirm the appointment/service purchase\n\nYou have the ability to use tools.\nOnce all the information described above is collected,\nUse Extract_appointment_or_purchase_service_details tool to set the appointment/purchase and confirm to the user that you have set it.\n"
            logger.debug(f"context[instructions] set")

        if self.user_conversation_state.conversation_state == "goal":

            self.context["instructions"] = "Keep asking these questions natruallly in the conversation until you have all these required information about the goal:\n\n- confirm the goal description\n- confirm the goal milestones\n- Has there been some goal progress already?\n- confirm the goal target date\n\nYou have the ability to use tools.\nOnce you have collected all the information described above and the user has confirmed the goal details,\nUse Extract_goal_details tool to set the goal and confirm to the user that you have set it.\n"
            logger.debug(f"context[instructions] set")

        
        if not self.doctor_store: logger.debug(f"doctor_store not set")

        if not self.service_store: logger.debug(f"service_store not set")


    def get_message(self, prompt_keys: list, include_history=[], role="user", include_system_prompt=False):

        if not all(key in self.context for key in prompt_keys):
            logger.debug(f"not all required prompt_keys present: provided {prompt_keys}")
            raise ValueError(f"context requires following keys: {[key for key in prompt_keys if key not in self.context]}")
    
        logger.debug(f"context required: {prompt_keys}, included history length: {len(include_history)}, role: {role}")
        context = {k: v for k, v in self.context.items() if k in prompt_keys}
        message = {
            "role": role, "content": [
                {
                    "type": "text",
                    "text": self.__PROMPT_MAKER.get(context)
                }
            ]
        }
        messages = include_history + [message]

        if include_system_prompt:
            logger.debug("system prompt added to messages")
            messages = [self.get_system_prompt()] + messages

        message_text_count = len(GPTMsgPrompt(message).get_text_content())
        logger.info(f"message text length: {message_text_count}")

        return GPTMsges(messages)


    def get_user_next_mode(self):

        tool_messages = self.get_message(["user_prompt"])
        tool = ToolRegistry.get_tool("mode_selector", tool_messages)
        _, resp_entry, results = tool.call()
        status, result = results
        
        logger.info("too called registry -> mode_selector")

        if status:
            next_mode = result.get('detect_conversation_intent_mode', ["normal"])[0]
            logger.debug(f"tool detected next mode: {next_mode}")

            if next_mode == "advice":
                logger.debug("next mode detected was advice setting the next mode to normal")
                next_mode = "normal"

            return next_mode
        
        logger.debug(f"tool was not called next mode: normal")
        
        return "normal"


    @staticmethod
    def load_fiass_store_key_information_history(user_id):
        return MongoHistoryWithFAISS(
            user_id,
            MONGO_INSTANCE,
            ConversationHistoryWithFaissSupportSchema, 
            ConversationHistoryWithFaissSupportSchemaSerializer
        )


    @staticmethod
    def load_conversation_state(user_id):
        
        logger.debug(f"loading conversation state: filter [user_id={user_id}]")
        conversation_state = ConversationState.objects(user_id=user_id).first()
        logger.debug(f"conversation state exists: {conversation_state}")

        if not conversation_state:
            logger.info(f"initializing conversationState for user")
            conversation_state = ConversationState(user_id=user_id, conversation_state="normal")

        _ = f"conversation state mode loaded: {conversation_state.conversation_state}"
        logger.info(_)
        logger.debug(_)

        return conversation_state


    @staticmethod
    def load_conversation_history_for_user_id(user_id):
        # loading chat history for user
        # will ignore all instances not in gpt accepted prompt format
        logger.debug(f"loading chat history: filter [user_id={user_id}] ordered [timestamp] limit [{APETITE * 2}]")
        history_instances = ChatHistory.objects(user_id=user_id).order_by('timestamp').limit(APETITE * 2)
        
        history_messages = []
        for instance in history_instances:
            try: prompt = GPTMsgPrompt(instance.prompt)
            except ValueError: 
                logger.debug(f"skipped! chat instance was not in GPTMsgPrompt accepted format: {instance.prompt} type {type(instance.prompt)}")
                continue
            history_messages.append(prompt.get_prompt())

        logger.debug(f"message history loaded: {len(history_messages)}")
        
        total_loaded_history_text_length = len("".join(GPTMsgPrompt(x).get_text_content() for x in history_messages))
        logger.info(f"total history string length: {total_loaded_history_text_length}")

        return history_messages


    def set_user_id(self, user_id):
        
        if not isinstance(user_id, int):
            logger.debug(f"invalid user_id[{user_id}] type {type(user_id)}")
            raise TypeError("user_id should be of type int")
        
        self.user_id = user_id
        self.user_message_history = self.load_conversation_history_for_user_id(self.user_id)
        self.user_conversation_state = self.load_conversation_state(self.user_id)

        # if conversation mode is something other than allowed modes will update it to normal
        if not self.user_conversation_state.conversation_state.lower().strip() in self.__VALID_MODES:
            logger.info("user conversation state is invalid and therefore updating to normal")
            logger.debug(f"user conversation state is invalid: {self.user_conversation_state.conversation_state}, allowed modes: {self.__VALID_MODES}")
            self.user_conversation_state.conversation_state = "normal"
            self.user_conversation_state.save()


        self.next_mode = self.get_user_next_mode()
        if self.user_conversation_state.conversation_state != self.next_mode:
            logger.debug(f"next mode ({self.next_mode}) not equal to set mode ({self.user_conversation_state.conversation_state}) updating conversation state")
            self.user_conversation_state.set_mode(self.next_mode)


        tick = time.time()
        self.key_information_store = self.load_fiass_store_key_information_history(self.user_id)
        tock = time.time() - tick
        logger.info(f"key information store loaded in: {tock} sec")
        
        key_informations = self.key_information_store.get(self.user_prompt.get_text_content(), k=20)
        req_key_information_cols = ["i_parameter_label","parameter_type","parameter_value"]
        logger.debug(f"key information store entries loaded: {key_informations.shape[0]}")
        self.context["history"] = json.dumps(key_informations[req_key_information_cols].to_dict("records"), indent=2) if not key_informations.empty else ""
        logger.debug(f"context[history] set")


        logger.debug("user_id set")


    def set_user_prompt(self, prompt):
        
        if not isinstance(prompt, GPTMsgPrompt):
            logger.debug(f"invalid prompt[{prompt}] type {type(prompt)}")
            raise TypeError("user_prompt should be of type GPTMsgPrompt")
        
        self.user_prompt = prompt
        self.context["user_prompt"] = self.user_prompt.get_text_content()
        logger.debug(f"context[user_prompt] set")

        current_prompt_text_length = len(self.context["user_prompt"])
        logger.info(f"current prompt text length: {current_prompt_text_length}")

        logger.debug(f"user_prompt set")


class ChatView(APIView):

    authentication_classes = [TokenAuthentication]

    @exception_handler()
    @request_schema_validation(schema={
        "message": {"type": "dict", "required": True, "empty": False, "check_with": "user_prompt"},
    }, validator=ConversationValidator())
    def post(self, request: Request):
        
        req = request.N_Payload

        conversation = Conversation(user_prompt=GPTMsgPrompt(req["message"]), user_id=request.user_details.user.id)

        response = {}

        if SAVE_CONVERSATION_HISTORY: 
            logger.debug("saving original user prompt")
            ChatHistory(user_id=conversation.user_id, prompt=conversation.user_prompt.get_prompt()).save()

        response["message"] = conversation.get_reply()

        if SAVE_CONVERSATION_HISTORY: 
            logger.debug("saving reply prompt")
            ChatHistory(user_id=conversation.user_id, prompt=response["message"]).save()

        toool_result = conversation.call_tools()
        if toool_result:
            logger.info("tool was called, conversation state set to normal")
            conversation.user_conversation_state.set_mode("normal")
            response.update(toool_result)
        else: logger.info("tools were not called")

        response["conversation_state"] = conversation.user_conversation_state.conversation_state

        return Response(response)



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
        Ask the user each of the following questions to get the required information about the appointment or service purchase.
        - confirm the exact doctor or service package
        - confirm the appointment/purchase date and appointment/purchase time
        - lastly confirm the appointment/service purchase

        You have the ability to use tools. 
        Once all the information described above is collected,
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


# updated with image support
class Documents(APIView):


    @exception_handler()
    @request_schema_validation(schema={
        "file": {"type": "string", "required": True, "empty": False, "check_with": "base64_string"},
        "file_type": {"type": "string", "required": False, "empty": False, "allowed": ["pdf", "image"], "default": "pdf"}
    }, validator=ConversationValidator)
    def post(self, request: Request):

        req = request.N_Payload
        
        io_ = BytesIO(req['file'])
        io_.seek(0)

        if req["file_type"] == "pdf":
            pdf = PDF(io_)
            DE = PDFDocumentExtract(pdf, GPT_KEY, EXTRACT_USER_RELATED_INFO, get_callable_df_with_columns(["i_parameter_label", "parameter_type", "parameter_value"]))
            results = DE.extract()

        elif req["file_type"] == "image":
            IMG = ImageDocumentExtract(io_, GPT_KEY, EXTRACT_USER_RELATED_INFO, get_callable_df_with_columns(["i_parameter_label", "parameter_type", "parameter_value"]))
            result = DE.extract()
            results = [result]

            
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

    static_filters = {
        "event_type": "appointment",
        "event_contact_id": lambda request: f"{request.doctor_id}"
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

    static_filters = {
        "event_type": "appointment",
        "user_id": UserManagerUtilityMixin.get_user_id
    }


# confirmed
class GoalsView(MongoFilteredListView, UserManagerUtilityMixin):

    authentication_classes = [TokenAuthentication]

    model = Goals
    serializer = GoalsSerializer
    pagination = DefaultPagination()

    static_filters = {
        "user_id": UserManagerUtilityMixin.get_user_id 
    }

