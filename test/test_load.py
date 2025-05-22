import pytest
import pandas as pd
import tempfile
import os
from unittest import mock
from utils.load import save_to_csv, save_to_postgresql, save_to_google_sheets, LoadError

# === Sample DataFrame for testing ===
@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'Name': ['Item1', 'Item2'],
        'Price': [100, 200],
        'Timestamp': pd.to_datetime(['2023-01-01', '2023-01-02'])
    })

# === Test save_to_csv ===
def test_save_to_csv_success(sample_df):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "test_output.csv")
        save_to_csv(sample_df, path)
        assert os.path.exists(path)

def test_save_to_csv_empty_df():
    with pytest.raises(LoadError, match="Failed to save to CSV: Cannot save empty DataFrame"):
        save_to_csv(pd.DataFrame(), "output.csv")

def test_save_to_csv_invalid_input():
    with pytest.raises(LoadError, match="Failed to save to CSV: Input must be a pandas DataFrame"):
        save_to_csv("not a df", "output.csv")

# === Test save_to_postgresql ===
@mock.patch("utils.load.create_engine")
def test_save_to_postgresql_success(mock_engine, sample_df):
    mock_conn = mock.MagicMock()
    mock_engine.return_value = mock_conn
    save_to_postgresql(sample_df, "test_table", "postgresql://user:pass@localhost/db")
    mock_conn.connect.assert_not_called()  # We don't call connect directly
    # We rely on df.to_sql() using engine

def test_save_to_postgresql_invalid_input():
    with pytest.raises(LoadError, match="Failed to save to PostgreSQL: Input must be a pandas DataFrame"):
        save_to_postgresql("not a df", "table", "conn")

    with pytest.raises(LoadError, match="Failed to save to PostgreSQL: Cannot save empty DataFrame"):
        save_to_postgresql(pd.DataFrame(), "table", "conn")

    with pytest.raises(LoadError, match="Failed to save to PostgreSQL: Table name and connection string are required"):
        save_to_postgresql(pd.DataFrame({"a": [1]}), "", "")

# === Test save_to_google_sheets ===
@mock.patch("utils.load.build")
@mock.patch("utils.load.service_account.Credentials.from_service_account_file")
def test_save_to_google_sheets_success(mock_creds, mock_build, sample_df):
    mock_service = mock.MagicMock()
    mock_build.return_value = mock_service
    mock_sheets = mock_service.spreadsheets.return_value
    mock_values = mock_sheets.values.return_value
    mock_update = mock_values.update.return_value
    mock_update.execute.return_value = {'updatedRange': 'Sheet1!A1:C3'}

    save_to_google_sheets(
        df=sample_df,
        spreadsheet_id="fake_id",
        range_name="Sheet1!A1",
        credentials_path="fake_creds.json"
    )

    mock_build.assert_called_once()
    assert mock_update.execute.called

def test_save_to_google_sheets_invalid_input():
    with pytest.raises(LoadError, match="Failed to save to Google Sheets: Input must be a pandas DataFrame"):
        save_to_google_sheets("not a df", "id", "range", "creds")

    with pytest.raises(LoadError, match="Failed to save to Google Sheets: Cannot save empty DataFrame"):
        save_to_google_sheets(pd.DataFrame(), "id", "range", "creds")

    with pytest.raises(LoadError, match="Failed to save to Google Sheets: Spreadsheet ID, range name, and credentials path are required"):
        save_to_google_sheets(pd.DataFrame({"a": [1]}), "", "", "")
