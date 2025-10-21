from pathlib import Path
from datetime import date
import random
from typing import List

OUT: Path = Path("Incoming-data")
OUT.mkdir(exist_ok=True)

def generate_txt(day: date, rows: int = 20) -> None:
    brands : List[str] = ['Adidas', 'H&M', 'Zara', 'Gucci', 'Nike']
    products: List[str] =['Dress', 'Shoes', 'T-shirt', 'Jeans', 'Sweater']
    colors : List[str] = ['Black', 'White', 'Red', 'Yellow', 'Blue']
    sizes : List[str] = ['S', 'M', 'L', 'XL']

    header : str = "User ID,Product ID,Product Name,Brand,Category,Price,Rating,Color,Size\n"

    lines : List[str] = [header]
    for i in range(rows):
        user_id: int =  random.randint(10, 99)
        product_id: int =  i + 1
        product_name: str =  random.choice(products)
        brand : str =  random.choice(brands)
        category: str = random.choice(["Men's Fashion", "Women's Fashion"])
        price: int = random.randint(10, 120)
        rating: float = round(random.uniform(1.0, 5.0), 3)
        color : str =  random.choice(colors)
        size : str = random.choice(sizes)

        line: str = f"{user_id},{product_id},{product_name},{brand},{category},{price},{rating},{color},{size}\n"
        lines.append(line)

    fname: Path =OUT / f"data_{day.isoformat()}.txt"
    with open(fname, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"Created TXT file: {fname}")

if __name__ == "__main__":
    today = date.today()
    generate_txt(today)

