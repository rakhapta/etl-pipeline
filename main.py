from utils.extract import extract_from_web
from utils.transform import transform_data
from utils.load import save_to_csv, save_to_postgresql, save_to_google_sheets

if __name__ == "__main__":
    # Configuration
    BASE_URL = "https://fashion-studio.dicoding.dev"
    MAX_PAGES = 50
    MAX_ITEMS = 1000
    
    # PostgreSQL configuration
    DB_CONNECTION = "postgresql://postgres:derahutan44@localhost:5432/fashion_db"
    TABLE_NAME = "products"
    
    # Google Sheets configuration
    SPREADSHEET_ID = "1F3pS1Hcb7GzH-QJEfuCxotGJ806mEEwUzY3940r1sOY"
    RANGE_NAME = "Sheet1!A1"
    CREDENTIALS_PATH = "google-sheets-api.json"

    # Extract
    raw_df = extract_from_web(base_url=BASE_URL, max_pages=MAX_PAGES, max_items=MAX_ITEMS)
    print(raw_df.head())
    print(raw_df.info())
    
    # Transform
    cleaned_df = transform_data(raw_df)
    print(cleaned_df.head())
    print(cleaned_df.info())
    
    # Load
    # 1. Save to CSV (Basic requirement)
    save_to_csv(cleaned_df, "product.csv")
    print("Data saved to CSV successfully")
    
    # 2. Save to PostgreSQL
    try:
        save_to_postgresql(cleaned_df, TABLE_NAME, DB_CONNECTION)
        print("Data saved to PostgreSQL successfully")
    except Exception as e:
        print(f"Error saving to PostgreSQL: {e}")
    
    # 3. Save to Google Sheets
    try:
        save_to_google_sheets(cleaned_df, SPREADSHEET_ID, RANGE_NAME, CREDENTIALS_PATH)
        print("Data saved to Google Sheets successfully")
    except Exception as e:
        print(f"Error saving to Google Sheets: {e}")
