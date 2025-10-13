from extract import extract_data
from transform import transform_data
from load import load_data_to_db
from report import generate_report

def main():
    df = extract_data('fashion_products.csv')
    engine = load_data_to_db(transform_data(df), 'fashion_sales')
    generate_report(engine)

if __name__ == "__main__":
    main()





    