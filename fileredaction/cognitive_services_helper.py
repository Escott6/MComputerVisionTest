#Cognitive_Services_Helper.py

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

import time
from re import search


def check_redacted(line):
    for phrase in redactedLines:
        line.replace(phrase, "---")
        
    
    return line 


