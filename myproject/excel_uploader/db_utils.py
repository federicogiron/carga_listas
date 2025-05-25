import pyodbc # For SQL Server database connectivity
from django.conf import settings # To access project settings (e.g., database credentials)
import logging # For logging errors and information

# Get an instance of a logger for this module
logger = logging.getLogger(__name__)

def get_sql_server_connection():
    """
    Establishes and returns a connection to the SQL Server database.

    Connection parameters (host, user, password, database name) are retrieved
    from the `AUTH_DB_MSSQL` dictionary in Django's `settings.py`.

    The connection string is configured for 'ODBC Driver 17 for SQL Server'.
    It includes 'TrustServerCertificate=yes', which might be necessary for
    development environments with self-signed certificates but should be
    reviewed for production security.

    Returns:
        tuple: (pyodbc.Connection object, error_message string)
            - If successful, (connection_object, None).
            - If an error occurs, (None, error_message_string).
    """
    # Retrieve SQL Server connection details from Django settings.
    # getattr is used to safely get the setting, defaulting to None if not found.
    db_config = getattr(settings, 'AUTH_DB_MSSQL', None)
    if not db_config:
        logger.error("AUTH_DB_MSSQL not configured in Django settings.")
        return None, "Database configuration (AUTH_DB_MSSQL) not found in settings.py."

    # Construct the connection string.
    # Ensure the ODBC driver specified matches the one installed on your system.
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};" 
        f"SERVER={db_config.get('DB_HOST')};" # Use .get() for safer dictionary access
        f"DATABASE={db_config.get('DB_NAME')};"
        f"UID={db_config.get('DB_USER')};"
        f"PWD={db_config.get('DB_PASSWORD')};"
        f"TrustServerCertificate=yes;" # Consider security implications for production
    )
    try:
        # Attempt to connect to the database.
        conn = pyodbc.connect(conn_str)
        return conn, None # Return connection object and no error message
    except pyodbc.Error as ex:
        # Handle database connection errors.
        sqlstate = ex.args[0] # pyodbc specific error code
        logger.error(f"SQL Server Connection Error: {sqlstate} - {ex}")
        return None, f"Database connection failed: {ex}" # Return None and error message

def insert_data_into_sql_server(data_list, table_name):
    """
    Inserts a list of dictionaries (records) into the specified SQL Server table.

    The function uses parameterized queries to prevent SQL injection.
    It handles transactions: all records are inserted, or none if an error occurs (rollback).

    Args:
        data_list (list of dict): A list of dictionaries where each dictionary
                                 represents a row of data to be inserted.
                                 Keys in the dictionary should correspond to column names.
                                 The column 'VentasQ(28d)' from Excel is expected to be
                                 renamed to 'VentasQ_28d' in the `data_list` before calling this.
        table_name (str): The name of the SQL Server table to insert data into.
                          IMPORTANT: This table name is used directly in the SQL query.
                          Currently, it's hardcoded in views.py as 'YourTargetTableName'.
                          Ensure this is changed to the actual table name.

    Returns:
        str or None:
            - None if the insertion is successful.
            - An error message string if any error occurs (e.g., no data,
              connection failure, SQL insertion error).
    """
    if not data_list:
        return "No data provided to insert."

    conn, error_msg = get_sql_server_connection()
    if error_msg: # If connection failed
        return error_msg

    cursor = None # Initialize cursor to None for finally block
    try:
        cursor = conn.cursor()
        
        # Define SQL column names based on the expected keys in `data_list`.
        # This order must match the order of values supplied to cursor.execute().
        # IMPORTANT: The key 'VentasQ(28d)' from the Excel file should be mapped to 'VentasQ_28d'
        # in the `data_list` *before* this function is called. This is handled in `views.py`.
        sql_columns = [
            'FECHA', 'TIENDA', 'SKU', 'DESCRIPCION_GDN', 'EAN',
            'PRECIO_REGULAR_GDN', 'PRECIO_OFERTA_GDN',
            'DESCUENTO_PROMEDIO', 'VentasQ_28d' # This matches the key after mapping in views.py
        ]
        
        # Create placeholders for parameterized query (e.g., (?, ?, ...))
        placeholders = ', '.join(['?'] * len(sql_columns))
        
        # Construct the SQL INSERT statement.
        # table_name should be a trusted value, not directly from user input without sanitization.
        # Here, it's intended to be set by the developer.
        insert_sql = f"INSERT INTO {table_name} ({', '.join(sql_columns)}) VALUES ({placeholders})"

        # Begin transaction: Disable autocommit to manage transaction manually.
        conn.autocommit = False 
        
        for record in data_list:
            # Create a list of values in the order defined by `sql_columns`.
            # record.get(col) is used to safely access keys, defaulting to None if a key is missing.
            values = [record.get(col) for col in sql_columns]
            cursor.execute(insert_sql, values)
        
        conn.commit() # Commit the transaction if all inserts are successful.
        return None # Indicate success
        
    except pyodbc.Error as ex:
        # If any pyodbc error occurs during insertion, rollback the transaction.
        if conn: # Check if conn exists before rollback
            conn.rollback()
        sqlstate = ex.args[0]
        logger.error(f"SQL Server Insert Error: {sqlstate} - {ex}. SQL: {insert_sql}")
        
        # Attempt to provide more specific error feedback (experimental)
        error_detail = str(ex)
        # This part tries to identify the problematic record. It's a simplified approach.
        # For complex scenarios, more robust error identification might be needed.
        if data_list and insert_sql: # Ensure these are defined
            for i, record_for_test in enumerate(data_list):
                try:
                    test_values = [record_for_test.get(col) for col in sql_columns]
                    # Create a new cursor for an isolated test execution (does not commit)
                    # This is to avoid issues with the main cursor's state after an error.
                    if conn: # Ensure connection is still available
                        with conn.cursor() as test_cursor: # Use 'with' for auto-closing
                             test_cursor.execute(insert_sql, test_values)
                except pyodbc.Error as single_ex:
                    error_detail = f"Error likely on data at index {i} (0-indexed): {record_for_test}. Details: {single_ex}"
                    logger.error(f"Potential error pinpointed on record {i}: {record_for_test}. Error: {single_ex}")
                    break # Stop after finding the first likely problematic record
                except Exception as general_ex:
                     error_detail = f"Unexpected error while trying to pinpoint issue on record at index {i}: {record_for_test}. Details: {general_ex}"
                     logger.error(f"Unexpected error checking record {i}: {record_for_test}. Error: {general_ex}")
                     break
        return f"Database insert failed. Details: {error_detail}"

    except Exception as e:
        # Catch any other non-pyodbc exceptions.
        if conn: # Check if conn exists before rollback
            conn.rollback()
        logger.error(f"Unexpected error during data insertion: {e}")
        return f"An unexpected error occurred during database operation: {e}"
    finally:
        # Ensure resources are closed.
        if cursor:
            cursor.close()
        if conn:
            conn.close()
