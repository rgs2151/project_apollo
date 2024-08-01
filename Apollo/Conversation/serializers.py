from .models import *
from rest_framework_mongoengine.serializers import DocumentSerializer


class ConversationHistoryWithFaissSupportSchemaSerializer(DocumentSerializer):
    class Meta:
        model = ConversationHistoryWithFaissSupportSchema
        fields = '__all__'


class SessionStateSerializer(DocumentSerializer):
    class Meta:
        model = SessionState
        fields = '__all__'


class SessionTypeSerializer(DocumentSerializer):
    session_state = SessionStateSerializer()
    class Meta:
        model = SessionType
        fields = '__all__'


class SessionSerializer(DocumentSerializer):
    session_type = SessionTypeSerializer()
    class Meta:
        model = Session
        fields = '__all__'


class ConvHistorySerializer(DocumentSerializer):
    session = SessionSerializer()
    class Meta:
        model = ChatHistory
        fields = '__all__'


class DoctorsWithFaissSupportSchemaSerializer(DocumentSerializer):
    class Meta:
        model = DoctorsWithFaissSupportSchema
        fields = '__all__'


class ServiceWithFaissSupportSchemaSerializer(DocumentSerializer):
    class Meta:
        model = ServiceWithFaissSupportSchema
        fields = '__all__'


class EventsSerializer(DocumentSerializer):
    class Meta:
        model = Events
        fields = '__all__'


class GoalsSerializer(DocumentSerializer):
    class Meta:
        model = Goals
        fields = '__all__'


class DocumentUploadedSerializer(DocumentSerializer):
    class Meta:
        model = DocumentUploaded
        # fields = '__all__'
        exclude = ("file_bytes",)

