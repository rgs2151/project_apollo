"""
GPT Prompts:
prompts are in the json format as defined in gpt request structure
Ability to validate and load the prompt in json format.
Default behaviour of gpt prompt
User, Assistant and system prompts handled in the same object
collecting prompts to messages
messages with various export capabilities
tool for tool calling
"""

import cerberus


class PromptValidator(cerberus.Validator):

    pass


SCHEMA_DEFINITION_DEFAULT = {
    "required": True,
    "empty": False
}


SCHEMA_DEFINITION_STRING_DEFAULT = {
    **SCHEMA_DEFINITION_DEFAULT,
    "type": "string"
}


SCHEMA_DEFINITION_LIST_DEFAULT = {
    **SCHEMA_DEFINITION_DEFAULT,
    "type": "list"
}


SCHEMA_DEFINITION_DICT_DEFAULT = {
    **SCHEMA_DEFINITION_DEFAULT,
    "type": "dict"
}


SCHEMA_CONTENT_DEFAULT = {
    "content": {**SCHEMA_DEFINITION_STRING_DEFAULT}
}


SCHEMA_DEFINITION_GPT4_TEXT = {
    **SCHEMA_DEFINITION_DICT_DEFAULT,
    "schema": {
        "type": {
            **SCHEMA_DEFINITION_STRING_DEFAULT,
            "allowed": ["text"]
        },
        "text": {**SCHEMA_DEFINITION_STRING_DEFAULT}
    }
}


SCHEMA_DEFINITION_GPT4_IMAGE = {
    **SCHEMA_DEFINITION_DICT_DEFAULT,
    "schema": {
        "type": {
            **SCHEMA_DEFINITION_STRING_DEFAULT,
            "allowed": ["image_url"]
        },
        "image_url": {
            **SCHEMA_DEFINITION_DICT_DEFAULT,
            "schema": {
                "url": {**SCHEMA_DEFINITION_STRING_DEFAULT}
            }
        }
    }
}


SCHEMA_CONTENT_GPT4 = {
    "content": {
        **SCHEMA_DEFINITION_LIST_DEFAULT,
        "schema": {
            "anyof": [
                SCHEMA_DEFINITION_GPT4_TEXT,
                SCHEMA_DEFINITION_GPT4_IMAGE
            ]
        }
    }
}


SCHEMA_USER_GPT4 = {
    "role": {**SCHEMA_DEFINITION_STRING_DEFAULT, "allowed": ["user"]},
    **SCHEMA_CONTENT_GPT4
}


SCHEMA_USER_DEFAULT = {
    "role": {**SCHEMA_DEFINITION_STRING_DEFAULT, "allowed": ["user"]},
    **SCHEMA_CONTENT_DEFAULT
}


SCHEMA_USER_PROMPT = {
    "prompt": {
        **SCHEMA_DEFINITION_DICT_DEFAULT,
        "anyof": [
            {"schema": SCHEMA_USER_DEFAULT},
            {"schema": SCHEMA_USER_GPT4}
        ]
    }
}


SCHEMA_TOOL_PROMPTS = {
    "tool": {**SCHEMA_DEFINITION_STRING_DEFAULT},
    "tool_inputs":{
        **SCHEMA_DEFINITION_DICT_DEFAULT,
        "allow_unknown": True
    }
}


SCHEMA_ASSISTANT_TOOL = {
    "role": {
        **SCHEMA_DEFINITION_STRING_DEFAULT,
        "allowed": ["assistant"]
    },
    **SCHEMA_TOOL_PROMPTS
}


SCHEMA_ASSISTANT_DEFAULT = {
    "role": {
        **SCHEMA_DEFINITION_STRING_DEFAULT, 
        "allowed": ["assistant"]
    },
    **SCHEMA_CONTENT_DEFAULT
}


SCHEMA_ASSISTANT_GPT4 = {
    "role": {
        **SCHEMA_DEFINITION_STRING_DEFAULT, 
        "allowed": ["assistant"]
    },
    **SCHEMA_CONTENT_GPT4
}


SCHEMA_ASSISTANT_PROMPT = {
    "prompt": {
        **SCHEMA_DEFINITION_DICT_DEFAULT,
        "anyof": [
            {"schema": SCHEMA_ASSISTANT_DEFAULT},
            {"schema": SCHEMA_ASSISTANT_GPT4},
            {"schema": SCHEMA_ASSISTANT_TOOL}
        ]
    }
}


SCHEMA_SYSTEM_DEFAULT = {
    "role": {
        **SCHEMA_DEFINITION_STRING_DEFAULT, 
        "allowed": ["system"]
    },
    **SCHEMA_CONTENT_DEFAULT
}


SCHEMA_SYSTEM_PROMPT = {
    "prompt": {
        **SCHEMA_DEFINITION_DICT_DEFAULT,
        "anyof": [
            {"schema": SCHEMA_SYSTEM_DEFAULT},
        ]
    }
}

