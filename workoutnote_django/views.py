from django.shortcuts import render


def handle_index(request):
    return render(request=request, template_name='index.html')
