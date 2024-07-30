from .gptcall import *

CHAT_SESSION_CONFIG = {

        "name": "chat",

        "purpose": "this session type governs the general conversation flow",

        "session_states": [

            {
                "session_state": {
                    "name": "normal",
                    "purpose": "default conversation mode"
                },
                "gpt_calls": [
                    KEY_INFORMATION_EXTRACT_GPT_CALL,
                    CHAT_NORMAL_REPLY_GENERATOR_GPT_CALL,
                    CHAT_NORMAL_MODE_SELECTOR_GPT_CALL
                ]
            },

            {
                "session_state": {
                    "name": "goal",
                    "purpose": "user wants to set a goal"
                },
                "gpt_calls": [
                    KEY_INFORMATION_EXTRACT_GPT_CALL,
                    CHAT_GOAL_REPLY_GENERATOR_GPT_CALL,
                    GOAL_DETAILS_EXTRACT_GPT_CALL,
                ]
            },

            {
                "session_state": {
                    "name": "appointment_or_service_purchase",
                    "purpose": "user wants to set an appointment with doctor"
                },
                "gpt_calls": [
                    KEY_INFORMATION_EXTRACT_GPT_CALL,
                    CHAT_APPOINTMENT_GOAL_REPLY_GENERATOR_GPT_CALL,
                    APPOINTMENT_EXTRACT_GPT_CALL
                ]
            },

        ]

}


DOCUMENT_UPLOAD_SESSION_CONFIG = {

    "name": "document_upload",

    "purpose": "this session type governs document upload",

    "session_states": [
        
        {
            "session_state": {
                "name": "upload",
                "purpose": "user wants to upload document"
            },
            "gpt_calls": [
                KEY_INFORMATION_EXTRACT_FOR_DOCUMENT_UPLOAD_GPT_CALL
            ]
        },        
        
    ]


}


