from unittest import TestCase
from v1.schema import *
from v1.gpt import *


GPT_API_KEY_PATH = r"C:\Users\nagen\Desktop\gpt\project_apollo\Apollo\openai_key"


class TestValidatiors(TestCase):


    def setUp(self):
        self.validator = PromptValidator()


    def test_user_prompt_validator(self):

        default_text_payload = {"content": "some string"}

        status = self.validator.validate(default_text_payload, SCHEMA_CONTENT_DEFAULT)
        self.assertTrue(status)


        _schema = {"_content": {**SCHEMA_DEFINITION_GPT4_TEXT}}
        status = self.validator.validate({
            "_content": {
                "type": "text",
                "text": "some text"
            }
        }, _schema)
        self.assertTrue(status)
        

        _schema = {"_content": {**SCHEMA_DEFINITION_GPT4_IMAGE}}
        status = self.validator.validate({
            "_content": {
                "type": "image_url",
                "image_url": {
                    "url": "some text"
                }
            }
        }, _schema)
        self.assertTrue(status)
        

        gpt4_image_payload = {
            "type": "image_url",
            "image_url": {
                "url": "some text"
            }
        }

        gpt4_text_payload = {
            "type": "text",
            "text": "some text"
        }

        status = self.validator.validate({"content": [gpt4_text_payload, gpt4_image_payload]}, SCHEMA_CONTENT_GPT4)
        self.assertTrue(status)
        status = self.validator.validate({"content": [gpt4_image_payload]}, SCHEMA_CONTENT_GPT4)
        self.assertTrue(status)
        status = self.validator.validate({"content": [gpt4_text_payload]}, SCHEMA_CONTENT_GPT4)
        self.assertTrue(status)
        

        status = self.validator.validate({
            "prompt": {
                "role": "user",
                "content": [
                    gpt4_text_payload, 
                    gpt4_image_payload
                ]
            }
        }, SCHEMA_USER_PROMPT)
        self.assertTrue(status)
        status = self.validator.validate({
            "prompt": {
                "role": "user",
                "content": "some text"
            }
        }, SCHEMA_USER_PROMPT)
        self.assertTrue(status)


    def test_assistant_prompt_validator(self):

        # tool inputs
        status = self.validator.validate({
            "tool": "some_tool",
            "tool_inputs": {
                "any": "key",
                "and": "values"
            },
        }, SCHEMA_TOOL_PROMPTS)
        self.assertTrue(status)


        status = self.validator.validate({
            "prompt": {
                "role": "assistant",
                "content": "some text",
            }
        }, SCHEMA_ASSISTANT_PROMPT)
        self.assertTrue(status)
        status = self.validator.validate({
            "prompt": {
                "role": "assistant",
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
                    },
                ],
            }
        }, SCHEMA_ASSISTANT_PROMPT)
        self.assertTrue(status)
        status = self.validator.validate({
            "prompt": {
                "role": "assistant",
                "tool": "tool_name",
                "tool_inputs": {
                    "any": "key",
                    "and": "values"
                }
            }
        }, SCHEMA_ASSISTANT_PROMPT)
        self.assertTrue(status)


    def test_system_prompt_validator(self):

        status = self.validator.validate({
            "prompt": {
                "role": "system",
                "content": "some text"
            }
        }, SCHEMA_SYSTEM_PROMPT)
        self.assertTrue(status)


class TestGPTCallables(TestCase):

    
    def setUp(self):

        # gpt api key
        with open(GPT_API_KEY_PATH, 'r') as f:
            self.api_key = f.read()


    def text_gpt(self):
        # will do this later
        pass


