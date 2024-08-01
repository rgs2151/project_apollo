import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

from pathlib import Path
import sys
sys.path.append("..")
print(">> Adding to path:", Path("..").absolute().resolve())

from mongoengine import connect, disconnect, get_db
from mongoengine.errors import NotUniqueError

from Conversation.models import *
from Conversation.apps import *
from Conversation.converse.sessionmanagers.chatsession import ChatSession

from unittest import TestCase

from .test_gpt_responses import *
import pandas as pd


with open("openai_key", "r") as f:
    GPT_KEY = f.read().strip()


RUN_GPT_CALL_TESTS = True


class MongoTestCase(TestCase):

    meta = {"db": "Apollo_Test", "alias": "default"}
    
    @classmethod
    def setUpClass(cls):
        cls.connection = connect(cls.meta["db"], alias=cls.meta["alias"], uuidRepresentation='standard')
        cls.db = get_db(alias=cls.meta["alias"])


    @classmethod
    def tearDownClass(cls):
        disconnect(alias=cls.meta["alias"])


    def tearDown(self):
        # Clear the database by dropping all collections
        db = self.connection[self.meta["db"]]
        for collection_name in db.list_collection_names():
            db.drop_collection(collection_name)


class TestSessionState(MongoTestCase):

    def test_create(self):
        state = SessionState(name="normal", purpose="testing ...")
        state.save()

        self.assertTrue(state.id)
        self.assertTrue(SessionState.objects(name="normal").count())

        # name should be unique
        with self.assertRaises(NotUniqueError):
            state = SessionState(name="normal", purpose="testing ...")
            state.save()
        

class TestSessionType(MongoTestCase):

    def test_create(self):
        state = SessionState(name="normal", purpose="testing ...")
        state.save()
        session_type = SessionType(name="chat", purpose="testing ...", session_state=state)
        session_type.save()

        self.assertTrue(session_type.id)
        self.assertTrue(SessionType.objects(name="chat").count())

        # (name, session_state unique)
        with self.assertRaises(NotUniqueError):
            session_type = SessionType(name="chat", purpose="testing ...", session_state=state)
            session_type.save()


def create_session_type(type_name, state_name):
    state = SessionState(name="normal", purpose="testing ...")
    state.save()
    session_type = SessionType(name="chat", purpose="testing ...", session_state=state)
    session_type.save()
    return session_type, state


def create_session(user_id, type_name, state_name):
    session_type, state = create_session_type(type_name, state_name)
    session = Session.create_session_for_user(user_id, "chat", "normal")
    return session, session_type, state


class TestSession(MongoTestCase):
    

    def test_create(self):
        session_type, state = create_session_type("chat", "normal")

        user_id = 10
        session = Session.create_session_for_user(user_id, "chat", "normal")
        self.assertEqual(session.user_id, user_id)
        self.assertEqual(session.session_type, session_type)

        # only 1 (user id, session_type) non archived can exist
        with self.assertRaises(NotUniqueError):
            session = Session.create_session_for_user(user_id, "chat", "normal")

        # 2 session archived session (user id, session_type) can exist
        session.archive()
        session = Session.create_session_for_user(user_id, "chat", "normal")


    def test_get(self):
        user_id = 10
        session, session_type, state = create_session(user_id, "chat", "normal")

        session_instance: Session = Session.get_session_for_user(user_id)
        self.assertEqual(session.id, session_instance.id)

        with self.assertRaises(SessionNotFound):
            Session.get_session_for_user(20)

        session_instance.archive()
        with self.assertRaises(SessionNotFound):
            Session.get_session_for_user(user_id)


class TestGPTCall(MongoTestCase):

    
    def test_create_basic_gpt_call(self):

        gpt_call = GPTCall(**{
            "name": "reply",
            "purpose": "generate message reply for normal conversation",
        })
        gpt_call.save()

        self.assertTrue(gpt_call.id)
        self.assertTrue(GPTCall.objects(name="reply").count())


    def test_get_gpt_call(self):
        pass


    def test_make_gpt_calls(self):
        
        gpt_calls_config = [
            {
                "name": "generate_reply",
                "purpose": "testing",
                "system_prompt": {
                    "name": "default_prompt",
                    "purpose": "testing",
                    "prompt": {
                        "role": "system",
                        "content": "this is the system prompt"
                    }
                },
            }
        ]

        calls = GPTCall.make_gpt_calls(gpt_calls_config)
        self.assertIsInstance(calls, list)

        self.assertEqual(Prompt.objects.count(), 1)

        for call in calls:
            call: GPTCall
            self.assertIsInstance(call, GPTCall)
            self.assertIsInstance(call.system_prompt, Prompt)
            self.assertTrue(call.id)
            self.assertTrue(call.system_prompt.id)

        gpt_calls_config = [
            {
                "name": "generate_reply",
                "purpose": "testing",
                "system_prompt": {
                    "name": "default_prompt",
                    "purpose": "testing",
                    "prompt": {
                        "role": "system",
                        "content": "this is the system prompt"
                    }
                },
                "tool": {
                    "name": "reply_generator",
                    "purpose": "testing",
                    "definition": {
                        "tool checking is relaxed": "so can pass anything here for now !!"
                    },
                },
                "tool_choice": "required",
                "tool_call": "some_python_function"
            }
        ]

        calls = GPTCall.make_gpt_calls(gpt_calls_config)
        self.assertIsInstance(calls, list)

        self.assertEqual(Prompt.objects.count(), 1)
        self.assertEqual(ToolPrompt.objects.count(), 1)

        for call in calls:
            call: GPTCall
            self.assertIsInstance(call, GPTCall)
            self.assertIsInstance(call.system_prompt, Prompt)
            self.assertTrue(call.id)
            self.assertTrue(call.system_prompt.id)
        

    def test_get_context_fields(self):

        tool = {
            "name": "reply_generator",
            "purpose": "testing",
            "definition": {
                "tool checking is relaxed": "so can pass anything here for now !!"
            },
        }

        gpt_calls_config = [
            {
                "name": "generate_reply",
                "purpose": "testing",
                "system_prompt": {
                    "name": "default_prompt",
                    "purpose": "testing",
                    "prompt": {
                        "role": "system",
                        "content": "this is the system prompt"
                    }
                },
                "tool": tool,
                "tool_choice": "required",
                "tool_call": "some_python_function"
            }
        ]

        calls = GPTCall.make_gpt_calls(gpt_calls_config)
        call: GPTCall = calls[0]

        field_maps = [
            {
                "field": {
                    "name": "assistant_message",
                    "field_type": "static",
                    "value": "always doubt yourself"
                },
                "label": "Assistant message",
                "key": "assistant_message"
            },
            {
                "field": {
                    "name": "user_prompt",
                    "field_type": "static",
                    "value": "user says this"
                },
                "label": "User message",
                "key": "user_prompt"
            }
        ]
        context_maps = Context.make_context(call, field_maps)

        fields = call.get_context_fields()
        self.assertIsInstance(fields, list)
        self.assertEqual(ContextField.objects.count(), len(field_maps))
        for field in fields:
            self.assertIsInstance(field, ContextField)
            self.assertTrue(field.id)



class TestContextField(MongoTestCase):

    
    def test_create_functional_fields(self):

        field_maps = {
            "current_date": "get_current_date",
            "current_day": "get_current_day",
            "user_prompt": "get_user_prompt",
            "key_information": "store_get_key_information"
        }

        fields = ContextField.create_functional_fields(field_maps)

        self.assertEqual(len(fields), len(field_maps.keys()))
        for field in fields:
            self.assertIsInstance(field, ContextField)
            self.assertTrue(field.id)
        

    def test_make_context(self):

        make_fields = [{"name": "field_1","field_type": "static","value": "some static value"}]

        fields = ContextField.make_fields(make_fields)
        self.assertIsInstance(fields, list)
        for field in fields:
            self.assertIsInstance(field, ContextField)
            self.assertTrue(field.id)
            self.assertFalse(field.priority)

        make_fields = [{"name": "field_1","field_type": "functional","value": "some_function"}]

        # updating field_1 without update flag should raise error
        with self.assertRaises(ValueError):
            updated_fields = ContextField.make_fields(make_fields)

        updated_fields = ContextField.make_fields(make_fields, update=True)
        self.assertEqual(updated_fields[0].id, fields[0].id)
        self.assertEqual(updated_fields[0].field_type, "functional")
        self.assertEqual(updated_fields[0].value, "some_function")
        

        make_fields = [
            {"name": "field_2", "field_type": "functional", "value": "some_function"},
            {"name": "field_3", "field_type": "static", "value": "static value"}
        ]
        updated_fields = ContextField.make_fields(make_fields)
        self.assertIsInstance(fields, list)
        for field in fields:
            self.assertIsInstance(field, ContextField)
            self.assertTrue(field.id)
            self.assertFalse(field.priority)

        self.assertEqual(ContextField.objects.count(), 3)


def create_sample_gpt_call_context():
    
    field_maps = {
        "current_date": "get_current_date",
        "current_day": "get_current_day",
        "key_information": "store_get_key_information",
        "user_prompt": "get_user_prompt",
    }
    
    fields = ContextField.create_functional_fields(field_maps)

    gpt_call = GPTCall(**{
        "name": "reply",
        "purpose": "generate message reply for normal conversation"
    })
    gpt_call.save()

    field_maps = [
        {"key": "current_date", "label": "today's date"},
        {"key": "current_day", "label": "today's day"},
        {"key": "history", "label": "User related information"},
        {"key": "user_prompt", "label": "user prompt"},
    ]
    for field_map, field in zip(field_maps, fields):
        field_map["field"] = field

    contexts = Context.map_context_field(gpt_call, field_maps)
    
    return gpt_call


class TestContext(MongoTestCase):


    def test_create_context(self):

        field_maps = {
            "current_date": "get_current_date",
            "current_day": "get_current_day",
            "key_information": "store_get_key_information",
            "user_prompt": "get_user_prompt",
        }
        
        fields = ContextField.create_functional_fields(field_maps)

        gpt_call = GPTCall(**{
            "name": "reply",
            "purpose": "generate message reply for normal conversation",
        })
        gpt_call.save()

        field_maps = [
            {"key": "current_date", "label": "today's date"},
            {"key": "current_day", "label": "today's day"},
            {"key": "history", "label": "User related information"},
            {"key": "user_prompt", "label": "user prompt"},
        ]
        for field_map, field in zip(field_maps, fields):
            field_map["field"] = field

        contexts = Context.map_context_field(gpt_call, field_maps)

        self.assertEqual(len(contexts), len(fields))
        for context in contexts:
            self.assertIsInstance(context, Context)
            self.assertTrue(context.id)
            self.assertEqual(context.gpt_call, gpt_call)


    def test_get_prompt_maker(self):

        gpt_call: GPTCall = create_sample_gpt_call_context()
        self.assertIsInstance(gpt_call, GPTCall)

        prompt_maker: PromptMaker = Context.get_prompt_maker(gpt_call)
        self.assertIsInstance(prompt_maker, PromptMaker)

        context = {
            "current_date": datetime.datetime.now().strftime("%d-%m-%Y"),
            "current_day": datetime.datetime.now().strftime("%A"),
            "history": "[{'prameter': 'parameter 1'}]",
            "user_prompt": "Hi, how are you doing?",
        }

        prompt = prompt_maker.get(context)
        self.assertIsInstance(prompt, str)
        for value in context.values(): self.assertTrue(value in prompt)
        
        self.assertTrue("today's date" in prompt)
        self.assertTrue("today's day" in prompt)
        self.assertTrue("User related information" in prompt)
        self.assertTrue("user prompt" in prompt)

        # print(">>" * 5, '\n' , prompt, '\n', ">>" * 5)


    def test_get_context(self):

        gpt_call: GPTCall = create_sample_gpt_call_context()

        context, context_callable = Context.get_context(gpt_call)
        self.assertIsInstance(context, dict)
        self.assertIsInstance(context_callable, dict)


    def test_make_context_content(self):
        field1 = ContextField(
            name = 'field_1', field_type = 'static', value = '10-09-1999', priority = 100
        )
        field2 = ContextField(
            name = 'field_2', field_type = 'functional', value = 'get_field_2', priority = 50
        )
        field1.save()
        field2.save()

        gpt_call = GPTCall.create_message_call(name="gpt_call", purpose="testing ...")

        context_1_1 = Context(
            gpt_call = gpt_call, context_field = field1, label = "field 1 was", key = "field_1"
        )
        context_1_2 = Context(
            gpt_call = gpt_call, context_field = field2, label = "field 2 was", key = "field_2"
        )
        context_1_1.save()
        context_1_2.save()

        class LookUpHere:
            @staticmethod
            def get_field_2(): return "this was field 2"

        prompt = Context.make_context_content(gpt_call, LookUpHere)
        self.assertIsInstance(prompt, str)
        self.assertTrue(prompt.endswith("10-09-1999"))
        # print(">>\n", [prompt], "\n>>")


    def test_make_context(self):

        field_maps = [
            {
                "field": {
                    "name": "assistant_message",
                    "field_type": "static",
                    "value": "always doubt yourself"
                },
                "label": "Assistant message:",
                "key": "assistant_message"
            }
        ]

        gpt_call = GPTCall.create_message_call(**{
            "name": "reply",
            "purpose": "generate message reply for normal conversation",
        })

        context_maps = Context.make_context(gpt_call, field_maps)
        self.assertIsInstance(context_maps, list)

        for context_map in context_maps:
            self.assertIsInstance(context_map, Context)
            self.assertTrue(context_map.id)

        field_maps = [
            {
                "field": {
                    "name": "assistant_message",
                    "field_type": "functional",
                    "value": "always_doubt_yourself",
                    "priority": 100
                },
                "label": "Assistant message:",
                "key": "message_assistant"
            }
        ]

        with self.assertRaises(ValueError):
            context_maps_updated = Context.make_context(gpt_call, field_maps)

        context_maps_updated = Context.make_context(gpt_call, field_maps, update=True)
        self.assertEqual(context_maps_updated[0].id, context_maps[0].id)
        self.assertEqual(field_maps[0]["key"], context_maps_updated[0].key)


class TestPrompt(MongoTestCase):


    def test_create(self):

        Prompt.create_prompt(
            "sample_user_prompt", "testing ...",
            {
                "role": "user",
                "content": "testing ..."
            }
        )

        Prompt.create_prompt(
            "sample_user_prompt_1", "testing ...",
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "testing ..."
                    }
                ]
            }
        )

        Prompt.create_prompt(
            "sample_user_prompt_1", "testing ...",
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "testing ..."
                    }
                ]
            }
        )

        Prompt.create_prompt(
            "sample_user_prompt_1", "testing ...",
            {
                "role": "system",
                "content": "testing ..."
            }
        )


class TestSessionStateGPTCalls(MongoTestCase):

    def test_make_state_gptcall_maps(self):

        config = [
            {
                "gpt_calls": [
                    {
                        "name": "tool_name",
                        "purpose": "testing",
                        "history_length": -1,
                        "system_prompt": {
                            "name": "test sys promot",
                            "purpose": "testing",
                            "prompt": {
                                "role": "system",
                                "content": "some content"
                            },
                        },
                        "tool": {
                            "name": "testing_tool",
                            "purpose": "testing",
                            "definition": {"some": "definition"},
                        },
                        "tool_choice": "auto",
                        "tool_call": "get_testing_tool",
                        "gpt": "gpt-4o",
                    }
                ],
                "session_state": {
                    "name": "normal",
                    "purpose": "normal conversation"
                }
            }
        ]

        session_state_gptcall_maps = SessionStateGPTCalls.make_state_gptcall_maps(config)
        self.assertIsInstance(session_state_gptcall_maps, list)

        for map_instance in session_state_gptcall_maps:
            self.assertIsInstance(map_instance, SessionStateGPTCalls)
            self.assertTrue(map_instance.id)

        self.assertEqual(Prompt.objects.count(), 1)
        self.assertEqual(GPTCall.objects.count(), 1)
        self.assertEqual(ToolPrompt.objects.count(), 1)
        self.assertEqual(SessionState.objects.count(), 1)


class TestSessionType(MongoTestCase):

    def test_make_session_type(self):

        config = {
            "name": "chat",
            "purpose": "testing",
            "session_states": [
                {
                    "name": "normal",
                    "purpose": "testing"
                },
                {
                    "name": "goal",
                    "purpose": "testing"
                },
            ]
        }

        session_type_maps = SessionType.make_session_type(config)
        self.assertIsInstance(session_type_maps, list)

        for session_type in session_type_maps:
            self.assertIsInstance(session_type, SessionType)
            self.assertTrue(session_type.id)

        self.assertEqual(SessionState.objects.count(), 2)
        self.assertEqual(SessionType.objects.count(), 2)


class TestInitializeContexts(MongoTestCase):

    def test_init(self):
        
        InitializeContexts(CONTEXTS)
        InitializeContexts(CONTEXTS)

        print("\n----- InitializeContexts -----")
        print("Context:", Context.objects.count())
        print("GPTCall:", GPTCall.objects.count())
        print("ContextField:", ContextField.objects.count())
        print("Prompt:", Prompt.objects.count())
        print("ToolPrompt:", ToolPrompt.objects.count())
        print("SessionState:", SessionState.objects.count())
        print("SessionType:", SessionType.objects.count())
        print("\n")


class TestInitializeSessionConfig(MongoTestCase):

    def test_init(self):
        
        InitializeSessionConfig(CHAT_SESSION_CONFIG)
        InitializeSessionConfig(CHAT_SESSION_CONFIG)

        print("\n----- InitializeSessionConfig -----")
        print("Context:", Context.objects.count())
        print("GPTCall:", GPTCall.objects.count())
        print("ContextField:", ContextField.objects.count())
        print("Prompt:", Prompt.objects.count())
        print("ToolPrompt:", ToolPrompt.objects.count())
        print("SessionState:", SessionState.objects.count())
        print("SessionType:", SessionType.objects.count())
        print("\n")


class SessionTestCase(MongoTestCase):

    def setUp(self):
        super().setUp()
        InitializeContexts(CONTEXTS)
        InitializeSessionConfig(CHAT_SESSION_CONFIG)
    

# python -m unittest tests.test_session.TestChatSession
# python -m unittest tests.test_session.TestChatSession.test_get_reply
# python -m unittest tests.test_session.TestChatSession.test_get_key_information
# python -m unittest tests.test_session.TestChatSession.test_get_mode_required_tool_results
class TestChatSession(SessionTestCase):


    def test_get_session(self):
        session: Session = ChatSession.get_session(10)
        self.assertIsInstance(session, Session)
        self.assertEqual(session.user_id, 10)
        self.assertTrue(session.id)
        self.assertEqual(session.session_type.name, "chat")
        self.assertEqual(session.session_type.session_state.name, "normal")
        self.assertTrue(session.session_type.id)


    def test_get_gpt_calls(self):

        session: Session = ChatSession.get_session(10)

        chat_session = ChatSession(self.connection, GPT_KEY, session)
        gpt_calls: list = chat_session.get_gpt_calls()

        self.assertIsInstance(gpt_calls, list)
        for call in gpt_calls:
            self.assertIsInstance(call, GPTCall)
            self.assertTrue(call.id)


    def test_get_reply_call(self):
        
        session: Session = ChatSession.get_session(10)

        chat_session = ChatSession(self.connection, GPT_KEY, session)
        gpt_calls: GPTCall = chat_session.get_reply_call()

        self.assertIsInstance(gpt_calls, GPTCall)
        self.assertTrue(gpt_calls.id)
        self.assertTrue("reply" in gpt_calls.name)


    def test_get_chat_messages(self):

        session: Session = ChatSession.get_session(10)
        
        chat_session = ChatSession(self.connection, GPT_KEY, session)
        history = chat_session.get_chat_messages()
        self.assertIsInstance(history, list)
        self.assertFalse(history)

        ChatHistory(session=session, prompt={
            "role": "user",
            "content": "some content"
        }).save()
        ChatHistory(session=session, prompt={
            "role": "assistant",
            "content": "some content"
        }).save()


        history = chat_session.get_chat_messages()
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 2)

        for hist in history: self.assertIsInstance(hist, dict)


    def test_log_gpt_call(self):

        session: Session = ChatSession.get_session(10)
        
        chat_session = ChatSession(self.connection, GPT_KEY, session)
        gpt_call: GPTCall = chat_session.get_reply_call()

        chat_session.log_gpt_call(gpt_call, SAMPLE_GPT_REPLY_RESPONSE)

        self.assertEqual(GPTCallHistory.objects(gpt_call=gpt_call).count(), 1)
        
        gpt_call_history: GPTCallHistory = GPTCallHistory.objects(gpt_call=gpt_call).first()
        self.assertTrue(gpt_call_history)
        self.assertEqual(gpt_call_history.response_json, SAMPLE_GPT_REPLY_RESPONSE.to_dict())


    def test_get_reply(self):
        
        if not RUN_GPT_CALL_TESTS: return

        session: Session = ChatSession.get_session(10)

        chat_session = ChatSession(self.connection, GPT_KEY, session)
        reply_gpt_call = chat_session.get_reply_call()
        reply = chat_session.get_reply({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I am going to climb mount everest next month",
                }
            ],
        })

        self.assertIsInstance(reply, str)
        self.assertIsInstance(reply_gpt_call, GPTCall)

        self.assertEqual(GPTCallHistory.objects(session=session).count(), 1)
        self.assertEqual(GPTCallHistory.objects(session=session, gpt_call=reply_gpt_call).count(), 1)
        self.assertEqual(ChatHistory.objects(session=session).count(), 2)
        
        for history, assistant in zip(ChatHistory.objects(session=session).all(), ["user", "assistant"]):
            self.assertIsInstance(history, ChatHistory)
            self.assertIsInstance(history.prompt, dict)
            self.assertEqual(history.prompt["role"], assistant)


    def test_get_key_information_extract_tool(self):

        session: Session = ChatSession.get_session(10)

        chat_session = ChatSession(self.connection, GPT_KEY, session)
        gpt_call: GPTCall = chat_session.get_key_information_extract_tool()

        self.assertIsInstance(gpt_call, GPTCall)
        self.assertTrue(gpt_call.id)
        self.assertTrue("key_information" in gpt_call.name)


    def test_get_key_information(self):

        if not RUN_GPT_CALL_TESTS: return

        session: Session = ChatSession.get_session(10)

        chat_session = ChatSession(self.connection, GPT_KEY, session)
        gpt_call = chat_session.get_key_information_extract_tool()

        result = chat_session.get_key_information({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I have type 2 diabetes. and headache due to overworking."
                }
            ]
        })

        self.assertEqual(GPTCallHistory.objects(session=session).count(), 1)
        self.assertEqual(GPTCallHistory.objects(session=session, gpt_call=gpt_call).count(), 1)

        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], dict)
        self.assertIn("extract_user_health_information_entry", result[1])
        self.assertIsInstance(result[1]["extract_user_health_information_entry"][0], pd.DataFrame)

        # print(result[1]["extract_user_health_information_entry"][0].to_markdown())

    
    def test_store_key_information(self):

        if not RUN_GPT_CALL_TESTS: return

        session: Session = ChatSession.get_session(10)

        chat_session = ChatSession(self.connection, GPT_KEY, session)

        chat_session.store_key_information({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I have type 2 diabetes. and headache due to overworking."
                }
            ]
        })

        self.assertTrue(ConversationHistoryWithFaissSupportSchema.objects.count())
        self.assertTrue(ConversationHistoryWithFaissSupportSchema.objects(session=session).count())
        
        for history in ConversationHistoryWithFaissSupportSchema.objects(session=session).all():
            self.assertEqual(history.session, session)
        
    
    def test_get_mode_tool_call(self):

        session: Session = ChatSession.get_session(10)

        chat_session = ChatSession(self.connection, GPT_KEY, session)
        gpt_calls: GPTCall = chat_session.get_mode_tool_call()

        self.assertIsInstance(gpt_calls, GPTCall)
        self.assertTrue(gpt_calls.id)
        self.assertTrue("mode" in gpt_calls.name)

    
    def test_get_mode(self):

        if not RUN_GPT_CALL_TESTS: return

        session: Session = ChatSession.get_session(10)
        
        chat_session = ChatSession(self.connection, GPT_KEY, session)
        gpt_call = chat_session.get_mode_tool_call()
        
        mode = chat_session.get_mode({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I want to set up goal to control my diabetes"
                }
            ]
        })

        self.assertEqual(GPTCallHistory.objects(session=session).count(), 1)
        self.assertEqual(GPTCallHistory.objects(session=session, gpt_call=gpt_call).count(), 1)

        self.assertIsInstance(mode, str)
        print(">>", mode)


    def test_get_next_session(self):
        
        if not RUN_GPT_CALL_TESTS: return

        session: Session = ChatSession.get_session(10)
        
        chat_session = ChatSession(self.connection, GPT_KEY, session)

        user_prompt_will_give_normal_mode = {
            "role": "user", "content": [
                {"type": "text", "text": "Hi how are you doing"}
            ]
        }

        # should give the same session
        next_session = chat_session.get_next_session(user_prompt_will_give_normal_mode)
        self.assertIsInstance(next_session, Session)
        self.assertEqual(session, next_session)
        self.assertEqual(next_session.session_type.session_state.name, "normal")
        
        user_prompt_will_give_goal_mode = {
            "role": "user", "content": [
                {"type": "text", "text": "I want to set up goal to control my diabetes"}
            ]
        }

        # should give new session
        next_session = chat_session.get_next_session(user_prompt_will_give_goal_mode)
        self.assertIsInstance(next_session, Session)
        self.assertNotEqual(session, next_session)
        self.assertEqual(next_session.session_type.session_state.name, "goal")


    def test_get_chatsession(self):

        if not RUN_GPT_CALL_TESTS: return

        # assuming previous mode was normal
        session: Session = ChatSession.get_session(10)

        user_prompt_will_give_normal_mode = {
            "role": "user", "content": [
                {"type": "text", "text": "Hi how are you doing"}
            ]
        }
        chat_session = ChatSession.get_chatsession(self.connection, GPT_KEY, session, user_prompt_will_give_normal_mode)

        self.assertIsInstance(chat_session, ChatSession)
        self.assertEqual(chat_session.session, session)


        user_prompt_will_give_goal_mode = {
            "role": "user", "content": [
                {"type": "text", "text": "I want to set up goal to control my diabetes"}
            ]
        }

        chat_session = ChatSession.get_chatsession(self.connection, GPT_KEY, session, user_prompt_will_give_goal_mode)
        self.assertIsInstance(chat_session, ChatSession)
        self.assertNotEqual(chat_session.session, session)
        self.assertEqual(chat_session.session.session_type.session_state.name, "goal")

    
    def test_get_mode_required_tools(self):

        session: Session = ChatSession.get_session(10, session_state="goal")
        
        chat_session = ChatSession(self.connection, GPT_KEY, session)

        # goal has 1 non mandatory tool
        tools = chat_session.get_mode_required_tools()
        self.assertIsInstance(tools, list)
        self.assertTrue(tools)

        for tool_call in tools:
            self.assertIsInstance(tool_call, GPTCall)
            self.assertTrue(tool_call.id)
            self.assertNotIn("mode", tool_call)
            self.assertNotIn("reply", tool_call)
            self.assertNotIn("key_information", tool_call)


# unable to test it
#    def test_get_mode_required_tool_results(self):

        if not RUN_GPT_CALL_TESTS: return

        session: Session = ChatSession.get_session(10, session_state="goal")
        
        chat_session = ChatSession(self.connection, GPT_KEY, session)

        user_prompt_will_give_goal_tool_call = {
            "role": "user", "content": [
                {"type": "text", "text": "I want to set up goal to control my diabetes. I have started the journey by taking my medicines regularly from last week and plan to take for next month."}
            ]
        }

        tool_results = chat_session.get_mode_required_tool_results(user_prompt_will_give_goal_tool_call)

        
