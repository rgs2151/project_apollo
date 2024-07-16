from django.test import TestCase


"python manage.py test Conversation.tests.TestTest.test_test_view"
class TestTest(TestCase):
    

    def test_test_view(self):

        payload = {
        "user_id": 10,
        "prompt": {
                "role": "user",
                "content": [
                        {
                                "type": "text",
                                "text": "I was diagnosed with diabetes"
                        }
                ]
        },
        }
        # response = self.client.post("/conversation/test-view/", payload, content_type='application/json')
        response = self.client.put("/conversation/test-view/", payload, content_type='application/json')
        print(response.content)


