from turbochat.gptprompts import *
from openai import OpenAI
from Apollo.settings import GPT_KEY


class Message:

    def __init__(self, prompt, context={}, system_instructions=None, history=None, tools: Tools=None) -> None:
        
        if not "message" in context:
            raise Exception("user message is required in context")

        self.context = context
        self.prompt = str(prompt)
        self.prompt.format(context)

        self.system_instructions = system_instructions
        self.history = history

        if not isinstance(tools, Tools):
            raise TypeError("tools should be of instance Tools")
        
        self.tools =  tools
        self.response = self.call_gpt()
        

    def make_message(self):
        
        system = System(self.system_instructions)
        user_prompt = User(self.prompt)

        if self.history:
            history_messages = Messages.from_text()

        prompts = [system] + history_messages.prompts + [user_prompt]
        return Messages(prompts)
    

    def call_gpt(self):

        message = self.make_message()

        client = OpenAI(api_key=GPT_KEY)
     
        response = None
        if self.self.tools:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[ {"role": "user", "content":"Understand and anlayze this prompt. Your response should strictly not be more than 5 words: "+prompt}],
                tools = self.tools.get_tools(),
                tool_choice="auto" # auto, required, disabled
            )
        
        else:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=message.get_entries(),
            )


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
        
        if self.tools:
            tool_calls = {}
            tool_calls = self.tools.get_results(self.response, tool_calls)

        return reply, tool_calls
    


