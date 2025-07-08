from django.shortcuts import render

def test_websocket_view(request):
    return render(request, 'test.html')
