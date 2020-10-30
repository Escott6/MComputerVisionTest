from django.http import HttpResponse
from .cognitive_services_helper import check_redacted
import time
import sys
import os
from array import array

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials


subscription_key = 'e1bf09dca0de4192a2aceaff80e4f380'
endpoint = 'https://stagingcomputervision.cognitiveservices.azure.com/'
redactedLines = ["phrases to redact", "test phrase2", "Expo Marker", "lazy"]



def home(request):
    
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
    if get_handw_text_results.status == OperationStatusCodes.succeeded:
        for text_result in get_handw_text_results.analyze_result.read_results:
            for line in text_result.lines:
                print(str(type(line))+ '\n')
                var = line.text
                print(var + '\n')
                for phrase in redactedLines:
                    var = var.replace(phrase, "---")
                print(var)
                print(line.bounding_box)
    print()

    return HttpResponse("Hello")