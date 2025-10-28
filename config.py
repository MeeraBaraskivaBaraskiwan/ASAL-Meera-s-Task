import os
from pathlib import Path
from typing import Optional


class Config:
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '5432')
    DB_NAME: str = os.getenv('DB_NAME', 'fashion_db')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '12345678')
    
    @classmethod
    def get_database_url(cls) -> str:
        return f'postgresql+psycopg2://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}'
    
    RABBITMQ_HOST: str = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT: int = int(os.getenv('RABBITMQ_PORT', '5672'))
    RABBITMQ_USER: str = os.getenv('RABBITMQ_USER', 'guest')
    RABBITMQ_PASSWORD: str = os.getenv('RABBITMQ_PASSWORD', 'guest')
    RABBITMQ_QUEUE: str = os.getenv('RABBITMQ_QUEUE', 'file_processing_queue')
    

    INCOMING_DIR: Path = Path(os.getenv('INCOMING_DIR', 'Incoming-data'))
    ARCHIVE_DIR: Path = Path(os.getenv('ARCHIVE_DIR', 'Archived-data'))
    
  
    TABLE_NAME: str = os.getenv('TABLE_NAME', 'fashion_sales')
    
    @classmethod
    def validate(cls) -> bool:

        if cls.DB_PASSWORD == '12345678':
            print("WARNING: Using default database password")
        
        if cls.RABBITMQ_PASSWORD == 'guest':
            print("WARNING: Using default RabbitMQ password")
        
        return True
    
  

config = Config()


if __name__ == "__main__":
    config.validate()
    print(f"\nDatabase URL: {config.get_database_url()}")