""" Allows for the redaction of words or phrases from a variety of file formats """
__author__ = "Evan Scott"
__email__  = "escott1367@gmail.com"
__status__ = "Prototype"

import fitz 
import re
import copy
import np
import cv2 
from PIL import Image, ImageDraw
from io import BytesIO
import requests
from django.conf import settings
import time 

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml.shared import OxmlElement
from docx.text.run import Run
import docx.dml.color
from pptx import Presentation

M_VISION_KEY = getattr(settings, "M_VISION_KEY")
M_VISION_ENDPOINT = getattr(settings,"M_VISION_ENDPOINT")

class Redactor: 
    
    # constructor 
    def __init__(self, path): 
        self.path = path

    # uses the xml for the highlighting
    def set_hightlight_xml(self, run):
        rpr = run._r.get_or_add_rPr()
        highlight = OxmlElement("a:highlight")
        srgbClr = OxmlElement("a:srgbClr")
        setattr(srgbClr, "val", WD_COLOR_INDEX.BLACK)
        highlight.append(srgbClr)
        rpr.append(highlight)
        return run         

    def add_run_styles(self, new_run, old_run):
        new_run.style = old_run.style
        new_run.bold = old_run.bold
        new_run.italic = old_run.italic
        new_run.underline = old_run.underline
        new_run.font.all_caps = old_run.font.all_caps
        color = new_run.font.color
        color.rgb = old_run.font.color.rgb
        new_run.font.complex_script = old_run.font.complex_script
        new_run.font.double_strike = old_run.font.double_strike
        new_run.font.emboss = old_run.font.emboss
        new_run.font.highlight_color = old_run.font.highlight_color
        new_run.font.imprint = old_run.font.imprint 
        new_run.font.math = old_run.font.math
        new_run.font.name = old_run.font.name
        new_run.font.outline = old_run.font.outline
        new_run.font.shadow = old_run.font.shadow
        new_run.font.size = old_run.font.size
        new_run.font.small_caps = old_run.font.small_caps
        new_run.font.snap_to_grid = old_run.font.snap_to_grid
        new_run.font.strike = old_run.font.strike
        new_run.font.subscript = old_run.font.subscript
        new_run.font.superscript = old_run.font.superscript
        return new_run


    def paragraph_rewrite(self, paragraph, phrase):
        #test
        pass;



    def redaction(self): 
        redacted_lines = ["powerpoint","ipsum", "phrases to redact", "over", "test phrase2", "jumps", "Yukon", "lazy", "computer", "canada", "website"]
        extension = self.path.split(".")[-1]
        # For docx
        if extension == "docx":
            doc = Document(self.path)
            # Clear one paragraph at a time 
            for paragraph in doc.paragraphs:
                lines = paragraph.runs
                for phrase in redacted_lines:
                    if phrase in paragraph.text: # There is something to redact
                        curr_runs = copy.copy(lines)    # copy the paragraph and clear it 
                        paragraph.clear()
                        for i in range(len(curr_runs)): # Find which run contains the phrase
                            if phrase in curr_runs[i].text: # The phrase to redact is in this run 
                                # Replace the word with the dash_word to redact the phrase
                                dash_word = "#"*len(phrase)
                                text = curr_runs[i].text.replace(phrase, dash_word)
                                curr_runs[i].text = text
                                # Split by the dash_word to add highlighting 
                                words = re.split('(#+)', curr_runs[i].text)
                                text_string = ""
                                #Search for the redacted word in the run 
                                for word in words:
                                    # if the word is the redacted word create new run and black it out 
                                    if word == dash_word:
                                        # if the new_run has words attached to it add it to the paragraph and create a new 
                                        # run for the redacted word
                                        if text_string != "":
                                            new_run = paragraph.add_run(text_string)
                                            new_run = self.add_run_styles(new_run, curr_runs[i])
                                        # If it is a fresh_run just create a new run containing only the redacted word and add it
                                        text_string = ""
                                        new_run = paragraph.add_run(dash_word)
                                        new_run = self.add_run_styles(new_run, curr_runs[i])
                                        new_run.font.highlight_color = WD_COLOR_INDEX.BLACK
                                    # else just add the word to the existing text
                                    else:
                                        text_string += word
                                # Deals with the remainder of the run after the phrase has been found
                                if text_string != "":
                                    new_run = paragraph.add_run(text_string)
                                    new_run = self.add_run_styles(new_run, curr_runs[i])
                            else:
                                #Append the run as there is nothing to change
                                #TODO cannot recognize the highlight color of the doc might need to go into lxml
                                new_run = paragraph.add_run(curr_runs[i].text)
                                new_run = self.add_run_styles(new_run, curr_runs[i])

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
        
        # For images you need to feed it single words not phrases or it will not work
        # invert the image and dilate it, merges the letters a bit then use contours to find each word separately
        elif extension == "jpg" or extension == "png" or extension == "jpeg":

            computervision_client = ComputerVisionClient(M_VISION_ENDPOINT, CognitiveServicesCredentials(M_VISION_KEY))
            recognize_handw_results = computervision_client.read(self.path,  raw=True)

            # Get the operation location (URL with an ID at the end) from the response
            operation_location_remote = recognize_handw_results.headers["Operation-Location"]
            # Grab the ID from the URL
            operation_id = operation_location_remote.split("/")[-1]
            response = requests.get(self.path)
            im = Image.open(BytesIO(response.content))

            while True:
                get_handw_text_results = computervision_client.get_read_result(operation_id)
                if get_handw_text_results.status not in ['notStarted', 'running']:
                    break
                time.sleep(1)

            # Print the detected text, line by line
            if get_handw_text_results.status == OperationStatusCodes.succeeded:
                for text_result in get_handw_text_results.analyze_result.read_results:
                    for line in text_result.lines:
                        for word in line.words:
                            for phrase in redacted_lines:
                                if phrase == word.text:
                                    loc = word.bounding_box
                                    # 
                                    draw = ImageDraw.Draw(im)
                                    # [x0,y0,x1,y1] or [(x0,y0), (x1,y1)] format
                                    #draw.rectangle([(loc[0], loc[1]), (loc[4], loc[5])], fill=(0,0,0))
                                    draw.polygon([(loc[0],loc[1]),(loc[2],loc[3]),(loc[4],loc[5]),(loc[6],loc[7])] ,fill=(0,0,0))
                save_loc = 'redactedpoly.' + extension
                im.save(save_loc)

            # For powerpoints 
        elif extension == "pptx" or extension == "ppt":
            presentation =  Presentation(self.path)
            for slide in presentation.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        for phrase in redacted_lines:
                            if (phrase in shape.text):
                                text_frame = shape.text_frame
                                for paragraph in text_frame.paragraphs:
                                    whole_text = "".join(run.text for run in paragraph.runs)
                                    whole_text = whole_text.replace(phrase,"-"*len(phrase))
                                    for idx, run in enumerate(paragraph.runs):
                                        if idx != 0:
                                            p = paragraph._p
                                            p.remove(run._r)
                                    if(not(not paragraph.runs)):
                                        paragraph.runs[0].text = whole_text
            presentation.save('redacted-powerpoint.pptx')

        elif extension == "txt":
            with open(self.path, "r+") as txt_file:
                for line in txt_file.readlines():
                    for phrase in redacted_lines:
                        if phrase in txt_file:
                            line.replace(phrase,"-"*len(phrase))
