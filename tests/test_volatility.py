import sys
sys.path.insert(0, '.')
from app import app
import json

with app.test_client() as client:
    response = client.get('/api/advanced/volatility')
    print('Status:', response.status_code)
    print('Data:', json.dumps(response.get_json(), indent=2))
