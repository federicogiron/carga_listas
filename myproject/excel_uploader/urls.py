from django.urls import path
from . import views # Import views from the current application

# Application namespace for URL reversing (e.g., {% url 'excel_uploader:upload_excel' %})
app_name = 'excel_uploader'

# Defines the URL patterns for the excel_uploader app.
urlpatterns = [
    # Maps the root path of this app (e.g., /uploader/) to the upload_excel_view.
    # - The empty string '' denotes the base URL for this app.
    # - views.upload_excel_view is the view function that will handle requests to this URL.
    # - name='upload_excel' provides a convenient way to refer to this URL pattern in templates and views.
    path('', views.upload_excel_view, name='upload_excel'),
]
