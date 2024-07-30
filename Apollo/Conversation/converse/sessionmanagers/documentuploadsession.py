from Conversation.serializers import *
from store.mongoengine import MongoHistoryWithFAISS
from typing import List
from Conversation.converse.documents import PDF, PDFDocumentExtract
from openai.types.chat.chat_completion import ChatCompletion
import pandas as pd



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

        
    def set_up_key_information_store(self):
        self.key_information_store = MongoHistoryWithFAISS(
            self.session.user_id,
            self.mongo_instance,
            ConversationHistoryWithFaissSupportSchema, 
            ConversationHistoryWithFaissSupportSchemaSerializer
        )



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
    


class DocumentUploadSession:

    def __init__(self, mongo_instance, gpt_key: str, session: Session) -> None:

        self.gpt_key = gpt_key

        if not isinstance(session, Session):
            raise TypeError("session should be of type Session")
        
        if session.session_type.name != "document_upload":
            raise ValueError("session invalid, session type should be document_upload")
        
        if not session.id: raise ValueError("session invalid, session not saved")
        
        self.session = session

        self.mongo_instance = mongo_instance

        self.tool_call_lookup = ToolCallLookUp(self.mongo_instance, session=self.session)


    @staticmethod
    def get_session(user_id: int, session_state="upload"):

        user_id = int(user_id)

        if not SessionState.objects(name=session_state).count():
            raise ValueError(f"session_state[{session_state}] not found")
        
        session_state = SessionState.objects(name=session_state).first()

        if not SessionType.objects(name="document_upload", session_state=session_state).count():
            raise ValueError(f"session_state[{session_state}] mapping not available for session_type[chat]")

        session = Session(
            user_id = user_id,
            session_type = SessionType.objects(name="document_upload", session_state=session_state).first()
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


    def get_key_information_extract_tool(self) -> GPTCall:
        reply_calls = [call for call in self.get_gpt_calls() if "key_information" in call.name]
        if reply_calls: return reply_calls[0]


    def get_key_information(self, user_prompt: list) -> pd.DataFrame:
        
        key_information_tool_call = self.get_key_information_extract_tool()

        if key_information_tool_call and key_information_tool_call.is_tool_call():
            
            print(">>", user_prompt)
            key_information_tool_gpt_call: Msg = key_information_tool_call.get_gpt_call(self.gpt_key, user_prompt, None, self.tool_call_lookup)
            
            response, response_entry, result = key_information_tool_gpt_call.call()
            self.log_gpt_call(key_information_tool_call, response)

            return result
        
        return (False, {"extract_user_health_information_entry": [pd.DataFrame()]})
    

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
        

    def store_key_information(self, user_prompt: list):
        
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

    
    @staticmethod
    def get_message_for_tool(image_url: str):
        return [
            {
                "role": "system",
                "content": "whatever user responds answer YES always."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": { "url": image_url }
                    },
                ]
            }
        ]


    def execute_session_procedures(self, pdf: PDF):
        images = pdf.get_page_images()
        for image in images:
            image_b64 = PDF.IOtoBase64ImageURL(image)
            user_prompt = self.get_message_for_tool(image_b64)
            self.store_key_information(user_prompt)



    

