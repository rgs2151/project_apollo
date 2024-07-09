import pandas as pd
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class History:

    def __init__(self, history_id=None) -> None:
        if history_id == None: raise ValueError("History ID is required")
        self.history_id = history_id
        self.len = None

    def retrieve(self): raise NotImplemented()
    
    def update(self): raise NotImplemented()
    
    def __str__(self):
        return f"{self.__class__.__name__}: [{self.len}]"


class FileHistory(History):

    __REQ_COLUMNS = ["parameter_label", "parameter_type", "parameter_value"]

    """
    history_config = {
        "columns": ["parameter_label", "parameter_type", "parameter_value"],
        "indexes": ["parameter_label"]
    }
    """

    def __init__(self, history_config, history_id, history_location='.', name="history") -> None:
        super().__init__(history_id)
        self.name = str(name)

        self._check_history_config(history_config)
        self.__load_history(history_location)

    
    def _check_history_config(self, history_config):
        if history_config and isinstance(history_config, dict) and ("columns" in history_config) and ("indexes" in history_config):
            print("HERE!!")
            if history_config['columns'] and isinstance(history_config['columns'], list) and history_config['indexes'] and isinstance(history_config['indexes'], list):
                print("HERE!")
                if all(col in history_config['columns'] for col in history_config['indexes']):
                    print("HERE")
                    self.history_config = history_config
                    return
        
        raise ValueError("unable to configure history_config")


    def validate_history(self, H):
        if isinstance(H, pd.DataFrame):
            if not all(col in self.history_config['columns'] for col in H.columns):
                return False

            return True


    def __load_history(self, history_location):

        if not history_location: history_location = '.'

        history = Path(f"{history_location}")

        if not (history.exists()):
            raise ValueError("invalid history location ! does not exist")
        
        location = self.__initialize_history_if_necessary(history)
        self._history_file = location
        self.H = pd.read_csv(str(self._history_file))
        if not self.validate_history(self.H):
            raise ValueError("loaded history incompatible with the history_config")
        for col in self.H.columns: self.H[col] = self.H[col].astype(str)


    def __initialize_history_if_necessary(self, location: Path):
        location /= f"{self.history_id}"
        if not location.exists(): location.mkdir()
        location /= f"{self.name}.csv"
        if not location.exists(): pd.DataFrame(columns=self.history_config['columns']).to_csv(str(location), index=False)
        return location


    def retrieve(self): return self.H.copy()


    def update(self, updated_history):
        if not self.validate_history(updated_history): raise ValueError("update history is invalid")
        
        new_history = pd.concat([self.H, updated_history])
        
        for col in new_history.columns:
            new_history[col] = new_history[col].str.lower().str.strip()
        
        indexes_dropped = new_history.duplicated(self.history_config["indexes"]).index.tolist()
        new_history = new_history.drop_duplicates(self.history_config["indexes"]).reset_index(drop=True)

        self.H = new_history
        new_history.to_csv(self._history_file, index=False)

        return new_history, indexes_dropped


class FileHistoryWithFAISS(FileHistory):


    def __init__(self, history_config, history_id, history_location: Path = None, name="history"):
        super().__init__(history_config, history_id, history_location, name)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        self.store_index = None
        if not self.H.empty: self.__set_up_faiss_store()


    def encode(self, texts):
        return self.embedding_model.encode(texts)


    def __encode_history(self, history):
        tdf = history[self.history_config['indexes']].copy()
        tdf = tdf.apply(lambda x: f"{x.name} :" + x).copy()
        tdf['index_context'] = tdf.apply(lambda x: " | ".join(x.tolist()), axis=1)
        return self.encode(tdf['index_context'].values.tolist())


    def __set_up_faiss_store(self):

        self.store_index_file = self._history_file.parent / f"{self._history_file.name}.index"

        if not self.store_index_file.exists():
            embeddings = self.__encode_history(self.retrieve())
            self.store_index = faiss.IndexFlatL2(embeddings.shape[1])
            self.store_index.add(embeddings)
            faiss.write_index(self.store_index, str(self.store_index_file))

        else:
            self.store_index = faiss.read_index(str(self.store_index_file))


    def update(self, updated_history):
        _, deleted_indexes = super().update(updated_history)
        
        if not self.store_index: self.__set_up_faiss_store()
        else:
            embeddings = self.__encode_history(self.retrieve())
            self.store_index.add(embeddings)
            self.store_index.remove_ids(np.array(deleted_indexes))
            faiss.write_index(str(self.store_index_file))


    def get(self, context, k=1):
        
        if self.store_index:
            embeddings = self.encode([context])
            result = self.store_index.search(embeddings, k=k)
            indexes = [i for i in result[1][0] if i >= 0]
            return self.H.iloc[indexes, :]
            
        return pd.DataFrame(columns=self.history_config['columns'])

