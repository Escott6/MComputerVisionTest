from django.http import HttpResponse
from django.views.generic import View

import time
from array import array
import re 
import fitz
from .cognitive_services_helper import check_redacted
from django.shortcuts import render

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from .models import Redactor


from django.conf import settings

M_VISION_KEY = getattr(settings, "M_VISION_KEY")
M_VISION_ENDPOINT = getattr(settings,"M_VISION_ENDPOINT")
redactedLines = ["phrases to redact", "test phrase2", "Yukon", "lazy", "computer", "canada", "website"]


class HomeView(View):
    template_name = 'fileredaction/home.html'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["file_type"] = 'pdf' 
        return context


def pdf_view(request):
    path = "fileredaction/static/fileredaction/sample.docx"
    redactor = Redactor(path)
    redactor.redaction()
    return render(request, "pdf.html")


def home(request):
    
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
                for phrase in redactedLines:
                    var = var.replace(phrase, "-"*len(phrase))
                print(var)
                new_text += var + " "
                print(line.bounding_box)
    print()

    return HttpResponse("Original text: " + original_text + " \n New Text: " + new_text)
