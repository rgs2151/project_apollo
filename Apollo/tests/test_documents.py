from unittest import TestCase

from pathlib import Path
import sys

__PATH__ = Path("..").absolute().resolve()
print("ADDING TO PATH:", str(__PATH__), " exists: ", Path(__PATH__).exists())
sys.path.append(str(__PATH__))


from Conversation.converse.documents import PDF, DocumentExtract
from Conversation.converse.tools import  EXTRACT_USER_RELATED_INFO, extract_user_health_information_entry
from io import BytesIO


class TestDocuments(TestCase):


    def setUp(self):
        sample_pdf = r"C:\Users\nagen\Desktop\gpt\sample.pdf"
        with open(sample_pdf, 'rb') as f:
            self.pdf_bytes = f.read()


    def test_documents(self):
        _io = BytesIO(self.pdf_bytes)
        _io.seek(0)
        pdf = PDF(_io)

        images = pdf.get_page_images()

        PDF.IOtoBase64ImageURL(images[0])[:50]


    def test_document_extract(self):
        _io = BytesIO(self.pdf_bytes)
        _io.seek(0)
        pdf = PDF(_io)

        # docextract = DocumentExtract(pdf, EXTRACT_USER_RELATED_INFO, extract_user_health_information_entry)
        # result = docextract.extract()
        




