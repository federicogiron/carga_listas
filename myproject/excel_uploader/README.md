# Excel Uploader App for Django

This Django app provides functionality to upload Excel files (.xlsx), validate their content against a predefined template, and load the data into a SQL Server database.

## Features

- File upload interface.
- Validation of Excel file structure (headers) and data types.
- Data cleaning and transformation.
- Direct loading of data into a SQL Server database.
- User feedback via Django messages framework.

## Setup and Configuration

1.  **Dependencies**:
    Ensure you have the following packages installed. You can install them using pip:
    ```bash
    pip install pandas openpyxl pyodbc Django
    ```
    (Django is assumed to be part of your project already).

2.  **Add to `INSTALLED_APPS`**:
    In your project's `settings.py`, add `excel_uploader` to the `INSTALLED_APPS` list:
    ```python
    INSTALLED_APPS = [
        # ... other apps
        'excel_uploader',
    ]
    ```

3.  **Database Configuration (`settings.py`)**:
    Add your SQL Server connection details to your project's `settings.py`. **For production, always use environment variables or a secure secrets management system for sensitive credentials.**
    ```python
    AUTH_DB_MSSQL = {
        "DB_HOST": "your_sql_server_host",  # e.g., "10.255.1.152"
        "DB_USER": "your_db_user",        # e.g., "fgiron.GDN"
        "DB_PASSWORD": "your_db_password",  # e.g., "$$$Dorinka15$$$"
        "DB_NAME": "your_db_name",          # e.g., "marketing"
    }
    ```
    The connection string in `db_utils.py` uses `ODBC Driver 17 for SQL Server`. Ensure this driver (or an appropriate one for your system) is installed and accessible. It also includes `TrustServerCertificate=yes;` which may be suitable for development but should be reviewed for production security.

4.  **Target Table Name**:
    In `myproject/excel_uploader/views.py`, inside the `upload_excel_view` function, find the line:
    `table_name = 'YourTargetTableName'`
    Change `'YourTargetTableName'` to the actual name of the table in your SQL Server database where the data should be inserted.
    *Consider moving this to `settings.py` for better configurability in the future.*

5.  **Include App URLs**:
    In your project's main `urls.py`, include the `excel_uploader` URLs:
    ```python
    from django.urls import path, include

    urlpatterns = [
        # ... other urls
        path('uploader/', include('excel_uploader.urls')),
    ]
    ```

## Excel File Template

The uploaded Excel file (.xlsx) must adhere to the following structure:

- **Headers (must be exact and in order)**:
  `FECHA`, `TIENDA`, `SKU`, `DESCRIPCION_GDN`, `EAN`, `PRECIO_REGULAR_GDN`, `PRECIO_OFERTA_GDN`, `DESCUENTO_PROMEDIO`, `VentasQ(28d)`

- **Data Types**:
    - `FECHA`: Date (YYYY-MM-DD)
    - `TIENDA`: Integer
    - `SKU`: Integer
    - `DESCRIPCION_GDN`: String (max 255 chars)
    - `EAN`: Integer
    - `PRECIO_REGULAR_GDN`: Decimal (e.g., 123.45)
    - `PRECIO_OFERTA_GDN`: Decimal (e.g., 100.00, optional)
    - `DESCUENTO_PROMEDIO`: Decimal (e.g., 0.1500)
    - `VentasQ(28d)`: Integer

**Note on SQL Column Name**: The Excel column `VentasQ(28d)` is mapped to a SQL column named `VentasQ_28d` in the database insertion logic due to SQL naming conventions. Ensure your database table uses `VentasQ_28d`.

## How to Use

1.  Run the Django development server: `python manage.py runserver`
2.  Navigate to `http://localhost:8000/uploader/` in your web browser.
3.  Select an Excel file matching the template and click "Upload and Process File".
4.  Feedback (success or errors) will be displayed on the page.
```
