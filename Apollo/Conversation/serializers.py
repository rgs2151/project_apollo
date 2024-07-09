from .models import *
from rest_framework_mongoengine.serializers import DocumentSerializer


class ConversationHistoryWithFaissSupportSchemaSerializer(DocumentSerializer):
    class Meta:
        model = ConversationHistoryWithFaissSupportSchema
        fields = '__all__'


class ConvHistorySerializer(DocumentSerializer):
    class Meta:
        model = ChatHistory
        fields = '__all__'

        
class ConversationStateSerializer(DocumentSerializer):
    class Meta:
        model = ConversationState
        fields = '__all__'

        
class DoctorsWithFaissSupportSchemaSerializer(DocumentSerializer):
    class Meta:
        model = DoctorsWithFaissSupportSchema
        fields = '__all__'


class ServiceWithFaissSupportSchemaSerializer(DocumentSerializer):
    class Meta:
        model = ServiceWithFaissSupportSchema
        fields = '__all__'


class EventsDataSerializer(DocumentSerializer):
    class Meta:
        model = Events
        fields = '__all__'


class GoalsSerializer(DocumentSerializer):
    class Meta:
        model = Goals
        fields = '__all__'

