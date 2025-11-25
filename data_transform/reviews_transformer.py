import pandas as pd
from textblob import TextBlob
import re
from typing import Optional
from datetime import datetime
import numpy as np


class ReviewsTransformer:
    
    def __init__(self):
        self.column_mapping = {
            'Clothing ID': 'product_id',
            'Age': 'customer_age',
            'Title': 'review_title',
            'Review Text': 'review_text',
            'Rating': 'rating',
            'Recommended IND': 'recommended',
            'Division Name': 'division',
            'Department Name': 'department',
            'Class Name': 'product_class'
        }
    
    def transform(self, df: pd.DataFrame, source_file: str = "kaggle_reviews") -> pd.DataFrame:
        
        print(f"\n TRANSFORMING REVIEWS DATA")
        print(f"   Input rows: {len(df)}")
        

        df_clean = df.rename(columns=self.column_mapping)
        
   
        if 'product_name' not in df_clean.columns:
          
            df_clean['product_name'] = (
                df_clean.get('product_class', 'Unknown') + ' ' + 
                df_clean.get('department', 'Item')
            )
        
        if 'brand' not in df_clean.columns:
        
            df_clean['brand'] = df_clean.get('division', 'Fashion Brand')
        
     
        print("   Cleaning review text...")
        df_clean['review_text'] = df_clean['review_text'].apply(self._clean_text)
        
       
        print("   Computing sentiment scores (this may take a moment)...")
        df_clean['sentiment_score'] = df_clean['review_text'].apply(self._compute_sentiment)
        df_clean['sentiment_category'] = df_clean['sentiment_score'].apply(self._categorize_sentiment)
        
   
        df_clean['rating'] = df_clean['rating'].fillna(3).astype(int).clip(1, 5)
        df_clean['recommended'] = df_clean['recommended'].fillna(0).astype(bool)
        df_clean['customer_age'] = df_clean['customer_age'].fillna(30).astype(int).clip(18, 100)
        
       
        df_clean['review_date'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(
            np.random.randint(0, 365, size=len(df_clean)), unit='D'
        )
        
        
        df_clean['source_file'] = source_file
        
       
        final_columns = [
            'product_id', 'product_name', 'brand', 'department',
            'review_text', 'rating', 'recommended', 'customer_age',
            'review_date', 'sentiment_score', 'sentiment_category', 'source_file'
        ]
        
        df_final = df_clean[final_columns].copy()
        
    
        df_final = df_final.dropna(subset=['review_text', 'product_id'])
        df_final = df_final[df_final['review_text'].str.len() > 10] 
        df_final = df_final.drop_duplicates(subset=['product_id', 'review_text'])
        
        print(f"   Output rows: {len(df_final)}")
        print(f"   Sentiment distribution:")
        print(df_final['sentiment_category'].value_counts())
        
        return df_final
    
    def _clean_text(self, text: Optional[str]) -> str:
        
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
     
        text = re.sub(r'<[^>]+>', '', text)
        
       
        text = ' '.join(text.split())
        
       
        text = text[:5000]
        
        return text.strip()
    
    def _compute_sentiment(self, text: str) -> float:

        if not text or len(text) < 10:
            return 0.0
        
        try:
            blob = TextBlob(text)
            return round(blob.sentiment.polarity, 2)
        except:
            return 0.0
    
    def _categorize_sentiment(self, score: float) -> str:
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def get_summary_stats(self, df: pd.DataFrame) -> dict:
        
        return {
            'total_reviews': len(df),
            'avg_rating': df['rating'].mean(),
            'recommendation_rate': df['recommended'].mean(),
            'avg_sentiment': df['sentiment_score'].mean(),
            'positive_reviews': (df['sentiment_category'] == 'positive').sum(),
            'negative_reviews': (df['sentiment_category'] == 'negative').sum(),
            'unique_products': df['product_id'].nunique()
        }


if __name__ == "__main__":
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from data_sources.reviews_fetcher import ReviewsFetcher
    
    print("="*60)
    print("TESTING REVIEWS TRANSFORMER")
    print("="*60)
    
    fetcher = ReviewsFetcher()
    
    try:
        raw_df = fetcher.get_sample_data(n_rows=50)
        print(f"Fetched {len(raw_df)} sample reviews")
        
        transformer = ReviewsTransformer()
        transformed_df = transformer.transform(raw_df)
        
        print("\n TRANSFORMATION COMPLETE")
        print(f"\nSample transformed data:")
        print(transformed_df[['product_name', 'rating', 'sentiment_score', 'sentiment_category']].head())
        
        stats = transformer.get_summary_stats(transformed_df)
        print(f"\n Summary Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f" Error: {e}")
        print("\nMake sure to:")
        print("1. Download the reviews dataset")
        print("2. Install textblob: pip install textblob")
        print("3. Download corpora: python -m textblob.download_corpora")



        