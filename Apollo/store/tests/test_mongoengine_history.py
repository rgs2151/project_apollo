from unittest import TestCase

from ..mongoengine import MongoHistory, MongoHistoryWithFAISS, IndexDocumentSchema

from mongoengine import Document, fields, connect
from mongoengine.base.metaclasses import TopLevelDocumentMetaclass

from rest_framework_mongoengine.serializers import DocumentSerializer

import pandas as pd



class ConversationHistorySchema(Document):
    history_id = fields.IntField(required=True, min=0)
    i_parameter_label = fields.StringField(required=True)
    parameter_type = fields.StringField(required=True)
    parameter_value = fields.StringField(required=True)

    meta = {
        'collection': 'Conversation_History',
    }


class ConversationHistoryWithFaissSupportSchema(Document):
    history_id = fields.IntField(required=True, min=0)
    i_parameter_label = fields.StringField(required=True)
    parameter_type = fields.StringField(required=True)
    parameter_value = fields.StringField(required=True)
    vector_id = fields.IntField(required=True, min=0)

    meta = {
        'collection': 'Conversation_History_Wtih_FAISS',
    }


class ConversationHistorySchemaSerializer(DocumentSerializer):
    class Meta:
        model = ConversationHistorySchema
        fields = '__all__'


class ConversationHistoryWithFaissSupportSchemaSerializer(DocumentSerializer):
    class Meta:
        model = ConversationHistoryWithFaissSupportSchema
        fields = '__all__'



instance = connect(db='Apollo', host="mongodb://localhost:27017/")


# python -m unittest history.tests.test_mongoengine_history
# python -m unittest history.tests.test_mongoengine_history.TestMongoHistory.test_retreive
# python -m unittest history.tests.test_mongoengine_history.TestMongoHistory.test_update
class TestMongoHistory(TestCase):


    def setUp(self):
        ConversationHistorySchema.drop_collection()


    def test_init(self):
        
        MH = MongoHistory(10, instance, ConversationHistorySchema, ConversationHistorySchemaSerializer)
        
        self.assertEqual(MH.document, ConversationHistorySchema)
        # self.assertEqual(MH.index_name, f"faiss_index_{ConversationHistorySchema._meta['collection']}")
        # self.assertIsInstance(MH.index_document_instance.__class__, TopLevelDocumentMetaclass)


    def test_retreive(self):

        MH = MongoHistory(10, instance, ConversationHistorySchema, ConversationHistorySchemaSerializer)
        instances = MH.retrieve()
        self.assertIsInstance(instances, pd.DataFrame)
        self.assertEqual(list(ConversationHistorySchema._fields.keys()), instances.columns.tolist())
        

    def test_update(self):

        MH = MongoHistory(10, instance, ConversationHistorySchema, ConversationHistorySchemaSerializer)

        update_history = pd.DataFrame([
            ["A", "b", "c"],
            ["A", "b", "c"],
            ["B", "b", "c"],
        ], columns=['i_parameter_label', 'parameter_type', 'parameter_value'])

        MH.update(update_history)
        df = MH.retrieve()
        self.assertEqual(df.shape[0], 2)

        MH.update(update_history)
        df = MH.retrieve()
        self.assertEqual(df.shape[0], 2)

        update_history = pd.DataFrame([
            ["A", "ee", "ee"],
        ], columns=['i_parameter_label', 'parameter_type', 'parameter_value'])
        
        MH.update(update_history)
        df = MH.retrieve()
        self.assertEqual(df.shape[0], 2)
        


# python -m unittest history.tests.test_mongoengine_history.TestMongoHistoryWithFAISS.test_update
# python -m unittest history.tests.test_mongoengine_history.TestMongoHistoryWithFAISS.test_get
class TestMongoHistoryWithFAISS(TestCase):


    def setUp(self):
        ConversationHistorySchema.drop_collection()
        IndexDocumentSchema.drop_collection()


    def test_init(self):

        MH = MongoHistoryWithFAISS(10, instance, ConversationHistoryWithFaissSupportSchema, ConversationHistoryWithFaissSupportSchemaSerializer)
        print(MH.store_index)


    def test_update(self):

        MH = MongoHistoryWithFAISS(10, instance, ConversationHistoryWithFaissSupportSchema, ConversationHistoryWithFaissSupportSchemaSerializer)
        
        update_history = pd.DataFrame([
            ["A", "b", "c"],
            ["A", "b", "c"],
            ["B", "b", "c"],
        ], columns=['i_parameter_label', 'parameter_type', 'parameter_value'])

        MH.update(update_history)
        df = MH.retrieve()
        self.assertEqual(df.shape[0], 2)
        self.assertEqual(MH.store_index.ntotal, 2)

        update_history = pd.DataFrame([
            ["A", "ee", "ee"],
        ], columns=['i_parameter_label', 'parameter_type', 'parameter_value'])
        MH.update(update_history)
        df = MH.retrieve()
        self.assertEqual(df.shape[0], 2)
        self.assertEqual(MH.store_index.ntotal, 2)


    def test_get(self):

        MH = MongoHistoryWithFAISS(10, instance, ConversationHistoryWithFaissSupportSchema, ConversationHistoryWithFaissSupportSchemaSerializer)

        update_history = pd.DataFrame([
            ["A", "b", "c"],
            ["A", "b", "c"],
            ["B", "b", "c"],
        ], columns=['i_parameter_label', 'parameter_type', 'parameter_value'])

        MH.update(update_history)
        df = MH.retrieve()
        self.assertEqual(df.shape[0], 2)

        print(MH.get("A", 10))

        

