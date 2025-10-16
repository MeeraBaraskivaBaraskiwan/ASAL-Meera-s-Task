import json
from pathlib import Path
import random
from datetime import date

OUT = Path("Incoming-data")
OUT.mkdir(exist_ok=True)

def gen_json(day, rows=10):
    brands = ['Adidas','H&M','Zara','Gucci','Nike']
    products = ['Dress','Shoes','T-shirt','Jeans','Sweater']
    colors = ['Black','White','Red','Yellow','Blue']
    sizes = ['S','M','L','XL']

    data = []
    for _ in range(rows):
        data.append({
            "User ID": random.randint(1000,3000),
            "Product ID": random.randint(800,1200),
            "Product Name": random.choice(products),
            "Brand": random.choice(brands),
            "Category": "Men's Fashion",
            "Price": random.randint(10,120),
            "Rating": round(random.random()*5, 6),
            "Color": random.choice(colors),
            "Size": random.choice(sizes)
        })

    fname = OUT / f"data_{day.isoformat()}.json"
    with open(fname, 'w') as f:
        json.dump(data, f, indent=4)
    print("Created mock JSON file:", fname)

if __name__ == "__main__":
    gen_json(date.today())