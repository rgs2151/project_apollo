from openai import OpenAI
from pathlib import Path
import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import io
import fitz

import sys
sys.path.append("..")

from turbochat.gptprompts import *


from pathlib import Path


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
        print("HERE!!!", history_config)
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
        if not isinstance(updated_history, pd.DataFrame): raise TypeError("required type dataframe")
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
        tdf = tdf.apply(lambda x: f"{x.name} :" + x)
        history['index_context'] = tdf.apply(lambda x: " | ".join(x.tolist()), axis=1)
        return self.encode(history['index_context'].values.tolist())

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


class DocumentKeyValuePairExtraction:

    
    __tool_definition = tool_definition = {

        "type": "function",

        "function": {

            "name": "collect_data_about_customer_report_health_from_medical_documents",

            "description": """
                Collects information about the client, medical document and health indicators Iff the prompt mentions that the following data from customer's medical document.
                Information collected will describe the client, clients's health parameters, about the medical document and it's purpose.
                Any information which is not related to the client is to be strictly not collected.
            """,
            
            "parameters": {

                "type": "object",
            
                "properties": {
                    
                    "entries": {
                        
                        "type": "array",
                        
                        "description": "list of object's containing information collected in specified format",

                        "items": {
                            "type": "object",
                            
                            "properties": {
                                
                                "parameter_label": {
                                    "type": "string",
                                    "description": """
                                        parameter label that will describe the medical document, client and client's health, which can be assigned to parameter value.
                                        Example: BMI, weight, height, heart rate, stress level, age, reported date, collected date, address, phone, report status, cholestrol, street, fax etc
                                        Note: It should not contain the values the information but rather very short (1-3 word if possible) discription of the parameter value.
                                    """
                                },
                                
                                "parameter_type": {
                                    "type": "string",
                                    "description": """
                                        type of parameter that was collected
                                        Example: client info, health, about medical document, etc
                                    """
                                },
                                
                                "parameter_value": {
                                    "type": "string",
                                    "description": """
                                        value of the collected parameter
                                        Example: 127cm, 40Kg, High, Low, Irregular, balanced, 163 mg/dL, 4.1, 0.37 mIU/L, 10 kg, Male, Yes, 02/01/2024 etc.
                                    """
                                },
                                
                            },
                            "required": [
                                "parameter_label",
                                "parameter_type",
                                "parameter_value",
                            ],
                        }
                    }
                },
            },

            "required": ["entries"],
        }

    }


    def __init__(self, document_bytes=None):
        
        self.__connect_to_gpt()
        self.pdf = self.__try_loading_pdf(document_bytes)


    def __connect_to_gpt(self):

        with open("openai_key", "r") as f:
            # Read first line
            api_key = f.read().strip()
        
        self.gpt_client = OpenAI(api_key=api_key)


    def __try_loading_pdf(self, pdf_bytes):
        
        pdf = io.BytesIO()
        pdf.write(pdf_bytes)
        pdf.seek(0)

        return fitz.open(stream=pdf)
    

    def __get_text(self):
        page_text = []
        for page in self.pdf.pages():
            page_text.append(page.get_text())
        return page_text

    
    # very specific callable
    @staticmethod
    def __tool_callable(entries):
        # collect_data_about_customer_report_health_from_medical_documents

        try: entries = pd.DataFrame(entries, columns=["parameter_label", "parameter_type", "parameter_value"])
        except Exception: return pd.DataFrame(columns=["parameter_label", "parameter_type", "parameter_value"])
        
        return entries
    
    
    def get_tool(self):

        return Tools([
            {
                "name": "collect_data_about_customer_report_health_from_medical_documents",
                "function": self.__tool_callable,
                "definition": self.__tool_definition
            }
        ])

    
    def extract(self):
        tools = self.get_tool()
        
        responses = []
        for text in self.__get_text():

            append_message = f"This information is from the user's medical document\n"
            text = append_message + text

            response = self.gpt_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=Messages([User(text)]).get_entries(),
                tools=tools.get_tools(),
                tool_choice="auto"
            )
            responses.append(response)

        if not responses:
            return responses

        stash = {}
        for response in responses:
            stash = tools.get_results(response, stash)

        return responses, stash
        

    def get_results(self, stash):

        if not stash:
            return pd.DataFrame(columns=['parameter_label', 'parameter_type', 'parameter_value'])

        for key, value in stash.items():
            stash_entries = pd.concat(stash[key])
            df = pd.DataFrame(stash_entries if stash[key] else [])
            df['parameter_label'] = df['parameter_label'].str.strip().str.lower()
            df['parameter_type'] = df['parameter_type'].str.strip().str.lower()
            df['parameter_value'] = df['parameter_value'].str.strip().str.lower()
            df = df.sort_values('parameter_type').reset_index(drop=True)
            df = df.drop_duplicates(["parameter_label"])

        return df

