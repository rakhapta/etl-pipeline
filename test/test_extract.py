import pytest
import pandas as pd
from unittest.mock import patch, Mock
from utils.extract import extract_from_web, ExtractionError
import requests
import json

@pytest.fixture
def mock_html_response():
    return """
    <div class="collection-card">
        <h3 class="product-title">Test Product</h3>
        <span class="price">$100</span>
        <div class="product-details">
            <p>Rating: ⭐4.5/5</p>
            <p>2 Colors</p>
            <p>Size: M</p>
            <p>Gender: Unisex</p>
        </div>
    </div>
    """

@pytest.fixture
def mock_html_multiple_products():
    return """
    <div class="collection-card">
        <h3 class="product-title">Test Product 1</h3>
        <span class="price">$100</span>
        <div class="product-details">
            <p>Rating: ⭐4.5/5</p>
            <p>2 Colors</p>
            <p>Size: M</p>
            <p>Gender: Male</p>
        </div>
    </div>
    <div class="collection-card">
        <h3 class="product-title">Test Product 2</h3>
        <span class="price">$200</span>
        <div class="product-details">
            <p>Rating: ⭐3.0/5</p>
            <p>3 Colors</p>
            <p>Size: L</p>
            <p>Gender: Female</p>
        </div>
    </div>
    """

def test_extract_from_web(mock_html_response):
    with patch('requests.get') as mock_get:
        mock_get.return_value.content = mock_html_response.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert 'Title' in df.columns
        assert 'Price' in df.columns
        assert df.iloc[0]['Title'] == "Test Product"
        assert df.iloc[0]['Price'] == 100.0

def test_extract_multiple_products(mock_html_multiple_products):
    with patch('requests.get') as mock_get:
        mock_get.return_value.content = mock_html_multiple_products.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=5)
        
        assert len(df) == 2
        assert df.iloc[0]['Title'] == "Test Product 1"
        assert df.iloc[1]['Title'] == "Test Product 2"
        assert df.iloc[0]['Gender'] == "Male"
        assert df.iloc[1]['Gender'] == "Female"
        assert df.iloc[0]['Colors'] == 2
        assert df.iloc[1]['Colors'] == 3

def test_extract_max_items_limit(mock_html_multiple_products):
    with patch('requests.get') as mock_get:
        mock_get.return_value.content = mock_html_multiple_products.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=2, max_items=1)
        
        assert len(df) == 1  # Should stop after first item
        assert df.iloc[0]['Title'] == "Test Product 1"

def test_invalid_input_parameters():
    # Test invalid URL
    with pytest.raises(ExtractionError, match="Extraction failed: Invalid base URL provided"):
        extract_from_web(base_url="invalid_url", max_pages=1, max_items=1)
    
    # Test invalid max_pages
    with pytest.raises(ExtractionError, match="Extraction failed: max_pages must be a positive integer"):
        extract_from_web(base_url="https://test.com", max_pages=0, max_items=1)
    with pytest.raises(ExtractionError, match="Extraction failed: max_pages must be a positive integer"):
        extract_from_web(base_url="https://test.com", max_pages=-1, max_items=1)
    with pytest.raises(ExtractionError, match="Extraction failed: max_pages must be a positive integer"):
        extract_from_web(base_url="https://test.com", max_pages="invalid", max_items=1)
    
    # Test invalid max_items
    with pytest.raises(ExtractionError, match="Extraction failed: max_items must be a positive integer"):
        extract_from_web(base_url="https://test.com", max_pages=1, max_items=0)
    with pytest.raises(ExtractionError, match="Extraction failed: max_items must be a positive integer"):
        extract_from_web(base_url="https://test.com", max_pages=1, max_items=-1)
    with pytest.raises(ExtractionError, match="Extraction failed: max_items must be a positive integer"):
        extract_from_web(base_url="https://test.com", max_pages=1, max_items="invalid")

def test_network_errors():
    with patch('requests.get') as mock_get:
        # Test timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        with pytest.raises(ExtractionError, match="Extraction failed"):
            extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)
        
        # Test connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        with pytest.raises(ExtractionError, match="Extraction failed"):
            extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)

def test_invalid_html_response():
    with patch('requests.get') as mock_get:
        # Test missing product title
        mock_get.return_value.content = """
            <div class="collection-card">
                <span class="price">$100</span>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        with pytest.raises(ExtractionError, match="No data was extracted from any page"):
            extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)

def test_pagination():
    with patch('requests.get') as mock_get:
        def mock_response(*args, **kwargs):
            mock = Mock()
            mock.status_code = 200
            
            # Return different content for different pages
            if args[0] == "https://test.com":
                mock.content = """
                    <div class="collection-card">
                        <h3 class="product-title">Page 1 Product</h3>
                        <span class="price">$100</span>
                        <div class="product-details">
                            <p>Rating: ⭐4.5/5</p>
                            <p>2 Colors</p>
                            <p>Size: M</p>
                            <p>Gender: Unisex</p>
                        </div>
                    </div>
                """.encode()
            else:
                mock.content = """
                    <div class="collection-card">
                        <h3 class="product-title">Page 2 Product</h3>
                        <span class="price">$200</span>
                        <div class="product-details">
                            <p>Rating: ⭐3.0/5</p>
                            <p>3 Colors</p>
                            <p>Size: L</p>
                            <p>Gender: Unisex</p>
                        </div>
                    </div>
                """.encode()
            return mock
        
        mock_get.side_effect = mock_response
        df = extract_from_web(base_url="https://test.com", max_pages=2, max_items=5)
        
        assert len(df) == 2
        assert df.iloc[0]['Title'] == "Page 1 Product"
        assert df.iloc[1]['Title'] == "Page 2 Product"

def test_no_products_found():
    with patch('requests.get') as mock_get:
        mock_get.return_value.content = "<div>No products</div>".encode()
        mock_get.return_value.status_code = 200
        
        with pytest.raises(ExtractionError, match="No data was extracted from any page"):
            extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)

def test_partial_product_data():
    with patch('requests.get') as mock_get:
        # Test product with missing rating
        mock_get.return_value.content = """
            <div class="collection-card">
                <h3 class="product-title">Test Product</h3>
                <span class="price">$100</span>
                <div class="product-details">
                    <p>No Rating</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)
        assert pd.isna(df.iloc[0]['Rating'])  # Rating should be None

def test_missing_product_elements():
    with patch('requests.get') as mock_get:
        # Test missing title
        mock_get.return_value.content = """
            <div class="collection-card">
                <span class="price">$100</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
            <div class="collection-card">
                <h3 class="product-title">Valid Product</h3>
                <span class="price">$200</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=2)
        assert len(df) == 1  # Should skip the first product due to missing title
        assert df.iloc[0]['Title'] == "Valid Product"
        
        # Test missing price
        mock_get.return_value.content = """
            <div class="collection-card">
                <h3 class="product-title">Test Product</h3>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
            <div class="collection-card">
                <h3 class="product-title">Valid Product</h3>
                <span class="price">$200</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=2)
        assert len(df) == 1  # Should skip the first product due to missing price
        assert df.iloc[0]['Title'] == "Valid Product"

def test_failed_pages_logging():
    with patch('requests.get') as mock_get:
        def mock_response(*args, **kwargs):
            mock = Mock()
            url = args[0]
            
            if url == "https://test.com":
                mock.status_code = 200
                mock.content = """
                    <div class="collection-card">
                        <h3 class="product-title">Test Product</h3>
                        <span class="price">$100</span>
                        <div class="product-details">
                            <p>Rating: ⭐4.5/5</p>
                            <p>2 Colors</p>
                            <p>Size: M</p>
                            <p>Gender: Unisex</p>
                        </div>
                    </div>
                """.encode()
            else:
                raise requests.exceptions.RequestException("Failed to fetch page")
            
            return mock
        
        mock_get.side_effect = mock_response
        df = extract_from_web(base_url="https://test.com", max_pages=2, max_items=5)
        
        assert len(df) == 1  # Should have data from first page only
        assert df.iloc[0]['Title'] == "Test Product"

def test_http_status_codes():
    with patch('requests.get') as mock_get:
        # Test 404 Not Found
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        with pytest.raises(ExtractionError, match="Extraction failed"):
            extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)
        
        # Test 500 Server Error
        mock_get.return_value.status_code = 500
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        with pytest.raises(ExtractionError, match="Extraction failed"):
            extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)

def test_malformed_price():
    with patch('requests.get') as mock_get:
        # Test invalid price format
        mock_get.return_value.content = """
            <div class="collection-card">
                <h3 class="product-title">Test Product</h3>
                <span class="price">Invalid Price</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
            <div class="collection-card">
                <h3 class="product-title">Valid Product</h3>
                <span class="price">$200</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=2)
        assert len(df) == 1  # Should skip the first product due to invalid price
        assert df.iloc[0]['Title'] == "Valid Product"

def test_malformed_colors():
    with patch('requests.get') as mock_get:
        # Test invalid colors format
        mock_get.return_value.content = """
            <div class="collection-card">
                <h3 class="product-title">Test Product</h3>
                <span class="price">$100</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>Many Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
            <div class="collection-card">
                <h3 class="product-title">Valid Product</h3>
                <span class="price">$200</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=2)
        assert len(df) == 1  # Should skip the first product due to invalid colors
        assert df.iloc[0]['Title'] == "Valid Product"

def test_empty_response():
    with patch('requests.get') as mock_get:
        # Test empty response
        mock_get.return_value.content = "".encode()
        mock_get.return_value.status_code = 200
        
        with pytest.raises(ExtractionError, match="No data was extracted from any page"):
            extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)

def test_max_retries():
    with patch('requests.get') as mock_get:
        # Test max retries for failed pages
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        
        with pytest.raises(ExtractionError, match="Extraction failed"):
            extract_from_web(base_url="https://test.com", max_pages=3, max_items=1)
        
        # Should have tried 3 times
        assert mock_get.call_count == 3

def test_malformed_rating():
    with patch('requests.get') as mock_get:
        # Test invalid rating format
        mock_get.return_value.content = """
            <div class="collection-card">
                <h3 class="product-title">Test Product</h3>
                <span class="price">$100</span>
                <div class="product-details">
                    <p>Rating: Invalid</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)
        assert pd.isna(df.iloc[0]['Rating'])  # Rating should be None for invalid format

def test_missing_details_section():
    with patch('requests.get') as mock_get:
        # Test missing product details section
        mock_get.return_value.content = """
            <div class="collection-card">
                <h3 class="product-title">Test Product</h3>
                <span class="price">$100</span>
            </div>
            <div class="collection-card">
                <h3 class="product-title">Valid Product</h3>
                <span class="price">$200</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=2)
        assert len(df) == 1  # Should skip the first product due to missing details
        assert df.iloc[0]['Title'] == "Valid Product"

def test_invalid_details_count():
    with patch('requests.get') as mock_get:
        # Test product with wrong number of detail elements
        mock_get.return_value.content = """
            <div class="collection-card">
                <h3 class="product-title">Test Product</h3>
                <span class="price">$100</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                </div>
            </div>
            <div class="collection-card">
                <h3 class="product-title">Valid Product</h3>
                <span class="price">$200</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=2)
        assert len(df) == 1  # Should skip the first product due to invalid details count
        assert df.iloc[0]['Title'] == "Valid Product"

def test_unicode_characters():
    with patch('requests.get') as mock_get:
        # Test product with unicode characters
        mock_get.return_value.content = """
            <div class="collection-card">
                <h3 class="product-title">Test Product 👕</h3>
                <span class="price">$100</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)
        assert df.iloc[0]['Title'] == "Test Product 👕"  # Should handle unicode characters

def test_html_entities():
    with patch('requests.get') as mock_get:
        # Test HTML entities in text
        mock_get.return_value.content = """
            <div class="collection-card">
                <h3 class="product-title">Test &amp; Product</h3>
                <span class="price">$100</span>
                <div class="product-details">
                    <p>Rating: ⭐4.5/5</p>
                    <p>2 Colors</p>
                    <p>Size: M</p>
                    <p>Gender: Unisex</p>
                </div>
            </div>
        """.encode()
        mock_get.return_value.status_code = 200
        
        df = extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)
        assert df.iloc[0]['Title'] == "Test & Product"  # Should decode HTML entities

def test_redirect_handling():
    with patch('requests.get') as mock_get:
        # Test handling of redirects
        def mock_response(*args, **kwargs):
            mock = Mock()
            if args[0] == "https://test.com":
                mock.status_code = 302
                mock.headers = {'Location': 'https://test.com/redirected'}
                mock.raise_for_status.side_effect = requests.exceptions.HTTPError("302 Found")
            else:
                mock.status_code = 200
                mock.content = """
                    <div class="collection-card">
                        <h3 class="product-title">Test Product</h3>
                        <span class="price">$100</span>
                        <div class="product-details">
                            <p>Rating: ⭐4.5/5</p>
                            <p>2 Colors</p>
                            <p>Size: M</p>
                            <p>Gender: Unisex</p>
                        </div>
                    </div>
                """.encode()
            return mock
        
        mock_get.side_effect = mock_response
        with pytest.raises(ExtractionError, match="Extraction failed"):
            extract_from_web(base_url="https://test.com", max_pages=1, max_items=1)
