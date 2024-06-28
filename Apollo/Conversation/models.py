from django.db import models
from mongoengine import Document, fields



class ConversationHistoryWithFaissSupportSchema(Document):
    history_id = fields.IntField(required=True, min=0)
    i_parameter_label = fields.StringField(required=True)
    parameter_type = fields.StringField(required=True)
    parameter_value = fields.StringField(required=True)
    vector_id = fields.IntField(required=True, min=0)

    meta = {
        'collection': 'Conversation_History_Wtih_FAISS',
    }





