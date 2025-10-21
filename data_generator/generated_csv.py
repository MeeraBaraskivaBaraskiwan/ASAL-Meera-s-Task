import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import random
from typing import List, Dict, Any

OUT : Path = Path("Incoming-data")
OUT.mkdir(exist_ok=True)

def generate_csv(day:date, rows :int=30) -> None:
    rows_list: List[Dict[str, Any]] = []
    brands : List[str] = ['Adidas','H&M','Zara','Gucci','Nike']
    products : List[str] =['Dress','Shoes','T-shirt','Jeans','Sweater']
    colors : List[str] = ['Black','White','Red','Yellow','Blue']
    sizes : List[str] = ['S','M','L','XL']
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
    df : pd.DataFrame = pd.DataFrame(rows_list)
    fname : Path =OUT / f"data_{day.isoformat()}.csv"
    df.to_csv(fname, index=False)
    print("Created mock file:", fname)

if __name__ == "__main__":
    today = date.today()
    generate_csv(today)              
    generate_csv(today - timedelta(days=1)) 