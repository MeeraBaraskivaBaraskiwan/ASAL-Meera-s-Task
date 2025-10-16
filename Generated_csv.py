import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import random

OUT = Path("Incoming-data")
OUT.mkdir(exist_ok=True)

def gen(day, rows=30):
    rows_list = []
    brands = ['Adidas','H&M','Zara','Gucci','Nike']
    products = ['Dress','Shoes','T-shirt','Jeans','Sweater']
    colors = ['Black','White','Red','Yellow','Blue']
    sizes = ['S','M','L','XL']
    for i in range(rows):
        rows_list.append({
            'User ID': random.randint(1000,3000),
            'Product ID': random.randint(800,1200),
            'Product Name': random.choice(products),
            'Brand': random.choice(brands),
            'Category': "Men's Fashion",
            'Price': random.randint(10,120),
            'Rating': round(random.random()*5, 6),
            'Color': random.choice(colors),
            'Size': random.choice(sizes),
        })
    df = pd.DataFrame(rows_list)
    fname = OUT / f"data_{day.isoformat()}.csv"
    df.to_csv(fname, index=False)
    print("Created mock file:", fname)

if __name__ == "__main__":
    today = date.today()
    gen(today)              
    gen(today - timedelta(days=1)) 