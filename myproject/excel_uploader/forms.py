from django import forms

class ExcelUploadForm(forms.Form):
    """
    A Django Form for handling the upload of Excel files.
    It includes a single FileField to accept .xlsx files.
    """
    file = forms.FileField(
        label='Excel File (.xlsx)', 
        help_text='Upload an Excel file with the .xlsx extension.'
    )
