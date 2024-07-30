from .gptcall import *
from .contextfields import *


DEFAULT_USER_PROMPT_FIELD = {
    "field": USER_PROMPT_CONTEXT_FIELD,
    "label": "User reply was",
    "key": "user_prompt",
}


DEFAULT_CURRENT_DATE_CONTEXT_FIELD = {
    "field": CURRENT_DATE_CONTEXT_FIELD,
    "label": "todays date is",
    "key": "todays_date",
}


DEFAULT_CURRENT_DAY_CONTEXT_FIELD = {
    "field": CURRENT_DAY_CONTEXT_FIELD,
    "label": "todays day is",
    "key": "todays_day",
}


DEFAULT_ASSISTANT_MESSAGE_GOAL_FIELD = {
    "field": ASSISTANT_MESSAGE_GOAL_FIELD,
    "label": "assistant instructions",
    "key": "assistant_instructions",
}


DEFAULT_ASSISTANT_MESSAGE_APPOINTMENT_FIELD = {
    "field": ASSISTANT_MESSAGE_APPOINTMENT_FIELD,
    "label": "assistant instructions",
    "key": "assistant_instructions",
}


DEFAULT_KEY_INFORMATION_STORE_FIELD = {
    "field": KEY_INFORMATION_STORE_FIELD,
    "label": "users known information",
    "key": "key_information_history",
}


DEFAULT_DOCTOR_STORE_FIELD = {
    "field": DOCTOR_STORE_FIELD,
    "label": "available doctor data",
    "key": "doctors",
}


CONTEXTS = [

    # session type chat

    {
        "gpt_call": KEY_INFORMATION_EXTRACT_GPT_CALL,
        "fields": [
            DEFAULT_USER_PROMPT_FIELD,
        ]

    },

    {
        "gpt_call": CHAT_NORMAL_REPLY_GENERATOR_GPT_CALL,
        "fields": [
            DEFAULT_CURRENT_DATE_CONTEXT_FIELD,
            DEFAULT_CURRENT_DAY_CONTEXT_FIELD,
            DEFAULT_KEY_INFORMATION_STORE_FIELD,
            DEFAULT_USER_PROMPT_FIELD,
        ]

    },

    {
        "gpt_call": CHAT_GOAL_REPLY_GENERATOR_GPT_CALL,
        "fields": [
            DEFAULT_CURRENT_DATE_CONTEXT_FIELD,
            DEFAULT_CURRENT_DAY_CONTEXT_FIELD,
            DEFAULT_KEY_INFORMATION_STORE_FIELD,
            DEFAULT_ASSISTANT_MESSAGE_GOAL_FIELD,
            DEFAULT_USER_PROMPT_FIELD,
        ]

    },

    {
        "gpt_call": CHAT_APPOINTMENT_GOAL_REPLY_GENERATOR_GPT_CALL,
        "fields": [
            DEFAULT_CURRENT_DATE_CONTEXT_FIELD,
            DEFAULT_CURRENT_DAY_CONTEXT_FIELD,
            DEFAULT_KEY_INFORMATION_STORE_FIELD,
            DEFAULT_ASSISTANT_MESSAGE_APPOINTMENT_FIELD,
            DEFAULT_DOCTOR_STORE_FIELD,
            DEFAULT_USER_PROMPT_FIELD,
        ]

    },

    {
        "gpt_call": GOAL_DETAILS_EXTRACT_GPT_CALL,
        "fields": [
            DEFAULT_CURRENT_DATE_CONTEXT_FIELD,
            DEFAULT_CURRENT_DAY_CONTEXT_FIELD,
            DEFAULT_ASSISTANT_MESSAGE_GOAL_FIELD,
            DEFAULT_USER_PROMPT_FIELD,
        ]

    },

    {
        "gpt_call": APPOINTMENT_EXTRACT_GPT_CALL,
        "fields": [
            DEFAULT_CURRENT_DATE_CONTEXT_FIELD,
            DEFAULT_CURRENT_DAY_CONTEXT_FIELD,
            DEFAULT_ASSISTANT_MESSAGE_APPOINTMENT_FIELD,
            DEFAULT_DOCTOR_STORE_FIELD,
            DEFAULT_USER_PROMPT_FIELD
        ]

    },
    
    {
        "gpt_call": CHAT_NORMAL_MODE_SELECTOR_GPT_CALL,
        "fields": [
            DEFAULT_USER_PROMPT_FIELD,
        ]

    },

]



