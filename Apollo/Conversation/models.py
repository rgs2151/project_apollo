from django.db import models
from mongoengine import Document, fields
import datetime


class ConversationHistoryWithFaissSupportSchema(Document):
    history_id = fields.IntField(required=True, min=0)
    i_parameter_label = fields.StringField(required=True)
    parameter_type = fields.StringField(required=True)
    parameter_value = fields.StringField(required=True)
    vector_id = fields.IntField(required=True, min=0)

    meta = {
        'collection': 'Conversation_History_Wtih_FAISS',
    }


class ConvHistory(Document):
    user_id = fields.IntField(required=True, min=0)
    role = fields.StringField(required=True)
    content = fields.StringField(required=True)
    created_at = fields.DateTimeField(default=datetime.datetime.now(), editable=False,)

    meta = {
        'collection': 'Conversation_History',
    }





