from .prompts.tool import *
from .toolcallables import *
from turbochat.v1.gpt import GPT, Tool
from turbochat.v1.prompt import GPTMsges, GPTToolPrompt
from Apollo.settings import GPT_KEY


class Registery():

    
    __REGISTRY = {
        "extract_user_related_information": {
            "tool_definition": {
                "tool": EXTRACT_USER_RELATED_INFO,
                "tool_callable": get_callable_df_with_columns(["i_parameter_label", "parameter_type", "parameter_value"]),
                "tool_choice": "required",
            },
            "gpt": {}
        }
    }


    @classmethod
    def get_registry(cls):
        return cls.__REGISTRY.copy()


    @classmethod
    def get_tool(cls, name: str, messages: GPTMsges):
        
        registry = cls.get_registry()
        if name not in registry:
            raise ValueError(f"tool: {name}, Not found in registry")
        
        if not isinstance(messages, GPTMsges):
            raise TypeError("messages should be of type turbochat.v1.gpt.Msg")
        
        tool_config = registry.get(name).copy()

        gpt_model = tool_config.pop("gpt", {})
        gpt = GPT(GPT_KEY, **gpt_model)

        tool_definition = tool_config.pop("tool_definition", {}).copy()
        if not tool_definition:
            raise ValueError(f"tool: {name}, tool_definition not found in registry")


        tool_definition["tool"] = GPTToolPrompt(tool_definition["tool"])

        return Tool(gpt, messages, **tool_definition)



