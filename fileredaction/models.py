import fitz 
import re 
from docx import Document
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from django.conf import settings

M_VISION_KEY = getattr(settings, "M_VISION_KEY")
M_VISION_ENDPOINT = getattr(settings,"M_VISION_ENDPOINT")

class Redactor: 
    
    # constructor 
    def __init__(self, path): 
        self.path = path 
  
    def redaction(self): 

        redacted_lines = ["phrases to redact", "test phrase2", "Yukon", "lazy", "computer", "canada", "website"]
        extension = self.path.split(".")[-1]
        # For docx
        if extension == "docx":
            doc = Document(self.path)
            
            for line in doc.paragraphs:
                for phrase in redacted_lines:
                    if line.text.find(phrase) >=0:
                        inline = line.runs
                        for i in range(len(inline)):
                            text = inline[i].text.replace(phrase,"-"*len(phrase))
                            inline[i].text = text
                        

#            for table in doc.tables:
#                for row in table.rows:
#                    for cell in row.cells:

            doc.save('./redacted.docx')

        # For pdfs
        elif extension == "pdf":

            # opening the pdf 
            doc = fitz.open(self.path) 

            # iterating through pages 
            for page in doc: 

                # _wrapContents is needed for fixing alignment issues with rect boxes 
                page._wrapContents() 
                                    
                for phrase in redacted_lines: 
                    areas = page.searchFor(phrase) 

                    for area in areas:
                        
                        anot = page.addRedactAnnot(area, fill = (0,0,0))
                        r = anot.rect
                        r.y1 = r.y0 + r.height * .9
                        r.y0 = r.y1 - r.height * .9
                        anot.setRect(r)
                        anot.update()

                # applying the redaction 
                page.apply_redactions() 

            # saving it to a new pdf 
            doc.save('redacted17.pdf') 
        
        # For images
        elif extension == "jpg" | extension == "png" | extension == "jpeg":

            computervision_client = ComputerVisionClient(M_VISION_ENDPOINT, CognitiveServicesCredentials(M_VISION_KEY))
            remote_image_handw_text_url = "https://raw.githubusercontent.com/MicrosoftDocs/azure-docs/master/articles/cognitive-services/Computer-vision/Images/readsample.jpg"
            recognize_handw_results = computervision_client.read(remote_image_handw_text_url,  raw=True)

            # Get the operation location (URL with an ID at the end) from the response
            operation_location_remote = recognize_handw_results.headers["Operation-Location"]
            # Grab the ID from the URL
            operation_id = operation_location_remote.split("/")[-1]

            while True:
                get_handw_text_results = computervision_client.get_read_result(operation_id)
                if get_handw_text_results.status not in ['notStarted', 'running']:
                    break
                time.sleep(1)

            # Print the detected text, line by line
            original_text = ""
            new_text = ""
            if get_handw_text_results.status == OperationStatusCodes.succeeded:
                for text_result in get_handw_text_results.analyze_result.read_results:
                    for line in text_result.lines:

                        var = line.text

                        print(var + '\n')
                        original_text += var + " "
                        for phrase in redacted_lines:
                            var = var.replace(phrase, "-"*len(phrase))
                        print(var)
                        new_text += var + " "
                        print(line.bounding_box)