import pytest
import pandas as pd
import numpy as np
from utils.transform import transform_data, TransformationError, validate_transformed_data
from datetime import datetime

@pytest.fixture
def sample_raw_df():
    return pd.DataFrame({
        'Title': ['Product A', 'Product B', None],
        'Price': [100, -50, 200],
        'Rating': [4.5, 3.0, None],
        'Colors': [2, 1, 3],
        'Size': ['M', 'L', None],
        'Gender': ['Male', 'Female', None],
        'Timestamp': [datetime(2024, 3, 1, 12, 0, 0)] * 3  # Fixed timestamp
    })

def test_transform_data(sample_raw_df):
    transformed_df = transform_data(sample_raw_df)
    
    # Test data type transformations
    assert transformed_df['Price'].dtype == np.float64
    assert transformed_df['Rating'].dtype == np.int64
    assert transformed_df['Colors'].dtype == np.float64
    
    # Test data cleaning
    assert transformed_df['Title'].isnull().sum() == 0  # No null values in title
    assert all(transformed_df['Price'] >= 0)  # No negative prices
    assert all(transformed_df['Colors'] > 0)  # Valid colors count
    
    # Test data completeness
    expected_columns = ['Title', 'Price', 'Rating', 'Colors', 'Size', 'Gender', 'Timestamp']
    assert all(col in transformed_df.columns for col in expected_columns)
    
    # Test filled values
    assert transformed_df.loc[2, 'Title'] == 'Unknown Product'
    assert transformed_df.loc[2, 'Rating'] == 0
    assert transformed_df.loc[2, 'Size'] == 'Not Specified'
    assert transformed_df.loc[2, 'Gender'] == 'Unisex'

def test_transform_data_empty():
    empty_df = pd.DataFrame()
    with pytest.raises(TransformationError, match="Failed to transform data: Input DataFrame is empty"):
        transform_data(empty_df)

def test_transform_data_missing_columns():
    invalid_df = pd.DataFrame({'Title': ['Test']})  # Missing required columns
    with pytest.raises(TransformationError, match="Failed to transform data: Missing required columns"):
        transform_data(invalid_df)

def test_transform_invalid_input():
    with pytest.raises(TransformationError, match="Failed to transform data: Input must be a pandas DataFrame"):
        transform_data("not a dataframe")

# def test_transform_data_all_null():
#     all_null_df = pd.DataFrame({
#         'Title': [None, None],
#         'Price': [None, None],
#         'Rating': [None, None],
#         'Colors': [None, None],
#         'Size': [None, None],
#         'Gender': [None, None],
#         'Timestamp': [None, None]
#     })
#     transformed_df = transform_data(all_null_df)
    
#     assert all(transformed_df['Title'] == 'Unknown Product')
#     assert all(transformed_df['Rating'] == 0)
#     assert all(transformed_df['Size'] == 'Not Specified')
#     assert all(transformed_df['Gender'] == 'Unisex')

def test_validate_transformed_data():
    sample_df = pd.DataFrame({
        'Title': ['Product A'],
        'Price': [100.0],
        'Rating': [5],
        'Colors': [2.0],
        'Size': ['M'],
        'Gender': ['Male'],
        'Timestamp': [datetime.now()]
    })
    
    validation_results = validate_transformed_data(sample_df)
    
    assert isinstance(validation_results, dict)
    assert 'null_values' in validation_results
    assert 'data_types' in validation_results
    assert 'total_rows' in validation_results
    assert 'price_range' in validation_results
    assert 'unique_values' in validation_results
    assert 'extraction_time_range' in validation_results

def test_validate_transformed_data_empty():
    with pytest.raises(ValueError, match="Input DataFrame is empty"):
        validate_transformed_data(pd.DataFrame())

def test_validate_transformed_data_invalid_input():
    with pytest.raises(ValueError, match="Input must be a pandas DataFrame"):
        validate_transformed_data("not a dataframe")

# def test_transform_data_with_extreme_values():
#     extreme_df = pd.DataFrame({
#         'Title': ['Product A'],
#         'Price': [float('inf')],  # Test handling of infinite values
#         'Rating': [1000],  # Test handling of very large ratings
#         'Colors': [0],  # Test handling of zero colors
#         'Size': [''],  # Test handling of empty string
#         'Gender': ['Unknown'],  # Test handling of unknown gender
#         'Timestamp': [datetime.now()]
#     })
    
#     transformed_df = transform_data(extreme_df)
#     assert np.isfinite(transformed_df['Price'].iloc[0])  # Price should be finite
#     assert transformed_df['Rating'].iloc[0] == 1000  # Rating should be preserved
#     assert transformed_df['Colors'].iloc[0] == 0.0  # Colors should be preserved
#     assert transformed_df['Size'].iloc[0] == 'Not Specified'  # Empty size should be replaced
#     assert transformed_df['Gender'].iloc[0] == 'Unisex'  # Unknown gender should be replaced

# def test_transform_data_timestamp_handling():
#     # Test with different timestamp formats
#     timestamps_df = pd.DataFrame({
#         'Title': ['Product A', 'Product B', 'Product C'],
#         'Price': [100, 200, 300],
#         'Rating': [4, 5, 3],
#         'Colors': [2, 3, 1],
#         'Size': ['M', 'L', 'S'],
#         'Gender': ['Male', 'Female', 'Unisex'],
#         'Timestamp': [
#             datetime(2024, 3, 1, 12, 0, 0),
#             pd.Timestamp('2024-03-01 12:00:00'),
#             '2024-03-01 12:00:00'
#         ]
#     })
    
#     transformed_df = transform_data(timestamps_df)
#     assert all(isinstance(ts, (datetime, pd.Timestamp)) for ts in transformed_df['Timestamp'])
