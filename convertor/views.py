# views.py

from django.shortcuts import render, redirect
from .forms import ReceiptFileForm
from .models import ReceiptFile

BACKEND_URL = 'http://16.170.243.1:8001/media/'

def upload_receipt_file(request):
    if request.method == 'POST':
        print(request.POST)
        form = ReceiptFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # You can perform additional actions here if needed
            receipt_files = ReceiptFile.objects.all().order_by('-uploaded_at')
            request.FILES.clear()
            return render(request, 'convert.html', {'form': form, 'receipt_files': receipt_files, "url": BACKEND_URL})
    else:
        form = ReceiptFileForm()
    receipt_files = ReceiptFile.objects.all()
    return render(request, 'convert.html', {'form': form, 'receipt_files': receipt_files, "url": BACKEND_URL})

def success_page(request):
    receipt_files = ReceiptFile.objects.all()
    return render(request, 'success_page.html', {'receipt_files': receipt_files})



