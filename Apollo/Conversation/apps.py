from django.apps import AppConfig
from .converse.prompts.context import CONTEXTS
from .converse.prompts.session import CHAT_SESSION_CONFIG, DOCUMENT_UPLOAD_SESSION_CONFIG
from .models import *


class InitializeSessionConfig:

    def __init__(self, session_config: dict):
        
        session_config_ = {}
        session_config_.update(session_config)

        session_states = session_config_.pop("session_states")
        session_state_gpt_maps = SessionStateGPTCalls.make_state_gptcall_maps(session_states)
        
        session_states = [x["session_state"] for x in session_states]
        session_config_["session_states"] = session_states
        session_type_maps = SessionType.make_session_type(session_config_)
        

class InitializeContexts:

    def __init__(self, context_config: list):
        
        for config in context_config:
            conf = {}
            conf.update(config)
            gpt_call: GPTCall = GPTCall.make_gpt_calls([conf.pop("gpt_call")], update=True)
            context = Context.make_context(gpt_call[0], conf.pop("fields"), update=True)


class ConversationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Conversation'

    def ready(self) -> None:
        InitializeContexts(CONTEXTS)
        InitializeSessionConfig(CHAT_SESSION_CONFIG)
        InitializeSessionConfig(DOCUMENT_UPLOAD_SESSION_CONFIG)

