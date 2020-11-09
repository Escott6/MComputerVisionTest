import fitz 
import re 
from docx import Document
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

class Redactor: 
    
    # static methods work independent of class object 
    @staticmethod
    def get_sensitive_data(lines): 
        
        """ Function to get all the lines """
          
        redactedLines = ["phrases to redact", "test phrase2", "Yukon", "lazy", "computer", "canada", "website"]
        redacted_lines = '|'.join(redactedLines)

        for line in lines: 
            
            # matching the regex to each line 
            if re.search(redacted_lines, line, re.IGNORECASE): 
                search = re.search(redacted_lines, line, re.IGNORECASE) 
                  
                # This is probably the problem
                yield search.group(1) 
  
    # constructor 
    def __init__(self, path): 
        self.path = path 
  
    def redaction(self): 
        extension = self.path.split(".")[-1]
        # For docx
        # TODO removes formatting for any area it redacts things for and doesn't redact from tables
        if extension == "docx":
            redacted_lines = ["phrases to redact", "test phrase2", "Yukon", "lazy", "computer", "canada", "website"]
            doc = Document(self.path)
            
            for line in doc.paragraphs:
                for phrase in redacted_lines:
                    if line.text.find(phrase) >=0:
                        inline = line.runs
                        for i in range(len(inline)):
                            text = inline[i].text.replace(phrase,"-"*len(phrase))
                            inline[i].text = text
#                            line.text = line.text.replace(phrase, "-"*len(phrase))
                        

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

                # geting the rect boxes which consists the matching email regex 
                sensitive = self.get_sensitive_data(page.getText("text") 
                                                    .split('\n')) 
                for data in sensitive: 
                    areas = page.searchFor(data) 

                    # drawing outline over sensitive datas 
                    [page.addRedactAnnot(area, fill = (0, 0, 0)) for area in areas] 

                # applying the redaction 
                page.apply_redactions() 

            # saving it to a new pdf 
            doc.save('redacted7.pdf') 
        
        # For images
        elif extension == "jpg" | extension == "png" | extension == "jpeg":

            computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
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
                        for phrase in redactedLines:
                            var = var.replace(phrase, "-"*len(phrase))
                        print(var)
                        new_text += var + " "
                        print(line.bounding_box)