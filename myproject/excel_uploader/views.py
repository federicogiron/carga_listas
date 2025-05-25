from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required # For restricting access to logged-in users
from .forms import ExcelUploadForm # The form for file upload
from django.contrib import messages # For displaying feedback to the user
from .excel_processing import process_excel_file # The function to validate and clean Excel data
from .db_utils import insert_data_into_sql_server # The function to insert data into the database

@login_required
def upload_excel_view(request):
    """
    Handles the Excel file upload, processing, and database insertion.

    - If GET request: Displays the empty upload form.
    - If POST request:
        - Validates the submitted form and file.
        - Checks for the correct file extension (.xlsx).
        - Calls `process_excel_file` to validate headers and data types, and clean data.
        - If processing errors occur, they are displayed to the user.
        - If data is valid, it maps the 'VentasQ(28d)' column to 'VentasQ_28d' for SQL compatibility.
        - Calls `insert_data_into_sql_server` to load the data into the specified table.
        - Displays success or error messages from the database operation.
        - Redirects to the same view on successful upload to clear the form, or re-renders
          the form with error messages if any step fails.
    """
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            # File type validation: Ensure it's an .xlsx file
            if not uploaded_file.name.endswith('.xlsx'):
                messages.error(request, "Invalid file type. Only .xlsx files are allowed.")
                # Form will be re-rendered below with this message
            else:
                # Process the uploaded Excel file
                cleaned_data, processing_errors = process_excel_file(uploaded_file)

                if processing_errors:
                    # If there are errors from excel_processing, display them
                    for error in processing_errors:
                        messages.error(request, error)
                    # Form will be re-rendered below with these messages
                
                elif cleaned_data:
                    # Data mapping: Adjust column name for SQL compatibility
                    # The Excel file has 'VentasQ(28d)', SQL table expects 'VentasQ_28d'
                    for row in cleaned_data:
                        if 'VentasQ(28d)' in row: # Check if the key exists to avoid KeyError
                            row['VentasQ_28d'] = row.pop('VentasQ(28d)')
                    
                    # Database insertion
                    # IMPORTANT: 'YourTargetTableName' is a placeholder.
                    # This should be replaced with the actual target table name in the SQL Server database.
                    # Consider making this configurable via settings.py in a future enhancement.
                    table_name = 'YourTargetTableName' 
                    db_error = insert_data_into_sql_server(cleaned_data, table_name)

                    if db_error:
                        # If database insertion fails, display the error
                        messages.error(request, db_error)
                        # Form will be re-rendered below with this message
                    else:
                        # Success: Display success message and redirect to clear the form
                        messages.success(request, f"Successfully processed '{uploaded_file.name}' and loaded data into {table_name}.")
                        return redirect('excel_uploader:upload_excel') 
                else:
                    # Fallback error if processing results in no data and no specific errors
                    # This case should ideally be covered by `processing_errors`,
                    # but it's a safeguard.
                    messages.error(request, "An unknown error occurred during file processing.")
                    # Form will be re-rendered below with this message
    else: 
        # GET request: Display an empty form
        form = ExcelUploadForm()
    
    # Render the upload form template with the form instance and any messages
    return render(request, 'excel_uploader/upload_form.html', {'form': form})
