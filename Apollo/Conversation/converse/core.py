from turbochat.gptprompts import *
from openai import OpenAI
from Apollo.settings import GPT_KEY


class Message:

    def __init__(self, prompt, context={}, system_instructions=None, history=None, tools=[]) -> None:
        
        self.context = context
        self.prompt = str(prompt)
        self.prompt = self.prompt.format(**context)

        self.system_instructions = system_instructions
        self.history = history

        if tools and not all(isinstance(x[0], Tools) for x in tools):
            raise TypeError("tools should be of instance Tools")
        
        self.tools =  [x[0] for x in tools]
        self.tools_required = [x[1] for x in tools]
        self.response, self.tool_responses = self.call_gpt()
        

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


        tool_responses = []
        for tool, required in zip(self.tools, self.tools_required):
            tool: Tools
            tool_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message.get_entries(),
                tools = tool.get_tools(),
                tool_choice="required" if required else "auto"
            )

            tool_responses.append(tool_response)

        return response, tool_responses


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
        
        if self.tool_responses:
            tool_calls = {}
            for response, tools in zip(self.tool_responses, self.tools):
                tools: Tools
                tool_calls = tools.get_results(response, tool_calls)

        return reply, tool_calls
    


