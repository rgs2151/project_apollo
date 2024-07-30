from turbochat.v1.prompt import GPTMsges, GPTToolPrompt
import json
from openai import OpenAI


class GPT:


    def __init__(self, api_key, model="gpt-3.5-turbo") -> None:
        self.client = OpenAI(api_key=api_key)
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

    def __init__(self, gpt: GPT, messages: GPTMsges):

        if not isinstance(gpt, GPT): raise TypeError("expected type for gpt: GPT")
        
        if not isinstance(messages, GPTMsges): raise TypeError("expected type for messages: GPTMsges")

        self.gpt = gpt
        self.messages = messages


    def _call(self): raise NotImplementedError

    
    def call(self):
        response = self._call()
        response_entry = GPT.get_response_entry(response)
        return response, response_entry


class Msg(GPTCallable):
    

    def __init__(self, gpt: GPT, messages: GPTMsges):
        super().__init__(gpt, messages)

        self.gpt = gpt
        self.messages = messages

    def _call(self):
        response = self.gpt.call(messages=self.messages.get_prompts())
        return response

    def call(self):
        response, response_entry = super().call()
        result = GPT.get_reply(response)
        return response, response_entry, result


class Tool(GPTCallable):


    def __init__(self, gpt: GPT, messages: GPTMsges, tool: GPTToolPrompt, tool_callable, tool_choice="required"):
        super().__init__(gpt, messages)

        if not isinstance(tool, GPTToolPrompt): raise TypeError("expected type for tool: GPTToolPrompt")

        choices = ["auto", "required", "disabled"]
        if not tool_choice in choices:
            raise ValueError(f"tool_choice can be one of {','.join(choices)}")
        
        if not callable(tool_callable): raise ValueError("tool_callable should be callable")

        self.tool = tool
        self.tool_choice = tool_choice
        self.tool_callable = tool_callable


    def _call(self):
        response = self.gpt.call(messages=self.messages.get_prompts(), tools=[self.tool.get_prompt()], tool_choice=self.tool_choice)
        return response
    

    def call(self):
        response, response_entry = super().call()
        result = self.get_results(response, self.tool, self.tool_callable)

        return response, response_entry, result


    @staticmethod
    def get_results(response, tool: GPTToolPrompt, tool_callable, collect={}):

        status = False

        if not collect: collect = {}

        try:
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:

                for tool_call in tool_calls:
                    
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    results = tool_callable(**tool_args)
                    
                    if not tool_name in collect:
                        collect[tool_name] = [results]
                    else: collect[tool_name].append(results)

                status = True

            return status, collect.copy()

        
        except Exception as err: return status, collect.copy()



        


