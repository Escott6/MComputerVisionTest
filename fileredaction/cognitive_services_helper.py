#Cognitive_Services_Helper.py

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

import time
import re


# Might want to replace search with findall
def check_redacted(line, redacted_lines):
    for phrase in line:
        #if re.search(redacted_lines, phrase, re.IGNORECASE):
        search = re.search(redacted_lines, phrase, re.IGNORECASE)
        if search:
            yield search.group(0)
