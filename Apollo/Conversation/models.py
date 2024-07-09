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
    reset_state = fields.BooleanField(default=False)
    last_updated_at = fields.DateTimeField(default=datetime.datetime.now())

    meta = {
        "collection": "Conversation_State"
    }


    def reset(self):
        self.reset_state = True
        self.save()


    def set_mode(self, mode):
        self.conversation_state = mode
        self.save()

    
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


class Events(Document):
    user_id = fields.IntField(required=True, min=0)
    event_type = fields.StringField(required=True)
    event_description = fields.StringField(required=True)
    event_contact = fields.StringField(required=True)
    event_date = fields.StringField(required=True)
    event_time = fields.StringField(required=True)

    meta = {
        "collection": "Events"
    }


class Goals(Document):
    user_id = fields.IntField(required=True, min=0)
    goal_type = fields.StringField(required=True)
    goal_description = fields.StringField(required=True)
    goal_milestones = fields.StringField(required=True)
    goal_progress = fields.IntField(required=True)
    goal_target_date = fields.StringField(required=True)

    meta = {
        "collection": "Goals"
    }
