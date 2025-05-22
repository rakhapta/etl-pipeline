import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TransformationError(Exception):
    """Custom exception for transformation errors"""
    pass

def transform_data(df):
    """
    Transform the extracted data with error handling
    
    Args:
        df (pd.DataFrame): Input DataFrame to transform
        
    Returns:
        pd.DataFrame: Transformed DataFrame
        
    Raises:
        TransformationError: If there are critical errors during transformation
        ValueError: If input DataFrame is invalid
    """
    try:
        # Validate input
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if df.empty:
            raise ValueError("Input DataFrame is empty")
            
        required_columns = ['Title', 'Price', 'Rating', 'Colors', 'Size', 'Gender', 'Timestamp']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
        # Create a copy to avoid modifying the original dataframe
        df_transformed = df.copy()
        
        # Handle null values with logging
        null_counts_before = df_transformed.isnull().sum()
        
        # Update fillna operations to avoid FutureWarnings
        df_transformed = df_transformed.assign(
            Title=df_transformed['Title'].fillna('Unknown Product'),
            Rating=df_transformed['Rating'].fillna(0),
            Size=df_transformed['Size'].fillna('Not Specified'),
            Gender=df_transformed['Gender'].fillna('Unisex')
        )
        
        # Handle negative prices and convert numeric columns
        df_transformed.loc[df_transformed['Price'] < 0, 'Price'] = 0
        df_transformed['Price'] = df_transformed['Price'].astype(np.float64)
        
        # Convert Rating to int64 - first round to nearest integer then convert
        df_transformed['Rating'] = df_transformed['Rating'].round().astype(np.int64)
        
        # Convert Colors to float64
        df_transformed['Colors'] = df_transformed['Colors'].astype(np.float64)
        
        null_counts_after = df_transformed.isnull().sum()
        
        if null_counts_before.any():
            logging.info(f"Null values handled: Before={null_counts_before}, After={null_counts_after}")
            
        return df_transformed
        
    except Exception as e:
        logging.error(f"Error during data transformation: {str(e)}")
        raise TransformationError(f"Failed to transform data: {str(e)}")

def validate_transformed_data(df):
    """
    Validate the transformed data with error handling
    
    Args:
        df (pd.DataFrame): DataFrame to validate
        
    Returns:
        dict: Validation results
        
    Raises:
        ValueError: If input DataFrame is invalid
    """
    try:
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if df.empty:
            raise ValueError("Input DataFrame is empty")

        validation_results = {
            'null_values': df.isnull().sum().to_dict(),
            'data_types': df.dtypes.to_dict(),
            'total_rows': len(df),
            'price_range': {
                'min': df['Price'].min(),
                'max': df['Price'].max()
            },
            'unique_values': {
                'Gender': df['Gender'].unique().tolist(),
                'Size': df['Size'].unique().tolist()
            },
            'extraction_time_range': {
                'earliest': df['Timestamp'].min(),
                'latest': df['Timestamp'].max()
            }
        }
        
        logging.info("Data validation completed successfully")
        return validation_results

    except Exception as e:
        logging.error(f"Error during data validation: {str(e)}")
        raise ValueError(f"Validation failed: {str(e)}")
