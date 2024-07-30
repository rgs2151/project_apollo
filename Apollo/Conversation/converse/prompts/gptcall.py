from .prompt import *
from .tool import *


KEY_INFORMATION_EXTRACT_GPT_CALL = {
                            
    "name": "key_information_extract",
    "purpose": "key_information_extract_tool tool call",
    "history_length": 0,
    "tool": KEY_INFORMATION_EXTRACT_TOOL,
    "tool_choice": "required",
    "tool_call": "get_key_information_extract"

}


CHAT_NORMAL_REPLY_GENERATOR_GPT_CALL = {

    "name": "chat_normal_reply_generator",
    "purpose": "generates reply when tool is called in normal mode",
    "history_length": 20,
    "system_prompt": NORMAL_SYSTEM_PROMPT_DEFINITION,

}


CHAT_GOAL_REPLY_GENERATOR_GPT_CALL = {

    "name": "chat_goal_reply_generator",
    "purpose": "generates reply when tool is called in goal mode",
    "history_length": -1,
    "system_prompt": NORMAL_SYSTEM_PROMPT_DEFINITION,

}


CHAT_APPOINTMENT_GOAL_REPLY_GENERATOR_GPT_CALL = {

    "name": "chat_appointment_reply_generator",
    "purpose": "generates reply when tool is called in appointment mode",
    "history_length": -1,
    "system_prompt": NORMAL_SYSTEM_PROMPT_DEFINITION,

}


GOAL_DETAILS_EXTRACT_GPT_CALL = {
                            
    "name": "goal_details_extract",
    "purpose": "goal_details_extract_tool tool call",
    "history_length": 20,
    "system_prompt": NORMAL_SYSTEM_PROMPT_DEFINITION,
    "tool": GOAL_DETAILS_EXTRACT_TOOL,
    "tool_choice": "auto",
    "tool_call": "get_goal_details_extract"

}


APPOINTMENT_EXTRACT_GPT_CALL = {
                            
    "name": "appointment_extract",
    "purpose": "appointment_extract_tool tool call",
    "history_length": 20,
    "system_prompt": NORMAL_SYSTEM_PROMPT_DEFINITION,
    "tool": APPOINTMENT_EXTRACT_TOOL,
    "tool_choice": "auto",
    "tool_call": "get_appointment_extract"

}


CHAT_NORMAL_MODE_SELECTOR_GPT_CALL = {

    "name": "chat_normal_mode_selector",
    "purpose": "chat_normal_mode_selector_tool tool call",
    "history_length": 0,
    "tool": CHAT_NORMAL_MODE_SELECTOR_TOOL,
    "tool_choice": "required",
    "tool_call": "get_chat_normal_mode_selector"

}


KEY_INFORMATION_EXTRACT_FOR_DOCUMENT_UPLOAD_GPT_CALL = {
                            
    "name": "key_information_extract",
    "purpose": "key_information_extract_tool tool call",
    "history_length": -1,
    "tool": KEY_INFORMATION_EXTRACT_TOOL,
    "tool_choice": "required",
    "tool_call": "get_key_information_extract"

}



