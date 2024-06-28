from .models import *
from rest_framework_mongoengine.serializers import DocumentSerializer


class ConversationHistoryWithFaissSupportSchemaSerializer(DocumentSerializer):
    class Meta:
        model = ConversationHistoryWithFaissSupportSchema
        fields = '__all__'


class ConvHistorySerializer(DocumentSerializer):
    class Meta:
        model = ConvHistory
        fields = '__all__'

