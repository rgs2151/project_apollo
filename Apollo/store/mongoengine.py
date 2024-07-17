from .H import History
import datetime
import pandas as pd
import numpy as np
from io import BytesIO
import faiss
from sentence_transformers import SentenceTransformer
from mongoengine import Document
from pymongo.mongo_client import MongoClient
from mongoengine.base.metaclasses import TopLevelDocumentMetaclass
from mongoengine import Document, fields
from mongoengine.queryset.visitor import Q
from rest_framework_mongoengine.serializers import DocumentSerializer


class IndexDocumentSchema(Document):
    history_id = fields.IntField(required=True, min=0)
    index_name = fields.StringField(required=True)
    index = fields.BinaryField(required=True)

    meta = {
        "collection": "FAISS_Index_store"
    }


class MongoHistory(History):

    
    def __init__(self, history_id, instance: MongoClient, document: TopLevelDocumentMetaclass, document_serializer: DocumentSerializer) -> None:
        super().__init__(history_id)

        if not isinstance(instance, MongoClient):
            raise TypeError("instance should be pymongo.mongo_client.MongoClient")
        
        # if not isinstance(document_serializer, DocumentSerializer):
        #     raise TypeError("document_serializer should be rest_framework_mongoengine.serializers.DocumentSerializer")
        self.document_serializer = document_serializer

        self._set_document(document)

    
    def _set_document(self, document: TopLevelDocumentMetaclass):
        
        if not isinstance(document, TopLevelDocumentMetaclass):
            raise TypeError("document should be of type mongoengine.Document")
        
        if not hasattr(document, "history_id"):
            raise Exception("document does not contain key:history_id. This key is required")

        self.document = document


    def serialize_documents(self, instances):
        if instances:
            instance_data = self.document_serializer(instances, many=True).data
            instance_data = pd.DataFrame(instance_data, columns=list(self.document._fields.keys()))
            return instance_data
        return pd.DataFrame(columns=list(self.document._fields.keys()))
    
    def retrieve(self):
        instances = self.document.objects.filter(history_id=self.history_id)
        return self.serialize_documents(instances)
    

    def validate_history(self, H):
        if isinstance(H, pd.DataFrame):
            required_cols = self.document._fields.copy()
            required_cols.pop("id", None)
            required_cols.pop("history_id", None)
            required_cols = list(required_cols.keys())

            if not all(col in required_cols for col in H.columns):
                return False

            return True


    def get_indexes(self):
        return [x for x in self.document._fields.keys() if x.startswith("i_")]
        

    def _drop_duplicates(self, updated_history):
        indexes = self.get_indexes()
        updated_history = updated_history.drop_duplicates(indexes).reset_index(drop=True)

        deleted = []
        if indexes:
            # check for duplicates
            for i in range(updated_history.shape[0]):
                _filter = updated_history.loc[i, indexes].to_dict()
                isntances = self.document.objects(**_filter)

                deleted.extend([i for i in isntances])
                # delete ids
                if isntances: isntances.delete()

        return deleted, updated_history


    def update(self, updated_history: pd.DataFrame):
        
        if not self.validate_history(updated_history): raise ValueError("update history is invalid")
        
        deleted_ids, updated_history = self._drop_duplicates(updated_history)
        
        updated_history['history_id'] = self.history_id
        new_instances = updated_history.apply(lambda x: self.document(**x.to_dict()), axis=1)

        self.document.objects.insert(new_instances)

        return deleted_ids, new_instances


class MongoHistoryWithFAISS(MongoHistory):


    def __init__(self, history_id, instance: MongoClient, document: TopLevelDocumentMetaclass, document_serializer: DocumentSerializer) -> None:
        super().__init__(history_id, instance, document, document_serializer)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        if not hasattr(document, "vector_id"):
            raise Exception("document does not contain key:vector_id. This key is required")
        
        self.index_name = f'faiss_index_{document._meta["collection"]}'
        self.__set_up_faiss_store()


    def encode(self, texts):
        return self.embedding_model.encode(texts)


    def __encode_history(self, history):
        tdf = history[self.get_indexes()].copy()
        tdf = tdf.apply(lambda x: f"{x.name} :" + x)
        tdf['index_context'] = tdf.apply(lambda x: " | ".join(x.tolist()), axis=1)
        return self.encode(tdf['index_context'].values.tolist())


    def __save_store_index(self):

        index_io = BytesIO()
        faiss.write_index(self.store_index, faiss.PyCallbackIOWriter(index_io.write))
        
        if not self.store_index_document:
            index_document_instance = IndexDocumentSchema(history_id=self.history_id, index_name=self.index_name, index=index_io.getvalue())
            self.store_index_document = index_document_instance

        else:
            self.store_index_document.index = index_io.getvalue()

        self.store_index_document.save()


    def __set_up_faiss_store(self):
        
        index_document_instance = IndexDocumentSchema.objects(history_id=self.history_id, index_name=self.index_name).first()

        if index_document_instance:
            self.store_index_document = index_document_instance
            index_io = BytesIO(index_document_instance.index)
            self.store_index = faiss.read_index(faiss.PyCallbackIOReader(index_io.read))
        
        else:
            
            history = self.retrieve()

            if not history.empty:
                embeddings = self.__encode_history(history)
                self.store_index = faiss.IndexFlatL2(embeddings.shape[1])
                self.store_index.add(embeddings)
                self.store_index_document = None
                self.__save_store_index()

            else: self.store_index = None
        
    
    def  update(self, updated_history: pd.DataFrame):

        updated_history["vector_id"] = -1
        
        deleted_indexes, new_instances =  super().update(updated_history)
        
        if self.store_index:

            if deleted_indexes:
                deleted_indexes = [x.vector_id for x in deleted_indexes]
                self.store_index.remove_ids(np.array(deleted_indexes))

        else:  self.__set_up_faiss_store()

        existing_records = self.document.objects(history_id=self.history_id)
        existing_df = self.serialize_documents(existing_records)
        updated_instances = existing_df.drop(columns=['vector_id']).reset_index().rename(columns={"index": "vector_id"}).apply(lambda x: self.document(**x.to_dict()), axis=1)
        existing_records.delete()
        self.document.objects.insert(updated_instances)

        new_df = existing_df.iloc[-1*len(new_instances):, :]

        embeddings = self.__encode_history(new_df)
        self.store_index.add(embeddings)
        self.__save_store_index()


    def get(self, context, k=1):
        
        if self.store_index:
            embeddings = self.encode([context])
            result = self.store_index.search(embeddings, k=k)
            indexes = [i for i in result[1][0] if i >= 0]
            instances = self.document.objects(history_id=self.history_id, vector_id__in=indexes)
            return self.serialize_documents(instances)
            
        return self.serialize_documents(None)


    def reset(self):
        
        history = self.retrieve()
        
        if not isinstance(history, pd.DataFrame) and history.empty:
            
            if self.store_index_document:
                self.store_index_document.delete()
                self.store_index_document = None

            self.store_index = None

        else: self.update(history[[col for col in history.columns if col not in ["vector_id", "history_id"]]])

