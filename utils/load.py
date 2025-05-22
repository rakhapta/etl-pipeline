import pandas as pd
import logging
from pathlib import Path
import os
from sqlalchemy import create_engine
from google.oauth2 import service_account
from googleapiclient.discovery import build
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LoadError(Exception):
    """Custom exception for loading errors"""
    pass

def save_to_csv(df, output_path, index=False):
    """
    Save DataFrame to CSV file with error handling
    
    Args:
        df (pd.DataFrame): DataFrame to save
        output_path (str): Path to save the CSV file
        index (bool): Whether to save the index
        
    Raises:
        LoadError: If there are errors during saving
        ValueError: If input parameters are invalid
    """
    try:
        # Validate input
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if df.empty:
            raise ValueError("Cannot save empty DataFrame")
        
        if not output_path:
            raise ValueError("Output path is required")
            
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        # Save to CSV
        df.to_csv(output_path, index=index)
        logging.info(f"Successfully saved data to CSV: {output_path}")
        
    except Exception as e:
        logging.error(f"Error saving to CSV: {str(e)}")
        raise LoadError(f"Failed to save to CSV: {str(e)}")

def save_to_postgresql(df, table_name, connection_string):
    """
    Save DataFrame to PostgreSQL database
    
    Args:
        df (pd.DataFrame): DataFrame to save
        table_name (str): Name of the table to save to
        connection_string (str): SQLAlchemy connection string (e.g., 'postgresql://user:password@localhost:5432/dbname')
        
    Raises:
        LoadError: If there are errors during saving
        ValueError: If input parameters are invalid
    """
    try:
        # Validate input
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if df.empty:
            raise ValueError("Cannot save empty DataFrame")
        
        if not table_name or not connection_string:
            raise ValueError("Table name and connection string are required")
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Save to PostgreSQL - suppress the SQLAlchemy warning
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            df.to_sql(
                name=table_name,
                con=engine,
                if_exists='replace',  # Replace if table exists
                index=False,
                method='multi'  # Faster for larger datasets
            )
        
        logging.info(f"Successfully saved data to PostgreSQL table: {table_name}")
        
    except Exception as e:
        logging.error(f"Error saving to PostgreSQL: {str(e)}")
        raise LoadError(f"Failed to save to PostgreSQL: {str(e)}")

def save_to_google_sheets(df, spreadsheet_id, range_name, credentials_path):
    """
    Save DataFrame to Google Sheets
    
    Args:
        df (pd.DataFrame): DataFrame to save
        spreadsheet_id (str): The ID of the target Google Spreadsheet
        range_name (str): The range where data should be written (e.g., 'Sheet1!A1')
        credentials_path (str): Path to the Google Sheets API credentials JSON file
        
    Raises:
        LoadError: If there are errors during saving
        ValueError: If input parameters are invalid
    """
    try:
        # Validate input
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if df.empty:
            raise ValueError("Cannot save empty DataFrame")
        
        if not all([spreadsheet_id, range_name, credentials_path]):
            raise ValueError("Spreadsheet ID, range name, and credentials path are required")
        
        # Convert DataFrame to a format that can be written to Google Sheets
        values = [df.columns.tolist()]  # Header row
        
        # Create a copy of the data for processing
        df_values = df.copy()
        
        # Convert timestamp to string format if present
        if 'Timestamp' in df_values.columns:
            df_values['Timestamp'] = df_values['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Extend values with the processed data
        values.extend(df_values.values.tolist())
        
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Build the Sheets API service
        service = build('sheets', 'v4', credentials=credentials, client_options={'universe_domain': 'googleapis.com'})
        
        body = {
            'values': values
        }
        
        # Write to Google Sheets
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        logging.info(f"Successfully saved data to Google Sheets: {result.get('updatedRange')}")
        
    except Exception as e:
        logging.error(f"Error saving to Google Sheets: {str(e)}")
        raise LoadError(f"Failed to save to Google Sheets: {str(e)}")
