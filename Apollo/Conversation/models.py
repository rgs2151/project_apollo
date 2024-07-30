from rest_framework.request import Request
from mongoengine import Document, fields

from turbochat.v1.prompt import GPTMsgPrompt, GPTToolPrompt, GPTMsges
from turbochat.v1.gpt import Tool, Msg, GPT
from .converse.prompts.user import PromptMaker

from Conversation.converse.documents import PDF

import datetime, json
from bson import ObjectId


class UserNotFound(Exception): pass


class SessionNotFound(Exception): pass


class InvalidSession(Exception): pass


class NotFound(Exception): pass


class ToolCallNotFound(Exception): pass


class ContextCallNotFound(Exception): pass


class Prompt(Document):
    name = fields.StringField(required=True)
    purpose = fields.StringField(required=True)
    prompt = fields.DictField(required=True)

    meta = {"collection": "Prompt"}


    @classmethod
    def create_prompt(cls, name: str, purpose: str, prompt: dict):
        prompt: GPTMsgPrompt = GPTMsgPrompt(prompt)
        prompt_instance = cls(name=str(name), purpose=str(purpose), prompt=prompt.get_prompt())
        prompt_instance.save()
        return prompt_instance
    

    @classmethod
    def create_or_update_or_get(cls,**kwargs):
        
        if cls.objects(name=kwargs["name"]).count():

            fetched_instance = cls.objects(name=kwargs["name"]).first()

            if (
                fetched_instance.purpose == kwargs["purpose"] and
                fetched_instance.prompt == kwargs["prompt"]
            ): return cls.objects(name=kwargs["name"]).first()
            
            else:
                fetched_instance = cls.objects(name=kwargs["name"]).first()
                fetched_instance.purpose = kwargs["purpose"]
                fetched_instance.prompt = GPTMsgPrompt(kwargs["prompt"]).get_prompt()
                fetched_instance.save()
                return fetched_instance

        else: return cls.create_prompt(**kwargs)


    def get_prompt(self, raw=True):
        prompt = GPTMsgPrompt(self.prompt)
        return prompt if raw else prompt.get_prompt()


class ToolPrompt(Document):
    name = fields.StringField(required=True)
    purpose = fields.StringField(required=True)
    definition = fields.DictField(required=True)
    
    meta = {"collection": "Tool"}

    @classmethod
    def create(cls, name: str, purpose: str, definition: dict):
        tool_prompt = GPTToolPrompt(definition)
        prompt_instance = cls(name=str(name), purpose=str(purpose), definition=tool_prompt.get_prompt())
        prompt_instance.save()
        return prompt_instance

    
    def get_tool_prompt(self, raw=False):
        return self.definition if raw else GPTToolPrompt(self.definition)
    

    @classmethod
    def create_or_update_or_get(cls,**kwargs):
        
        if cls.objects(name=kwargs["name"]).count():
            
            fetched_instance = cls.objects(name=kwargs["name"]).first()

            if (
                fetched_instance.purpose == kwargs["purpose"] and
                fetched_instance.definition == kwargs["definition"]
            ): return cls.objects(name=kwargs["name"]).first()
            
            else:
                fetched_instance = cls.objects(name=kwargs["name"]).first()
                fetched_instance.purpose = kwargs["purpose"]
                fetched_instance.definition = GPTToolPrompt(kwargs["definition"]).get_prompt()
                fetched_instance.save()
                return fetched_instance

        else: return cls.create(**kwargs)


class ContextField(Document):
    name = fields.StringField(required=True, unique=True)
    field_type = fields.StringField(required=True, enum=["static", "functional"])
    value = fields.DynamicField(required=True)
    priority = fields.IntField(required=False, default=0)

    meta = { "collection": "ContextField" }

    @classmethod
    def create_functional_fields(cls, field_maps: dict):
        fields = []
        for key, value in field_maps.items():
            field = cls(**{
                "name": key, "value": value, "field_type": "functional"
            })
            field.save()
            fields.append(field)
        return fields


    @classmethod
    def make_fields(cls, fields: list, update=False):
        """
        fields = [
            {
                "name": values...
                "field_type": values...
                "value": values...
                "priority": values...
            }
        ]
        """

        if not isinstance(fields, list): raise Type("fields should be of type list")

        if not fields: raise ValueError("not fields to create")

        for field in fields:
            if ("name" not in field) or ("field_type" not in field) or ("value" not in field):
                raise ValueError('"name", "field_type", "value", field keys are required')


        for field in fields:
            if cls.objects(name=field.get("name")).count():
                fetched_field = cls.objects(name=field.get("name")).first()
                update_required = not (
                    fetched_field.name == field.get("name") and
                    fetched_field.field_type == field.get("field_type") and
                    fetched_field.value == field.get("value") and
                    fetched_field.priority == field.get("priority", 0)
                )

                if (not update) and update_required:
                    raise ValueError(f"field name: {field.get("name")} requested update but update flag is set to {update}")
                
                else:
                    fetched_field.field_type = field.get("field_type")
                    fetched_field.value = field.get("value")
                    fetched_field.percentage = field.get("percentage")
                    fetched_field.save()


        fields_collected = []
        for field in fields:

            if cls.objects(name=field.get("name")).count():
                fetched_field = cls.objects(name=field.get("name")).first()
                fields_collected.append(fetched_field)

            else:
                created_field = cls(**field)
                created_field.save()
                fields_collected.append(created_field)

        return fields_collected


class GPTCall(Document):
    name = fields.StringField(required=True, unique=True)
    purpose = fields.StringField(required=True)
    history_length = fields.IntField(required=False, min_value=-1, default=0)
    system_prompt = fields.ReferenceField(Prompt, required=False, default=None)
    tool = fields.ReferenceField(ToolPrompt, required=False, default=None)
    tool_choice = fields.StringField(required=False, nullable=True, enum=["auto", "required", "disabled"], default=None)
    tool_call = fields.StringField(required=False, default=None)
    gpt = fields.StringField(required=False, enum=["gpt-4o", "gpt-3.5"], default="gpt-4o")

    
    def __eq__(self, other):
        return (
            self.id == other.id and
            self.name == other.name and
            self.purpose == other.purpose and
            self.history_length == other.history_length and
            self.system_prompt == other.system_prompt and
            self.tool == other.tool and
            self.tool_choice == other.tool_choice and
            self.tool_call == other.tool_call and
            self.gpt == other.gpt
        )

    
    meta = { "collection": "GPTCall" }


    def is_tool_call(self): return True if self.tool else False


    @classmethod
    def create_message_call(cls, **kwargs):
        # remove tool reference keys if any
        kwargs.pop("tool", None)
        kwargs.pop("tool_choice", None)
        kwargs.pop("tool_call", None)

        instance = cls(**kwargs)
        instance.save()
        return instance
    

    @classmethod
    def create_tool_call(cls, **kwargs):
        if "tool" not in kwargs or "tool_choice" not in kwargs or "tool_call" not in kwargs:
            raise ValueError("creating tool call requires keys: tool, tool_choice, tool_call")
        
        if not isinstance(kwargs["tool"], ToolPrompt): raise TypeError("tool should be of type ToolPrompt")

        instance = cls(**kwargs)
        instance.save()
        return instance


    def get_gpt(self, gpt_key) -> GPT: return GPT(gpt_key, model=self.gpt)


    def get_gpt_call(self, gpt_key: str, messages, context_call_lookup_obj: object, tool_call_lookup_obj: object, summary=False, add_to_user_content=[]):

        if summary: summary={"name": self.name}

        if not isinstance(messages, list): raise TypeError("messages should be list")

        if not self.history_length: messages = []
        elif self.history_length == -1: pass
        else: messages = messages[:self.history_length]
        if summary:
            summary["messages"] = {}
            summary["messages"] = {"history": messages}

        system_prompt = {}
        if self.system_prompt:
            system_prompt = self.system_prompt.get_prompt(raw=False)
            messages = [system_prompt] + messages

        if summary: summary["messages"]["system_prompt"] = system_prompt

        if context_call_lookup_obj:
            context_content = Context.make_context_content(self, context_call_lookup_obj)
            content = [{"type": "text", "text": context_content}]
            if add_to_user_content:
                content = add_to_user_content + content
            context_prompt = { "role": "user", "content": content }
            messages += [context_prompt]
        
            if summary: summary["messages"]["user_prompt"] = context_prompt

        else: 
            if summary: summary["messages"]["user_prompt"] = {}
        
        # for msg in messages: print(json.dumps(msg, indent=1))

        messages = GPTMsges(messages)

        gpt = self.get_gpt(gpt_key)

        kwargs = {"gpt": gpt, "messages": messages}

        if summary: summary["gpt"] = self.gpt
        if summary: summary["is_tool_call"] = self.is_tool_call()

        if self.is_tool_call():
            
            if not hasattr(tool_call_lookup_obj, self.tool_call):
                raise ToolCallNotFound(f"tool call required {self.tool_call} was not found in object {tool_call_lookup_obj}")
            
            tool = GPTToolPrompt(self.tool.get_tool_prompt(raw=True))

            kwargs["tool"] = tool
            kwargs["tool_callable"] = getattr(tool_call_lookup_obj, self.tool_call)
            kwargs["tool_choice"] = self.tool_choice

            if summary: 
                summary["tool"] = {}
                summary["tool"]["name"] = self.tool.name
                summary["tool"]["callable"] = self.tool_call
                summary["tool"]["choice"] = self.tool_choice

            return_call = Tool(**kwargs)

        else: return_call = Msg(**kwargs)

        if summary: return return_call, summary
        return return_call


    @classmethod
    def make_gpt_calls(cls, config, update=False):
        """
        config = [
            {
                "name": "name",
                "purpose": "purpose",
                "history_length": -1,
                "system_prompt": {
                    "name": "name",
                    "purpose": "purpose",
                    "prompt": {gpt-prompt},
                },
                "tool": {
                    "name": "name",
                    "purpose": "purpose",
                    "definition": {gpt-tool-definition},
                },
                "tool_choice": "tool_choice",
                "tool_call": "tool_call",
                "gpt": "gpt",
            }
        ]
        """

        config_ = []
        for conf in config:
            conf_ = {}
            conf_.update(conf)

            if "system_prompt" in conf_ and conf_["system_prompt"]:
                conf_["system_prompt"] = Prompt.create_or_update_or_get(**conf_["system_prompt"])

            if "tool" in conf_ and conf_["tool"]:
                conf_["tool"] = ToolPrompt.create_or_update_or_get(**conf_["tool"])
            
            config_.append(conf_)

        tool_instances = []
        for conf in config_:
            conf_ = {}
            conf_.update(conf)

            if cls.objects(name=conf_["name"]).count():
                instance = cls.objects(name=conf_["name"]).first()
                if not (
                    instance.purpose == conf_.get("purpose", None) and
                    instance.history_length == conf_.get("history_length", 0) and
                    instance.system_prompt == conf_.get("system_prompt", None) and
                    instance.tool == conf_.get("tool", None) and
                    instance.tool_choice == conf_.get("tool_choice", None) and
                    instance.tool_call == conf_.get("tool_call", None) and
                    instance.gpt == conf_.get("gpt", "gpt-4o")
                ):
                    instance.purpose = conf_.get("purpose", None)
                    instance.history_length = conf_.get("history_length", 0)
                    instance.system_prompt = conf_.get("system_prompt", None)
                    instance.tool = conf_.get("tool", None)
                    instance.tool_choice = conf_.get("tool_choice", None)
                    instance.tool_call = conf_.get("tool_call", None)
                    instance.gpt = conf_.get("gpt", "gpt-4o")
                    instance.save()

                    tool_instances.append(instance)
                
                else: tool_instances.append(instance)

            else:
                is_tool = True if ( # is tool
                    "tool" in conf_ and conf_["tool"] and
                    "tool_choice" in conf_ and conf_["tool_choice"] and
                    "tool_call" in conf_ and conf_["tool_call"]
                ) else False

                if is_tool: tool_instances.append(cls.create_tool_call(**conf_))
                else: tool_instances.append(cls.create_message_call(**conf_))

        return tool_instances


    def get_context_fields(self):
        if Context.objects(gpt_call=self).count():
            context_maps = Context.objects(gpt_call=self).all()
            return [maps.context_field for maps in context_maps]
        return []


class Context(Document):
    gpt_call = fields.ReferenceField(GPTCall)
    context_field = fields.ReferenceField(ContextField)
    label = fields.StringField(required=True)
    key = fields.StringField(required=True)

    
    meta = {
        "collection": "Context",
        'indexes': [
            {
                'fields': ('gpt_call', 'context_field', 'key'),
                'unique': True
            }
        ]
    }
    

    @classmethod
    def map_context_field(cls, gpt_call:GPTCall, field_maps: list, update=False):
        """
        field_maps = [
            "field": ContextField(),
            "label": "some label",
            "key": "key"
        ]
        """
        
        if not isinstance(gpt_call, GPTCall): raise TypeError("gpt_call should be of instance GPTCall")

        if not (field_maps or isinstance(field_maps, list)): raise ValueError("no fields to map")

        fields = [x["field"] for x in field_maps]

        if not all(isinstance(x, ContextField) for x in fields): 
            raise TypeError("not all field of instance ContextField")
        
        if len(fields) != len({x.id for x in fields}): raise ValueError("fields contain duplicate values")
        

        field_maps = [(x["field"], x["key"], x["label"]) for x in field_maps]


        for conf in field_maps:

            field, key, label = conf

            if not ContextField.objects(id = field.id).count():
                raise ValueError(f"ContextField[{field.id}] does not exist")
        
            if cls.objects(gpt_call=gpt_call, context_field=field.id).count():

                found_map = cls.objects(gpt_call=gpt_call, context_field=field.id).first()

                update_field_map = not (
                    found_map.key == key and
                    found_map.label == label
                )

                if not update and update_field_map:
                    raise ValueError(f"update is set to {update} and Context for GPTCall[{gpt_call.id}] already contains maps from provided ContextField[{field_map['field'].id}]")

                else:
                    found_map.key = key
                    found_map.label = label
                    found_map.save()



            context_maps = []
            for conf in field_maps:

                field, key, label = conf

                if cls.objects(gpt_call=gpt_call, context_field=field.id).count():
                    found_map = cls.objects(gpt_call=gpt_call, context_field=field.id).first()
                    context_maps.append(found_map)

                else:
                    entry = {"gpt_call": gpt_call}
                    entry["context_field"] = field
                    entry.update({"key": key, "label": label})
                    context = cls(**entry)
                    context.save()
                    context_maps.append(context)

        return context_maps


    @classmethod
    def get_prompt_maker(cls, gpt_call: GPTCall):

        if not isinstance(gpt_call, GPTCall): raise TypeError("gpt_call should be of instance GPTCall")

        if not cls.objects(gpt_call=gpt_call).count():
            raise ValueError(f"Context for gpt_call[{gpt_call.id}] is empty")
        
        context = cls.objects(gpt_call=gpt_call).all()
        context = {c.key: {"label": c.label} for c in context}
        return PromptMaker(context)


    @classmethod
    def get_context(cls, gpt_call:GPTCall, include_priorities=False):
        
        if not cls.objects(gpt_call=gpt_call).count():
            raise NotFound("no context for gpt call found")
        
        context_fields = cls.objects(gpt_call=gpt_call).all()

        context = {}
        context_callables = {}
        for field in context_fields:
            field: Context
            if field.context_field.field_type == "static":
                context[field.key] = field.context_field.value
            else: context_callables[field.key] = field.context_field.value
        
        
        if include_priorities:
            priorities_context = {}
            priorities_context_callables = {}
            
            for field in context_fields:
                field: Context
                if field.context_field.field_type == "static":
                    priorities_context[field.key] = field.context_field.priority
                else: priorities_context_callables[field.key] = field.context_field.priority

            return context, context_callables, priorities_context, priorities_context_callables


        return context, context_callables

    
    @classmethod
    def make_context_content(cls, gpt_call: GPTCall, context_function_call_lookup: object):

        context, context_callables, priorities_context, priorities_context_callables = cls.get_context(gpt_call, include_priorities=True)

        for key, value in context_callables.items():
            if not hasattr(context_function_call_lookup, value):
                raise ContextCallNotFound(f"call required {value} was not found in object {context_function_call_lookup}")
            
            if callable(context_function_call_lookup): result = getattr(context_function_call_lookup, value)()
            else: result = getattr(context_function_call_lookup, value)()
            context[key] = result

        priorities_context.update(priorities_context_callables)
        context = {key: context[key] for key in sorted(priorities_context, key = lambda x: priorities_context[x])}

        prompt_maker: PromptMaker = cls.get_prompt_maker(gpt_call)

        return prompt_maker.get(context)


    @classmethod
    def make_context(cls, gpt_call: GPTCall, field_maps: list, update=False):
        """
        fields = [
            {
                "field": {
                    "name": "field_name",
                    "field_type": "static",
                    "value": "some value"
                },
                "label": "some label",
                "key": "key"
            }
        ]
        """
        
        if not isinstance(gpt_call, GPTCall): raise TypeError("gpt_call should be of instance GPTCall")

        fields = [x.get("field") for x in field_maps]
        fields = ContextField.make_fields(fields, update=update)

        field_maps_ = []
        for map_conf_, field in zip(field_maps, fields): 
            map_conf = {}
            map_conf.update(map_conf_)
            map_conf["field"] = field
            field_maps_.append(map_conf)

        context_maps = cls.map_context_field(gpt_call, field_maps_, update=update)

        return context_maps


class SessionState(Document):
    name = fields.StringField(required=True, unique=True)
    purpose = fields.StringField(required=True)
    
    meta = {"collection": "SessionState"}

    @classmethod
    def create_or_update_or_get(cls,**kwargs):
        
        if cls.objects(name=kwargs["name"]).count():

            fetched_instance = cls.objects(name=kwargs["name"]).first()

            if (
                fetched_instance.purpose == kwargs["purpose"]
            ): return cls.objects(name=kwargs["name"]).first()
            
            else:
                fetched_instance = cls.objects(name=kwargs["name"]).first()
                fetched_instance.purpose = kwargs["purpose"]
                fetched_instance.save()
                return fetched_instance

        else: 
            created_instance = cls(**kwargs)
            created_instance.save()
            return created_instance


class SessionStateGPTCalls(Document):
    gpt_call = fields.ReferenceField(GPTCall, required=True)
    session_state = fields.ReferenceField(SessionState, required=True)

    meta = {
        "collection": "SessionStateGPTCalls",
        'indexes': [
            {
                'fields': ('gpt_call', 'session_state'),
                'unique': True
            }
        ]
    }


    @classmethod
    def make_state_gptcall_maps(cls, config: list):
        """
        config = [
            {
                "gpt_calls": [
                    {
                        "name": "name",
                        "purpose": "purpose",
                        "history_length": -1,
                        "system_prompt": {
                            "name": "name",
                            "purpose": "purpose",
                            "prompt": {gpt-prompt},
                        },
                        "tool": {
                            "name": "name",
                            "purpose": "purpose",
                            "definition": {gpt-tool-definition},
                        },
                        "tool_choice": "tool_choice",
                        "tool_call": "tool_call",
                        "gpt": "gpt",
                    }
                ],
                "session_state": {
                    "name": "name",
                    "purpose": "purpose"
                }
            }
        ]
        """

        state_maps  = []
        for conf in config:
            conf_ = {}
            conf_.update(conf)

            conf_["session_state"] = SessionState.create_or_update_or_get(**conf_.pop("session_state"))
            conf_["gpt_calls"] = GPTCall.make_gpt_calls(conf_.pop("gpt_calls"), update=True)

            for gptcall in conf_["gpt_calls"]:

                if cls.objects(session_state=conf_["session_state"], gpt_call=gptcall).count():
                    fetched_instance = cls.objects(session_state=conf_["session_state"], gpt_call=gptcall).first()
                    state_maps.append(fetched_instance)

                else:
                    created_instance = cls(session_state=conf_["session_state"], gpt_call=gptcall)
                    created_instance.save()
                    state_maps.append(created_instance)
                    
        return state_maps


class SessionType(Document):
    name = fields.StringField(required=True)
    purpose = fields.StringField(required=True)
    session_state = fields.ReferenceField(SessionState, required=True)

    meta = {
        "collection": "SessionType",
        'indexes': [
            {
                'fields': ('name', 'session_state'),
                'unique': True
            }
        ]
    }

    
    @classmethod
    def make_session_type(cls, session_type: dict, update=True):
        """
        session_type = {
            "name": "name",
            "purpose": "purpose",
            "session_states": [
                {
                    "name": "name",
                    "purpose": "purpose"
                }
            ]
        }
        """

        if not isinstance(session_type, dict):
            raise TypeError("session_type should be of type dict")
        
        if "name" not in session_type and session_type["name"] and "purpose" not in session_type and session_type["purpose"]:
            raise ValueError("name and purpose are required inside session_type")
        

        session_type_ = {}
        session_type_.update(session_type)
        session_states = []
        for session_state in session_type_["session_states"]:
            session_states.append(SessionState.create_or_update_or_get(**session_state))
        session_type_["session_states"] = session_states


        session_types = []
        for session_state in session_type_.pop("session_states"):

            if cls.objects(name=session_type_["name"], session_state=session_state).count():
                
                fetched_instance = cls.objects(name=session_type_["name"], session_state=session_state).first()

                update_required = not (
                    fetched_instance.purpose == session_type_["purpose"]
                )

                if update_required and not update:
                    raise ValueError(f"SessionType instance already exists for session state and update is set to {update}")
                
                else:
                    fetched_instance.purpose = session_type_["purpose"]
                    fetched_instance.save()
                
                session_types.append(fetched_instance)

            else:
                created_instance = cls(session_state=session_state, **session_type_)
                created_instance.save()
                session_types.append(created_instance)

        return session_types

    
class Session(Document):

    user_id = fields.IntField(required=True, min=0)
    session_type = fields.ReferenceField(SessionType, required=True)
    created_at = fields.DateTimeField(required=False, default=datetime.datetime.now())
    archived = fields.BooleanField(required=False, default=False)
    archived_at = fields.DateTimeField(required=False, default=None)

    meta = {
        "collection": "Session",
        'indexes': [
            {
                'fields': ('user_id', 'session_type'),
                'unique': True,
                'partialFilterExpression': {'archived': False}
            }
        ]
    }


    def archive(self):
        self.archived = True
        self.archived_at = datetime.datetime.now()
        self.save()


    @classmethod
    def get_session_for_user(cls, user_id: int):
        if not isinstance(user_id, int):
            raise TypeError(f"expected user_id to be int found {type(user_id)}")
        
        if not cls.objects(user_id=user_id, archived=False).count():
            raise SessionNotFound(f"session not found for user_id: {user_id}")

        return cls.objects(user_id=user_id, archived=False).first()


    @classmethod
    def create_session_for_user(cls, user_id: int, session_type: str, session_state: str):
        session_type_instance = None
        if SessionState.objects(name=session_state).count():
            session_state_instance = SessionState.objects(name=session_state).first()
            if not SessionType.objects(name=session_type, session_state=session_state_instance).count():
                raise InvalidSession(f"session_type [{session_type}] with session_state [{session_state}] not found")
            else: session_type_instance = SessionType.objects(name=session_type, session_state=session_state_instance).first()
        else: raise InvalidSession(f"session_state [{session_state}] not found")

        session = cls(user_id=user_id, session_type=session_type_instance)
        session.save()
        return session


class ChatHistory(Document):
    session = fields.ReferenceField(Session, required=True)
    prompt = fields.DictField(required=True)
    created_at = fields.DateTimeField(default=datetime.datetime.now())
    
    meta = {'collection': 'Chat_History'}


class GPTCallHistory(Document):
    gpt_call = fields.ReferenceField(GPTCall, required=True)
    session = fields.ReferenceField(Session, required=True)
    response_json = fields.DictField(required=True)
    created_at = fields.DateTimeField(default=datetime.datetime.now())
    
    meta = {'collection': 'GPTCall_History'}


class ConversationHistoryWithFaissSupportSchema(Document):
    history_id = fields.IntField(required=True, min=0)
    vector_id = fields.IntField(required=True, min=0)
    i_parameter_label = fields.StringField(required=True)
    parameter_type = fields.StringField(required=True)
    parameter_value = fields.StringField(required=True)
    session = fields.ReferenceField(Session, required=True)

    meta = {
        'collection': 'Conversation_History_Wtih_FAISS',
    }


class DoctorsWithFaissSupportSchema(Document):
    history_id = fields.IntField(required=True, min=0)
    vector_id = fields.IntField(required=True, min=0)
    user_id = fields.IntField(required=True, min=0)
    dr_name = fields.StringField(required=False, default="")
    dr_specialist = fields.StringField(required=False, default="")
    i_dr_description = fields.StringField(required=False, default="")
    dr_days = fields.StringField(required=False, default="")
    dr_time_start = fields.StringField(required=False, default="")
    dr_time_end = fields.StringField(required=False, default="")
    created_at = fields.DateTimeField(default=datetime.datetime.now())
    
    meta = {
        "collection": "Doctors"
    }


class ServiceWithFaissSupportSchema(Document):
    history_id = fields.IntField(required=True, min=0)
    vector_id = fields.IntField(required=True, min=0)
    service_name = fields.StringField(required=False, default="")
    service_provider = fields.StringField(required=False, default="")
    i_service_description = fields.StringField(required=False, default="")
    service_cost = fields.StringField(required=False, default="")
    service_duration = fields.StringField(required=False, default="")
    created_at = fields.DateTimeField(default=datetime.datetime.now())
    
    meta = {
        "collection": "Service"
    }


class Events(Document):
    session = fields.ReferenceField(Session, required=True)
    event_type = fields.StringField(required=True)
    event_description = fields.StringField(required=True)
    event_contact = fields.StringField(required=True)
    event_contact_id = fields.StringField(required=True)
    event_date = fields.StringField(required=True)
    event_time = fields.StringField(required=True)
    event_status = fields.BooleanField(required=False, default=False)
    created_at = fields.DateTimeField(default=datetime.datetime.now())

    meta = {
        "collection": "Events"
    }


class Goals(Document):
    session = fields.ReferenceField(Session, required=True)
    goal_type = fields.StringField(required=True)
    goal_description = fields.StringField(required=True)
    goal_milestones = fields.StringField(required=True)
    goal_progress = fields.IntField(required=True)
    goal_target_date = fields.StringField(required=True)
    created_at = fields.DateTimeField(default=datetime.datetime.now())

    meta = {
        "collection": "Goals"
    }


class DocumentUploaded(Document):
    session = fields.ReferenceField(Session, required=True)
    file_bytes = fields.StringField(required=True)
    document_preview_bytes = fields.StringField(required=True)
    document_type = fields.StringField(required=False, enum=["pdf"], default="pdf")
    number_pages = fields.IntField(require=True, min_value=1)
    discription = fields.StringField(required=False)
    shared_globaly = fields.BooleanField(default=False)
    shared_at = fields.DateTimeField(required=False)
    created_at = fields.DateTimeField(default=datetime.datetime.now())

    meta = {
        "collection": "Documents_Uploaded"
    }


    @classmethod
    def from_pdf_document(cls, session: Session, pdf: PDF):
        imageio = pdf.get_page_image(0)
        doc = {
            "session": session,
            "file_bytes": pdf.get_document_base64_string(),
            "document_preview_bytes": pdf.IOtoBase64(imageio),
            "number_pages": len(pdf)
        }

        instance = cls(**doc)
        instance.save()
        return instance
    
    def share(self):
        self.shared_globaly = True
        self.shared_at = datetime.datetime.now()
        self.save()

    def unshare(self):
        self.shared_globaly = False
        self.shared_at = None
        self.save()



