from django.db import models
from mongoengine import Document, fields
import datetime


class ConversationHistoryWithFaissSupportSchema(Document):
    history_id = fields.IntField(required=True, min=0)
    vector_id = fields.IntField(required=True, min=0)
    i_parameter_label = fields.StringField(required=True)
    parameter_type = fields.StringField(required=True)
    parameter_value = fields.StringField(required=True)

    meta = {
        'collection': 'Conversation_History_Wtih_FAISS',
    }


class ConvHistory(Document):
    user_id = fields.IntField(required=True, min=0)
    role = fields.StringField(required=True)
    content = fields.StringField(required=True)
    created_at = fields.DateTimeField(default=datetime.datetime.now())

    meta = {
        'collection': 'Conversation_History',
    }


class ChatHistory(Document):
    user_id = fields.IntField(required=True, min=0)
    prompt = fields.DictField(required=True)
    created_at = fields.DateTimeField(default=datetime.datetime.now())
    meta = {
        'collection': 'Chat_History',
    }


class ConversationState(Document):
    user_id = fields.IntField(required=True, min=0)
    conversation_state = fields.StringField(required=False, default="")
    last_updated_at = fields.DateTimeField(default=datetime.datetime.now())

    meta = {
        "collection": "Conversation_State"
    }


class DoctorsWithFaissSupportSchema(Document):
    history_id = fields.IntField(required=True, min=0)
    vector_id = fields.IntField(required=True, min=0)
    dr_name = fields.StringField(required=False, default="")
    dr_specialist = fields.StringField(required=False, default="")
    i_dr_description = fields.StringField(required=False, default="")
    dr_days = fields.StringField(required=False, default="")
    dr_time_start = fields.StringField(required=False, default="")
    dr_time_end = fields.StringField(required=False, default="")
    
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
    
    meta = {
        "collection": "Service"
    }


class EventsData(Document):
    user_id = fields.IntField(required=True, min=0)
    event_type = fields.StringField(required=True)
    i_event_description = fields.StringField(required=True)
    event_contact = fields.StringField(required=True)
    event_date = fields.StringField(required=True)
    event_time = fields.StringField(required=True)
    
    meta = {
        "collection": "Events"
    }



