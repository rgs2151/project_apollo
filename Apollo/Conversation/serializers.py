from .models import *
from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers
from UserManager.models import UserDetails
from UserManager.serializers import UserDetailsSerializer


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


class UserDetailsField(serializers.Field):
    
    def to_representation(self, value):
        try:
            user_details = UserDetails.objects.get(user__id=value)
            return UserDetailsSerializer(user_details).data
        except UserDetails.DoesNotExist:
            return None


class SessionSerializerWithUserDetails(DocumentSerializer):
    user_details = UserDetailsField(source="user_id")
    session_type = SessionTypeSerializer()
    class Meta:
        model = Session
        fields = '__all__'


class EventsSerializer(DocumentSerializer):
    session = SessionSerializerWithUserDetails()
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

