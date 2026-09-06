from django.http import HttpResponse


def home(request):
    return HttpResponse('e-Business Card Generator')
