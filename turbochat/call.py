
from typing import Any
from turbochat.gptprompts import Messages, Tools


class GPT:


    def __init__(self, api_key, model="gpt-3.5-turbo") -> None:
        self.client = OpenAI(api_key=GPT_KEY)
        self.model = model

    
    def call(self, **kwargs):
        return self.client.chat.completions.create(model=self.model, **kwargs)


    @staticmethod
    def get_response_entry(response, return_first=True):
        
        if len(response.choices):
            
            if return_first: return response.choices[0].message.to_dict()
            else:
                return [msg.to_dict() for msg in response.choices]

        return None
    

    @staticmethod
    def get_reply(response, return_first=True):
        if len(response.choices):
            
            if return_first: return response.choices[0].message.content
            else:
                return [msg.content for msg in response.choices]


class GPTCallable:

    def __init__(self, gpt: GPT, messages: Messages):

        if not isinstance(gpt, GPT): raise TypeError("expected type for gpt: GPT")
        
        if not isinstance(messages, Messages): raise TypeError("expected type for messages: Messages")

        self.gpt = gpt
        self.messages = messages


    def _call(self): raise NotImplementedError

    
    def call(self):
        response = self._call(self)
        response_entry = GPT.get_response_entry(response)
        return response, response_entry


class ToolCall(GPTCallable):


    def __init__(self, gpt: GPT, messages: Messages, tool: Tools, required=False):
        super().__init__(gpt, messages)

        if not isinstance(tool, Tools): raise TypeError("expected type for tool: Tools")
        
        self.tool = tool
        self.required = required

    
    def _call(self):
        response = self.gpt.call(messages=self.messages.get_entries(), tools=self.tool.get_tools(), tool_choice=self.required)
        return response
    

    def call(self):
        response, response_entry = super().call()
        results = self.get_tool_results(response)
        return response, response_entry, results


    def get_tool_results(self, response):
        result = {}
        result = self.tool.get_results(response, result)
        return result


class Msg(GPTCallable):

    def __init__(self, gpt: GPT, messages: Messages):
        super().__init__(gpt, messages)

        self.gpt = gpt
        self.messages = messages

    def _call(self):
        response = self.gpt.call(messages=self.messages.get_entries())
        return response

    def call(self):
        response, response_entry = super().call()
        result = GPT.get_reply(response)
        return response, response_entry, result


