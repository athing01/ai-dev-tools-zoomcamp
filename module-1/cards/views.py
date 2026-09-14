from django.shortcuts import render

from .forms import BusinessCardForm


def home(request):
    form = BusinessCardForm(request.POST or None, request.FILES or None)
    submission_valid = request.method == 'POST' and form.is_valid()

    return render(
        request,
        'cards/home.html',
        {
            'form': form,
            'submission_valid': submission_valid,
        },
    )
