import requests
import json
from pathlib import Path
from datetime import date
from typing import Optional, Dict, Any, List

def fetch_dummyjson()-> Optional[Path]:
    print("\nFetching real fashion products from DummyJSON API ")
 
    try:
        response = requests.get('https://dummyjson.com/products/category/womens-dresses')
        data: Dict[str, Any] = response.json()
        
        products: List[Dict[str, Any]] =data.get('products', [])
        print(f"Fetched {len(products)} products from external API")
        transformed : List[Dict[str, Any]] = []
        for p in products:
            product = {
                'User ID': 5000,
                'Product ID': p['id'] + 50000,  
                'Product Name': p['title'][:50],
                'Brand': p.get('brand', 'External Brand'),
                'Category': "Women's Fashion",
                'Price': int(p['price']),
                'Rating': round(p.get('rating', 4.0), 2),
                'Color': 'Multi',
                'Size': 'M'
            }
            transformed.append(product)
        
        output_dir : Path = Path('Incoming-data')
        output_dir.mkdir(exist_ok=True)
        
        json_file: Path =  output_dir / f"external_api_{date.today().isoformat()}.json"
        
        output_data: Dict[str, Any] ={
            'source': 'dummyjson_api',
            'products': transformed
        }
        
        with open(json_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Created: {json_file}")
        print(f"Contains {len(transformed)} products")
        print(f"Product IDs: {transformed[0]['Product ID']} - {transformed[-1]['Product ID']}")
        
        return json_file
        
    except Exception as e:
        print(f" Error: {e}")
        return None

if __name__ == "__main__":
    print("="*60)
    print("FETCHING REAL EXTERNAL JSON FOR TASK 2")
    print("="*60)
    
    result = fetch_dummyjson()
    
    print("\n" + "="*60)
    if result:
        print("SUCCESS ;) ")

