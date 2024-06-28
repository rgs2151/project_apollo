import re, json


class Prompt():
    
    def __init__(self, content: str): self.content = str(content)
        
    def __str__(self): return self.content
    
    def __repr__(self): return self.__str__()


class System(Prompt):
    
    def get_entry(self): return {'role': 'system', 'content': self.content}


class User(Prompt):
    
    def get_entry(self): return {'role': 'user', 'content': self.content}


class Assistant(Prompt):
    
    def get_entry(self): return {'role': 'assistant', 'content': self.content}


class Messages:
    
    def __init__(self, prompts: list) -> None:
        self.__set_prompts(prompts) 
        
    
    def __set_prompts(self, prompts):
        if not isinstance(prompts, list): raise TypeError
        if not all(isinstance(prompt, Prompt) for prompt in prompts): raise TypeError
        self.prompts = prompts

    
    def get_entries(self):
        return [prompt.get_entry() for prompt in self.prompts]


    def to_text(self):
        entries = self.get_entries()
        history_text = "\n\n"
        for entry in entries:
            history_text += f"[{entry["role"]}]\n"
            history_text += f"{entry["content"]}\n\n"
        
        return history_text


    @classmethod
    def from_text(cls, text):
        sections = re.split(r'\n\[(.*?)\]\n', text)
        sections = [section.replace("\n", "") for section in sections]
        sections = [section for section in sections if section]
        
        result = []
        for i in range(0, len(sections), 2):
            key = sections[i].lower().strip()
            content = sections[i + 1].strip()
            if key == 'system': value = System(content)
            elif key == 'user': value = User(content)
            elif key == 'assistant': value = Assistant(content)
            else: raise ValueError(f"key: {key} not recognised")
        
            result.append(value)
        
        return cls(result)


    @classmethod
    def from_txt_file(cls, file_path):
        with open(file_path, 'r') as f:
            return cls.from_text(f.read())


class Tools:
    
    def __init__(self, tool_definitions: list) -> None:
        """
        [
            {
                "name": name of the tool,
                "function": python function,
                "definition": chat gpt definition of tool
            }
        ]
        """
        self.tool_definitions = tool_definitions


    def get_tools(self):
        return [tool_definition['definition'] for tool_definition in self.tool_definitions]
    
    
    def get_results(self, response, stash={}):
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            
            for tool_call in tool_calls:
                
                function_name = tool_call.function.name
                
                available_functions_filtered = [tool_definition for tool_definition in  self.tool_definitions if function_name == tool_definition['definition']['function']['name']]
                if not available_functions_filtered:
                    raise ValueError(f"Function Not FOUND: {function_name}")
                
                tool_definition = available_functions_filtered[0]
                
                function_to_call = tool_definition['function']
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                
                if not tool_definition['name'] in stash:
                    stash[tool_definition['name']] = [function_response]
                else: stash[tool_definition['name']].append(function_response)
                    
        return stash

