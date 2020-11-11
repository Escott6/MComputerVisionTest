import fitz 
import re 
from docx import Document
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from django.conf import settings
from docx.enum.text import WD_COLOR_INDEX
import copy

M_VISION_KEY = getattr(settings, "M_VISION_KEY")
M_VISION_ENDPOINT = getattr(settings,"M_VISION_ENDPOINT")

class Redactor: 
    
    # constructor 
    def __init__(self, path): 
        self.path = path


    def add_run_styles(self, new_run, old_run):
        new_run.style = old_run.style
        new_run.bold = old_run.bold
        new_run.italic = old_run.italic
        new_run.underline = old_run.underline
        new_run.font.name = old_run.font.name
        new_run.font.size = old_run.font.size
        return new_run
  
    def redaction(self): 

        redacted_lines = ["phrases to redact", "test phrase2", "Yukon", "lazy", "computer", "canada", "website"]
        extension = self.path.split(".")[-1]
        # For docx
        if extension == "docx":
            doc = Document(self.path)
            
            for paragraph in doc.paragraphs:
                for phrase in redacted_lines:
                    if phrase in paragraph.text: # There is something to redact
                        
                        lines = paragraph.runs
                        curr_runs = copy.copy(lines)
                        paragraph.clear()

                        for i in range(len(curr_runs)):

                            if phrase in curr_runs[i].text: # The phrase to redact is in this run 
                                text = curr_runs[i].text.replace(phrase,"-"*len(phrase))
                                curr_runs[i].text = text
                                words = re.split('(\W)', lines[i].text)

                                new_run = paragraph.add_run("")
                                
                                for word in words:

                                    if word == "-"*len(phrase):
                                        if new_run.text != "":
                                            new_run = self.add_run_styles(new_run, curr_runs[i])
                                            paragraph.runs.append(new_run)
                                        new_run = paragraph.add_run("-"*len(phrase))
                                        new_run.font.highlight_color = WD_COLOR_INDEX.BLACK
                                        new_run = self.add_run_styles(new_run, curr_runs[i])
                                        paragraph.runs.append(new_run)
                                        new_run = paragraph.add_run()
                                    else:
                                        new_run.text += word
                                        
                                if new_run != "":
                                    new_run = self.add_run_styles(new_run, curr_runs[i])
                                    paragraph.runs.append(new_run)
                            else:
                                paragraph.runs.append(curr_runs[i])
# TODO fix tables
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