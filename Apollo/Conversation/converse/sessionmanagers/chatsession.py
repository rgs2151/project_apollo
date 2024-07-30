from store.mongoengine import MongoHistoryWithFAISS
from Conversation.serializers import *
from openai.types.chat.chat_completion import ChatCompletion
import datetime, json, pandas as pd
from typing import List


class DocumentStore:


    def __init__(self, mongo_instance, session: Session):

        self.session = session
        self.mongo_instance = mongo_instance
        
        gpt_calls = []
        if SessionStateGPTCalls.objects(session_state = self.session.session_type.session_state).count():
            calls: list = SessionStateGPTCalls.objects(session_state = self.session.session_type.session_state).all()
            gpt_calls = [call.gpt_call.name for call in calls]

        self.key_information_store = None
        if "key_information_extract" in gpt_calls:
            self.set_up_key_information_store()

        self.doctor_store = None
        if "appointment_extract" in gpt_calls:
            self.set_up_doctor_store()


    def set_up_key_information_store(self):
        self.key_information_store = MongoHistoryWithFAISS(
            self.session.user_id,
            self.mongo_instance,
            ConversationHistoryWithFaissSupportSchema, 
            ConversationHistoryWithFaissSupportSchemaSerializer
        )


    def set_up_doctor_store(self):
        self.doctor_store = MongoHistoryWithFAISS(
            self.session.user_id,
            self.mongo_instance,
            DoctorsWithFaissSupportSchema,
            DoctorsWithFaissSupportSchemaSerializer
        )


class ContextCallLookUp:


    def __init__(self, mongo_instance, session: Session, user_prompt = "") -> None:

        self.user_prompt = user_prompt

        self.mongo_instance = mongo_instance

        self.set_session(session)

        # stores
        self.key_information_store = None

    
    def set_session(self, session: Session):
        self.session = session
        self.document_store = DocumentStore(self.mongo_instance, session)

    
    def get_key_information_store(self):
        if self.document_store.key_information_store:
            key_informations = self.document_store.key_information_store.get(self.user_prompt, k=10)
            req_key_information_cols = ["i_parameter_label", "parameter_type", "parameter_value"]
            key_informations = key_informations[req_key_information_cols].rename(columns={"i_parameter_label": "parameter", "parameter_type": "type", "parameter_value": "parameter_value"})
            return json.dumps(key_informations.to_dict("records"), indent=2) if not key_informations.empty else ""
        
        return ""

    
    def get_current_date(self):
        return datetime.datetime.now().strftime("%Y-%m-%d")
    

    def get_current_day(self):
        return datetime.datetime.now().strftime("%A")
    

    def get_user_prompt(self):  return self.user_prompt


    def set_user_prompt(self, user_prompt: dict):
        self.user_prompt = GPTMsgPrompt(user_prompt).get_text_content()


    def get_doctor_store(self, user_prompt: dict):
        if self.document_store.doctor_store:
            doctors = self.document_store.doctor_store.get(self.user_prompt, k=10)
            req_key_information_cols = ["user_id", "dr_name", "dr_days", "dr_time_start", "dr_time_end"]
            doctors = doctors[req_key_information_cols].rename(columns={
                "user_id": "doctor_id", "dr_name": "name", "dr_days": "days_available", "dr_time_start": "start_time", "dr_time_end": "end_time"
            })
            return json.dumps(doctors.to_dict("records"), indent=2) if not doctors.empty else ""
        
        return ""


class ToolCallLookUp:


    def __init__(self, mongo_instance, session: Session) -> None:
        
        self.mongo_instance = mongo_instance

        self.set_session(session)


    def set_session(self, session: Session):
        self.session = session
        self.document_store = DocumentStore(self.mongo_instance, session)


    def get_key_information_extract(self, entries):
        df = pd.DataFrame(entries)
        df.columns = ["i_parameter_label", "parameter_type", "parameter_value"]
        return df
    

    def get_chat_normal_mode_selector(self, mode): return mode


    def get_goal_details_extract(self, **kwargs):
        return kwargs


class ChatSession:


    def __init__(self, mongo_instance, gpt_key: str, session: Session) -> None:
        
        self.gpt_key = gpt_key

        if not isinstance(session, Session):
            raise TypeError("session should be of type Session")
        
        if session.session_type.name != "chat":
            raise ValueError("session invalid, session type should be chat")
        
        if not session.id: raise ValueError("session invalid, session not saved")
        
        self.session = session

        self.mongo_instance = mongo_instance

        self.context_call_lookup = ContextCallLookUp(self.mongo_instance, session=self.session)

        self.tool_call_lookup = ToolCallLookUp(self.mongo_instance, session=self.session)

        self.__gpt_call_summary = []


    def _add_gpt_call_summary(self, summary: dict):
        self.__gpt_call_summary.append(summary)


    def _get_gpt_call_summary(self): return self.__gpt_call_summary


    def get_chat_messages(self):
        history = ChatHistory.objects(session=self.session).all()
        return [GPTMsgPrompt(hist.prompt).get_prompt() for hist in history]


    def get_next_session(self, user_prompt: dict) -> Session:
        if self.session.session_type.session_state.name == "normal":
            next_mode = self.get_mode(user_prompt)
            if next_mode != self.session.session_type.session_state.name:
                return self.get_session(self.session.user_id, session_state=next_mode)
        return self.session
    

    @classmethod
    def get_chatsession(cls, mongo_instance, gpt_key: str, session: Session, user_prompt: dict):
        chat_session = cls(mongo_instance, gpt_key, session)
        new_session = chat_session.get_next_session(user_prompt)
        if new_session != chat_session.session:
            chat_session.session.archive()
            return cls(mongo_instance, gpt_key, new_session)
        return chat_session


    @staticmethod
    def get_session(user_id: int, session_state="normal"):

        user_id = int(user_id)

        if not SessionState.objects(name=session_state).count():
            raise ValueError(f"session_state[{session_state}] not found")
        
        session_state = SessionState.objects(name=session_state).first()

        if not SessionType.objects(name="chat", session_state=session_state).count():
            raise ValueError(f"session_state[{session_state}] mapping not available for session_type[chat]")
        
        session = Session(
            user_id = user_id,
            session_type = SessionType.objects(name="chat", session_state=session_state).first()
        )
        session.save()
        
        return session


    def get_session_state(self):
        return self.session.session_type.session_state


    def get_gpt_calls(self) -> List[GPTCall]:
        if SessionStateGPTCalls.objects(session_state = self.get_session_state()).count():
            calls: list = SessionStateGPTCalls.objects(session_state = self.get_session_state()).all()
            gpt_calls = [call.gpt_call for call in calls]
            return gpt_calls
        return []


    def get_reply_call(self) -> GPTCall:
        reply_calls = [call for call in self.get_gpt_calls() if "reply" in call.name]
        if reply_calls: return reply_calls[0]
    

    def get_reply(self, user_prompt: dict):
        
        reply_call: GPTCall = self.get_reply_call()

        if reply_call and not reply_call.is_tool_call():
            reply_call: GPTCall
            
            chat_messages = self.get_chat_messages()
            
            self.context_call_lookup.set_user_prompt(user_prompt)
            reply_gpt_call, summary = reply_call.get_gpt_call(self.gpt_key, chat_messages, self.context_call_lookup, self.tool_call_lookup, summary=True)
            
            ChatHistory(session=self.session, prompt=user_prompt).save()
            response, response_entry, result = reply_gpt_call.call()
            summary["results"] = response_entry
            self._add_gpt_call_summary(summary)
            ChatHistory(session=self.session, prompt=response_entry).save()

            self.log_gpt_call(reply_call, response)

            return result
        
        return ""


    def get_key_information_extract_tool(self) -> GPTCall:
        reply_calls = [call for call in self.get_gpt_calls() if "key_information" in call.name]
        if reply_calls: return reply_calls[0]


    def get_key_information(self, user_prompt: dict) -> pd.DataFrame:
        
        key_information_tool_call = self.get_key_information_extract_tool()

        if key_information_tool_call and key_information_tool_call.is_tool_call():
            
            chat_messages = self.get_chat_messages()
            
            self.context_call_lookup.set_user_prompt(user_prompt)
            key_information_tool_gpt_call: Msg = key_information_tool_call.get_gpt_call(self.gpt_key, chat_messages, self.context_call_lookup, self.tool_call_lookup)
            
            response, response_entry, result = key_information_tool_gpt_call.call()
            self.log_gpt_call(key_information_tool_call, response)

            return result
        
        return (False, {"extract_user_health_information_entry": [pd.DataFrame()]})
    

    def store_key_information(self, user_prompt: dict):
        status, stash = self.get_key_information(user_prompt)

        if (
            stash and 
            "extract_user_health_information_entry" in stash and 
            stash["extract_user_health_information_entry"] and
            isinstance(stash["extract_user_health_information_entry"], list)
        ): df = stash["extract_user_health_information_entry"][0]
        else : return
            
        if status and not df.empty and self.tool_call_lookup.document_store.key_information_store:
            df["session"] = [self.session] * df.shape[0]
            self.tool_call_lookup.document_store.key_information_store.update(df)


    def get_mode_tool_call(self) -> GPTCall:
        mode_calls = [call for call in self.get_gpt_calls() if "mode" in call.name]
        if mode_calls: return mode_calls[0]


    def get_mode(self, user_prompt: dict) -> str:

        mode_tool_call = self.get_mode_tool_call()

        if mode_tool_call and mode_tool_call.is_tool_call():
            
            chat_messages = []
            
            self.context_call_lookup.set_user_prompt(user_prompt)
            mode_tool_gpt_call, summary = mode_tool_call.get_gpt_call(self.gpt_key, chat_messages, self.context_call_lookup, self.tool_call_lookup, summary=True)
            
            response, response_entry, result = mode_tool_gpt_call.call()
            summary["results"] = response_entry
            self._add_gpt_call_summary(summary)
            self.log_gpt_call(mode_tool_call, response)

            if not result[0]: return "normal"

            if (
                result[1] and 
                "detect_conversation_intent_mode" in result[1] and 
                result[1]["detect_conversation_intent_mode"]
            ): 
                mode = result[1]["detect_conversation_intent_mode"][0]
                if mode == "advice": return "normal"
                return mode
        
        return "normal"


    def log_gpt_call(self, gpt_call: GPTCall, response: ChatCompletion):

        if not isinstance(gpt_call, GPTCall):
            raise TypeError("gpt_call should be of type GPTCall")
        
        if not isinstance(response, ChatCompletion):
            raise TypeError("gpt_call should be of type GPTCall")

        if response and isinstance(response, ChatCompletion) and response.to_dict():
            history_instance = GPTCallHistory(
                gpt_call = gpt_call,
                session = self.session,
                response_json = response.to_dict()
            )
            history_instance.save()
        

    def get_conversation_history(self):
        pass


    def get_mode_required_tools(self):

        calls = self.get_gpt_calls()
        calls_filtered = []
        for call in calls:
            
            if not (
                "mode" in call.name or
                "reply" in call.name or
                "key_information" in call.name
            ): calls_filtered.append(call)

        return calls_filtered


    def get_mode_required_tool_results(self, user_prompt: dict):

        required_tool_calls = self.get_mode_required_tools()

        chat_messages = self.get_chat_messages()

        tool_results = []
        for tool_call in required_tool_calls:

            if tool_call and tool_call.is_tool_call():
                tool_call: GPTCall
                        
                self.context_call_lookup.set_user_prompt(user_prompt)
                tool_gpt_call, summary = tool_call.get_gpt_call(self.gpt_key, chat_messages, self.context_call_lookup, self.tool_call_lookup, summary=True)
                
                response, response_entry, result = tool_gpt_call.call()
                summary["results"] = response_entry
                self._add_gpt_call_summary(summary)
                tool_results.append((response, response_entry, result))
                self.log_gpt_call(tool_call, response)

        return tool_results
    

    def consume_mode_required_tool_results(self, user_prompt: dict):

        tool_results = self.get_mode_required_tool_results(user_prompt)

        goal_created = None
        appointment_created = None
        for response, response_entry, tool_result in tool_results:

            status, stash = tool_result

            if not status: continue

            if "extract_goal_details" in stash and stash["extract_goal_details"]:
                goal_extracted = stash["extract_goal_details"][0]
                goal_extracted["session"] = self.session
                goal_created = Goals(**goal_extracted)
                goal_created.save()


            if "appointment_extract_tool" in stash and stash["appointment_extract_tool"]:
                appointment_extracted = stash["appointment_extract_tool"][0]
                appointment_extracted["session"] = self.session
                appointment_created = Events(**appointment_extracted)
                appointment_created.save()


        return goal_created, appointment_created


    def execute_session_procedures(self, user_prompt: dict):
        reply = self.get_reply(user_prompt)
        self.store_key_information(user_prompt)
        goal_extracted, event_extracted = self.consume_mode_required_tool_results(user_prompt)
        return reply, goal_extracted, event_extracted



