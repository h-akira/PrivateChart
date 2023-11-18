from django.shortcuts import render

def index(request):
  context = None
  return render(request,'home/index.html',context)
