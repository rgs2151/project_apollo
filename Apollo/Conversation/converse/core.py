from turbochat.gptprompts import *
from openai import OpenAI
from Apollo.settings import GPT_KEY


class Message:

    def __init__(self, prompt, context={}, system_instructions=None, history=None, tools: Tools=None) -> None:
        
        self.context = context
        self.prompt = str(prompt)
        self.prompt = self.prompt.format(**context)

        self.system_instructions = system_instructions
        self.history = history

        if tools and not isinstance(tools, Tools):
            raise TypeError("tools should be of instance Tools")
        
        self.tools =  tools
        self.response, self.tool_response = self.call_gpt()
        

    def make_message(self):
        
        system = System(self.system_instructions)
        user_prompt = User(self.prompt)

        if self.history:
            history_messages = Messages.from_text(self.history)
            prompts = [system] + history_messages.prompts + [user_prompt]

        else: prompts = [system, user_prompt]

        return Messages(prompts)
    

    def call_gpt(self):

        message = self.make_message()

        client = OpenAI(api_key=GPT_KEY)
     
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message.get_entries()
        )


        tool_response = None
        if self.tools:
            tool_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message.get_entries(),
                tools = self.tools.get_tools(),
                tool_choice="required" # auto, required, disabled
            )

        return response, tool_response


    def get_history(self, apetite=30):
        # will keep combination of
        messages = self.make_message()
        user = User(self.context.get("message", ""))
        prompts = messages.prompts[1:-1]
        prompts = prompts[apetite*-2:]
        prompts.append(user)
        return Messages(prompts).to_text()


    def get_results(self):

        reply = self.response.choices[0].message.content
        tool_calls = {}
        
        if self.tool_response:
            tool_calls = {}
            tool_calls = self.tools.get_results(self.tool_response, tool_calls)

        return reply, tool_calls
    


