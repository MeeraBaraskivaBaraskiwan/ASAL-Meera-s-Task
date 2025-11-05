from pathlib import Path
from datetime import date
from config import config  

OUT = config.INCOMING_DIR
OUT.mkdir(exist_ok=True)


def create_corrupted_csv_missing_columns():
    print("\nCreating CSV with MISSING COLUMNS...")
    
    filepath = OUT / f"corrupted_missing_cols_{date.today().isoformat()}.csv"
    
    content = """User ID,Product ID,Category,Price,Rating
1001,2001,Men's Fashion,50,4.5
1002,2002,Women's Fashion,75,4.8
"""
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Created: {filepath.name}")
    print(f"Error type: Missing 'Product Name' and 'Brand' columns")
    return filepath


def create_corrupted_csv_invalid_data():
    print("\nCreating CSV with INVALID DATA...")
    
    filepath = OUT / f"corrupted_invalid_data_{date.today().isoformat()}.csv"
    
    content = """User ID,Product ID,Product Name,Brand,Category,Price,Rating,Color,Size
1001,2001,T-Shirt,Nike,Men's Fashion,EXPENSIVE,4.5,Blue,M
1002,2002,Shoes,Adidas,Men's Fashion,FREE,4.8,Black,L
"""
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Created: {filepath.name}")
    print(f"Error type: Invalid price values")
    return filepath


def create_empty_file():
    print("\nCreating EMPTY FILE...")
    
    filepath = OUT / f"corrupted_empty_{date.today().isoformat()}.csv"
    
    with open(filepath, 'w') as f:
        f.write("")
    
    print(f"Created: {filepath.name}")
    print(f"Error type: Empty file")
    return filepath


def create_corrupted_json_invalid_structure():
    print("\nCreating JSON with INVALID STRUCTURE...")
    
    filepath = OUT / f"corrupted_structure_{date.today().isoformat()}.json"
    
    content = """{
    "products": [
        {
            "User ID": 1001,
            "Product ID": 2001,
            "Product Name": "T-Shirt"
        }
    
"""
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Created: {filepath.name}")
    print(f"Error type: Invalid JSON syntax")
    return filepath


def create_corrupted_csv_wrong_delimiter():
    print("\nCreating CSV with WRONG DELIMITER...")
    
    filepath = OUT / f"corrupted_delimiter_{date.today().isoformat()}.csv"
    
    content = """User ID;Product ID;Product Name;Brand;Category;Price;Rating;Color;Size
1001;2001;T-Shirt;Nike;Men's Fashion;50;4.5;Blue;M
1002;2002;Shoes;Adidas;Men's Fashion;75;4.8;Black;L
"""
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Created: {filepath.name}")
    print(f"Error type: Wrong delimiter (semicolons)")
    return filepath


def create_all_corrupted_files():
    print("="*60)
    print("CREATING CORRUPTED FILES FOR TASK 9 TESTING")
    print("="*60)
    
    files = []
    
    files.append(create_corrupted_csv_missing_columns())
    files.append(create_corrupted_csv_invalid_data())
    files.append(create_empty_file())
    files.append(create_corrupted_json_invalid_structure())
    files.append(create_corrupted_csv_wrong_delimiter())
    
    print("\n" + "="*60)
    print(f"Created {len(files)} corrupted files")
    print("="*60)
    
    return files


if __name__ == "__main__":
    create_all_corrupted_files()