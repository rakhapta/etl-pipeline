import pytest
import pandas as pd

@pytest.fixture(scope="session")
def sample_data():
    return {
        'id': [1, 2, 3],
        'title': ['Product A', 'Product B', 'Product C'],
        'price': [100, 200, 300],
        'description': ['Desc A', 'Desc B', 'Desc C'],
        'category': ['Cat A', 'Cat B', 'Cat C'],
        'image': ['img1.jpg', 'img2.jpg', 'img3.jpg']
    }

@pytest.fixture(scope="session")
def sample_df(sample_data):
    return pd.DataFrame(sample_data) 