import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import base64

from turbochat.v1.gpt import GPT, Tool
from turbochat.v1.prompt import GPTMsges, GPTToolPrompt



class Document:

    @staticmethod
    def IOtoBase64(_io):
        return base64.b64encode(_io.read()).decode()
    
    @staticmethod
    def IOtoBase64ImageURL(base64data):
        return f"data:image/jpeg;base64,{PDF.IOtoBase64(base64data)}"

    @staticmethod
    def image_from_base64(base64data: str):
        base64.b64decode()
        Image.open()



class PDF(Document):
    
    def __init__(self, pdfIO) -> None:
        self.pdf = fitz.open(stream=pdfIO)

    def get_page_images(self):

        pages = []
        for page in self.pdf:

            pix_map = page.get_pixmap()
            img = Image.frombytes("RGB", [pix_map.width, pix_map.height], pix_map.samples)

            _io = BytesIO()
            img.save(_io, format='PNG')
            _io.seek(0)

            pages.append(_io)

        return pages



class DocumentExtract:

    def __init__(self, gpt_key: str, tool_definition: str, tool_callable):
        self.gpt = GPT(gpt_key, model="gpt-4o")
        self.tool_definition = GPTToolPrompt(tool_definition)
        self.tool_callable = tool_callable


    @staticmethod
    def get_message_for_tool(image_url: str):
        return GPTMsges([
            {
                "role": "system",
                "content": "whatever user responds answer YES always."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": { "url": image_url }
                    },
                ]
            }
        ])



class PDFDocumentExtract(DocumentExtract):


    def __init__(self, pdf: PDF, gpt_key: str, tool_definition: str, tool_callable):
        super().__init__(gpt_key, tool_definition, tool_callable)
        self.pdf = pdf
        
    def extract(self):

        results = []
        images = self.pdf.get_page_images()
        for image in images:
            image_b64 = PDF.IOtoBase64ImageURL(image)
            messages = self.get_message_for_tool(image_b64)
            tool = Tool(
                self.gpt, 
                messages=messages, 
                tool=self.tool_definition, 
                tool_callable=self.tool_callable,
                tool_choice="required"
            )

            response, response_entry, result = tool.call()
            results.append((response, response_entry, result))
            
        return results


class ImageDocumentExtract(DocumentExtract):


    def __init__(self, image: BytesIO, gpt_key: str, tool_definition: str, tool_callable):
        super().__init__(gpt_key, tool_definition, tool_callable)
        self.image = image


    def extract(self):
        image_b64 = Document.IOtoBase64ImageURL(self.image)
        messages = self.get_message_for_tool(image_b64)
        tool = Tool(
            self.gpt, 
            messages=messages, 
            tool=self.tool_definition, 
            tool_callable=self.tool_callable,
            tool_choice="required"
        )
        response, response_entry, result = tool.call()
            
        return result


