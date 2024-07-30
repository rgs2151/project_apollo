from turbochat.v1.schema import PromptValidator, SCHEMA_ASSISTANT_PROMPT, SCHEMA_USER_PROMPT, SCHEMA_SYSTEM_PROMPT


INVALID_PROMPT_INFO_MESSAGE = """
Prompts can be in following format

# system
{
    "role": "system",
    "content": "some text"
}


# user
{
    "role": "user",
    "content": "some text"
} or {
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "some text"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "some url"
            }
        }
    ]
}

# assistant



"""


class GPTMsgPrompt:

    _validator = PromptValidator()


    def __init__(self, prompt) -> None:
        
        status, errors = self.validate(prompt)
        if not status: raise ValueError("invalid prompt, prompt did not match any of the defined schemas")

        self.__prompt = prompt


    def get_prompt(self): return self.__prompt.copy()


    @staticmethod
    def validate(prompt):
        prompt = {"prompt": prompt}

        status = False
        for schema in [SCHEMA_ASSISTANT_PROMPT, SCHEMA_USER_PROMPT, SCHEMA_SYSTEM_PROMPT]:
            status = GPTMsgPrompt._validator.validate(prompt, schema)
            if status: break

        return status, GPTMsgPrompt._validator.errors


    def has_image(self):
        
        if self.is_user():
            content = self.__prompt["content"]
            if isinstance(content, list):
                for cont in content:
                    if "image_url" in cont: return True

        else: False

    
    def get_image_content(self):
        
        content_ = []
        if self.has_image():
            content = self.__prompt["content"]
            for cont in content:
                if "image_url" in cont:
                    content_.append(cont)
        
        return content_


    def is_user(self): return self.__prompt["role"] == "user"
    

    def is_assistant(self): return self.__prompt["role"] == "assistant"
    

    def is_system(self): return self.__prompt["role"] == "system"


    def get_text_content(self):
        
        prompt = self.get_prompt()
        content = prompt["content"]

        if isinstance(content, str): return content

        if isinstance(content, list):
            return "\n".join([cont['text'] for cont in content if cont['type'] == "text"])
        
        return ""



class GPTMsges:

    def __init__(self, prompts) -> None:
        
        status, errors = self.validate(prompts)
        if not status: raise ValueError(f"invlaid prompt encountered, {errors}")

        self.__prompts = [GPTMsgPrompt(prompt) for prompt in prompts]


    @staticmethod
    def validate(prompts):
        
        status = False
        errors = None
        for prompt in prompts:
            status, errors = GPTMsgPrompt.validate(prompt)
            if not status: break

        return status, errors


    def get_prompts(self): return [prompt.get_prompt() for prompt in self.__prompts]


class GPTToolPrompt:

    _validator = PromptValidator()

    def __init__(self, prompt: dict) -> None:
        # No way to validate tool definitions for not
        # any definition will be coonsidered as correct definition        
        
        self.__prompt = prompt


    def get_prompt(self): return self.__prompt.copy()
    
    

