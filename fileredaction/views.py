from django.shortcuts import render

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from .models import Redactor


from django.conf import settings

M_VISION_KEY = getattr(settings, "M_VISION_KEY")
M_VISION_ENDPOINT = getattr(settings,"M_VISION_ENDPOINT")
redactedLines = ["phrases to redact", "software", "slide","test phrase2", "Yukon", "lazy", "computer", "canada", "website"]

def home(request):
    query = request.GET.get('search_res', None)
    context = {}
    if query and request.method == 'GET':
        redactor = Redactor(query)
        results = redactor.redaction()
        context.update({'results':results})
    return render(request,'home.html', context)
