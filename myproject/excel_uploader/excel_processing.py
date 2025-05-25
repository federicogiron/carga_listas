import pandas as pd
from io import BytesIO # To handle the uploaded file object, especially from Django's InMemoryUploadedFile

def process_excel_file(uploaded_file_object):
    """
    Processes an uploaded Excel file (.xlsx) to validate its structure, headers, and data types.

    Args:
        uploaded_file_object: An InMemoryUploadedFile or TemporaryUploadedFile object from Django.
                              The file is expected to be an Excel file (.xlsx).

    Returns:
        tuple: (cleaned_data, errors)
            - cleaned_data (list of dicts or None): A list of dictionaries, where each dictionary
              represents a row from the Excel file with cleaned and validated data.
              Returns None if critical errors occur (e.g., header mismatch, file read error).
            - errors (list of str): A list of error messages detailing validation failures.
              Empty if no errors.
    """
    errors = []
    cleaned_data = None
    # Define the expected headers in the exact order.
    expected_headers = [
        'FECHA', 'TIENDA', 'SKU', 'DESCRIPCION_GDN', 'EAN',
        'PRECIO_REGULAR_GDN', 'PRECIO_OFERTA_GDN',
        'DESCUENTO_PROMEDIO', 'VentasQ(28d)'
    ]

    try:
        # Attempt to read the Excel file using pandas.
        # uploaded_file_object.seek(0) is important to reset the stream's cursor,
        # in case the file has been read previously (e.g., by Django's upload handlers).
        try:
            uploaded_file_object.seek(0) 
            df = pd.read_excel(uploaded_file_object, engine='openpyxl')
        except Exception as e:
            # Catch errors during file reading (e.g., corrupted file, not a valid Excel format).
            errors.append(f"Error reading Excel file: It might be corrupted or not a valid .xlsx file. (Details: {e})")
            return None, errors # Critical error, cannot proceed.

        # 1. Header Validation: Check if the actual headers match the expected ones.
        if not list(df.columns) == expected_headers:
            errors.append(f"Invalid headers. Expected: {expected_headers}. Got: {list(df.columns)}")
            return None, errors # Critical error, data cannot be reliably processed.

        # Create a copy of the DataFrame for processing to avoid SettingWithCopyWarning.
        processed_df = df.copy()

        # 2. Data Validation and Cleaning for each column.
        # Row numbers in error messages are i+2 (i is 0-indexed, +1 for header, +1 for 1-indexed rows).

        # FECHA: Expected format YYYY-MM-DD.
        original_fechas = processed_df['FECHA'].copy() # Store original values for error reporting.
        processed_df['FECHA'] = pd.to_datetime(processed_df['FECHA'], errors='coerce')
        for i, val in enumerate(processed_df['FECHA']):
            if pd.isna(val): # pd.NaT (Not a Time) indicates a parsing error.
                errors.append(f"Row {i+2}: FECHA '{original_fechas.iloc[i]}' is not a valid date or not in YYYY-MM-DD format.")
            else:
                # Convert successfully parsed dates to 'YYYY-MM-DD' string format.
                processed_df.loc[i, 'FECHA'] = val.strftime('%Y-%m-%d')

        # TIENDA: Expected integer.
        original_tienda = processed_df['TIENDA'].copy()
        processed_df['TIENDA'] = pd.to_numeric(processed_df['TIENDA'], errors='coerce')
        for i, val in enumerate(processed_df['TIENDA']):
            if pd.isna(val): # NaN indicates a conversion error.
                 errors.append(f"Row {i+2}: TIENDA '{original_tienda.iloc[i]}' must be an integer.")
        # Note: pd.to_numeric might convert integers to float (e.g., 1 to 1.0).
        # This is usually fine for database insertion, as DB will handle final type.
        # If strict integer format (no .0) is needed *before* DB, further checks can be added.

        # SKU: Expected integer.
        original_sku = processed_df['SKU'].copy()
        processed_df['SKU'] = pd.to_numeric(processed_df['SKU'], errors='coerce')
        for i, val in enumerate(processed_df['SKU']):
            if pd.isna(val):
                errors.append(f"Row {i+2}: SKU '{original_sku.iloc[i]}' must be an integer.")

        # DESCRIPCION_GDN: Expected string, max 255 characters.
        for i, desc in enumerate(processed_df['DESCRIPCION_GDN']):
            if not isinstance(desc, str):
                if pd.isna(desc): # Handle NaN values.
                    # Option 1: Treat as error
                    errors.append(f"Row {i+2}: DESCRIPCION_GDN must be a string (received empty or non-string).")
                    processed_df.loc[i, 'DESCRIPCION_GDN'] = "" # Replace NaN with empty string for consistency.
                    # Option 2: Allow empty by setting to "" and not adding error (if empty is acceptable)
                    # processed_df.loc[i, 'DESCRIPCION_GDN'] = ""
                else:
                    # Attempt to convert other types (e.g., numbers) to string.
                    processed_df.loc[i, 'DESCRIPCION_GDN'] = str(desc).strip()
            else:
                # Strip whitespace from existing strings.
                processed_df.loc[i, 'DESCRIPCION_GDN'] = desc.strip()
            
            # Check length after potential conversion and stripping.
            if len(processed_df.loc[i, 'DESCRIPCION_GDN']) > 255:
                errors.append(f"Row {i+2}: DESCRIPCION_GDN '{processed_df.loc[i, 'DESCRIPCION_GDN'][:20]}...' exceeds 255 characters.")

        # EAN: Expected integer.
        original_ean = processed_df['EAN'].copy()
        processed_df['EAN'] = pd.to_numeric(processed_df['EAN'], errors='coerce')
        for i, val in enumerate(processed_df['EAN']):
            if pd.isna(val):
                errors.append(f"Row {i+2}: EAN '{original_ean.iloc[i]}' must be an integer.")

        # PRECIO_REGULAR_GDN: Expected decimal number.
        original_prg = processed_df['PRECIO_REGULAR_GDN'].copy()
        processed_df['PRECIO_REGULAR_GDN'] = pd.to_numeric(processed_df['PRECIO_REGULAR_GDN'], errors='coerce')
        for i, val in enumerate(processed_df['PRECIO_REGULAR_GDN']):
            if pd.isna(val):
                errors.append(f"Row {i+2}: PRECIO_REGULAR_GDN '{original_prg.iloc[i]}' must be a decimal number.")
        # Note: Pandas converts numeric columns to float. True decimal type enforcement (e.g., exact two decimal places)
        # is typically best handled at the database level or with Python's `Decimal` type if strictness is needed here.
        # For now, we ensure it's numeric. Rounding can be applied if desired:
        # processed_df['PRECIO_REGULAR_GDN'] = processed_df['PRECIO_REGULAR_GDN'].round(2)

        # PRECIO_OFERTA_GDN: Expected decimal, optional (can be empty/NaN).
        original_pog = processed_df['PRECIO_OFERTA_GDN'].copy()
        processed_df['PRECIO_OFERTA_GDN'] = pd.to_numeric(processed_df['PRECIO_OFERTA_GDN'], errors='coerce')
        # Check for conversion errors only if the original value was not already NaN/empty.
        for i, original_val in enumerate(original_pog):
            # If original was not null/empty but current is NaN, it means conversion failed.
            if not pd.isna(original_val) and original_val != '' and pd.isna(processed_df.loc[i, 'PRECIO_OFERTA_GDN']):
                errors.append(f"Row {i+2}: PRECIO_OFERTA_GDN '{original_val}' is not a valid decimal number.")
        # Replace NaN values with None, which is more suitable for database insertion (SQL NULL).
        processed_df['PRECIO_OFERTA_GDN'] = processed_df['PRECIO_OFERTA_GDN'].where(pd.notnull(processed_df['PRECIO_OFERTA_GDN']), None)
        # Optional rounding:
        # processed_df['PRECIO_OFERTA_GDN'] = processed_df['PRECIO_OFERTA_GDN'].round(2)

        # DESCUENTO_PROMEDIO: Expected decimal number.
        original_dp = processed_df['DESCUENTO_PROMEDIO'].copy()
        processed_df['DESCUENTO_PROMEDIO'] = pd.to_numeric(processed_df['DESCUENTO_PROMEDIO'], errors='coerce')
        for i, val in enumerate(processed_df['DESCUENTO_PROMEDIO']):
            if pd.isna(val):
                 errors.append(f"Row {i+2}: DESCUENTO_PROMEDIO '{original_dp.iloc[i]}' must be a decimal number.")
        # Optional rounding:
        # processed_df['DESCUENTO_PROMEDIO'] = processed_df['DESCUENTO_PROMEDIO'].round(4)

        # VentasQ(28d): Expected integer.
        original_vq = processed_df['VentasQ(28d)'].copy()
        processed_df['VentasQ(28d)'] = pd.to_numeric(processed_df['VentasQ(28d)'], errors='coerce')
        for i, val in enumerate(processed_df['VentasQ(28d)']):
            if pd.isna(val):
                errors.append(f"Row {i+2}: VentasQ(28d) '{original_vq.iloc[i]}' must be an integer.")

        # If there are any errors collected during validation, do not return cleaned data.
        if not errors:
            # Convert the cleaned DataFrame to a list of dictionaries.
            # Each dictionary represents a row, with column headers as keys.
            cleaned_data = processed_df.to_dict(orient='records')
        else:
            cleaned_data = None # Ensure data is explicitly None if errors occurred.

    except Exception as e:
        # Catch any other unexpected errors during the entire processing.
        errors.append(f"An unexpected error occurred during file processing: {e}")
        cleaned_data = None

    return cleaned_data, errors
