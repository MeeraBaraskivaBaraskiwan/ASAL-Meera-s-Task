import pika
import json
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import time
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config


class queue_manager:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or config.RABBITMQ_HOST
        self.port = port or config.RABBITMQ_PORT
        self.username = username or config.RABBITMQ_USER
        self.password = password or config.RABBITMQ_PASSWORD
        
   
        self.main_queue = config.RABBITMQ_QUEUE
        self.broken_queue = config.RABBITMQ_BROKEN_QUEUE
        
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
    
    def connect(self) -> None:
       
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
         
            self.channel.queue_declare(queue=self.main_queue, durable=True)
            self.channel.queue_declare(queue=self.broken_queue, durable=True)
            
            print(f" Connected to RabbitMQ at {self.host}:{self.port}")
            print(f" Main Queue: {self.main_queue}")
            print(f" Broken Queue: {self.broken_queue}")
            
        except pika.exceptions.AMQPConnectionError as e:
            print(f" Failed to connect to RabbitMQ: {e}")
            raise
    
    def disconnect(self) -> None:
    
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print(" Disconnected from RabbitMQ")
    
    def publish_to_main_queue(self, filepath: Path) -> bool:
    
        return self._publish_file(filepath, self.main_queue)
    
    def publish_to_broken_queue(self, filepath: Path, error_message: str = "") -> bool:
        
        if not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")
        
        try:
            message: Dict[str, Any] = {
                'filepath': str(filepath),
                'filename': filepath.name,
                'error_message': error_message,
                'timestamp': time.time(),
                'status': 'broken'
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key=self.broken_queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            print(f" Published to broken_queue: {filepath.name}")
            print(f"   Error: {error_message}")
            return True
            
        except Exception as e:
            print(f" Failed to publish to broken queue: {e}")
            return False
    
    def _publish_file(self, filepath: Path, queue_name: str) -> bool:
      
        if not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")
        
        try:
            message: Dict[str, Any] = {
                'filepath': str(filepath),
                'filename': filepath.name,
                'timestamp': time.time()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            print(f" Published to {queue_name}: {filepath.name}")
            return True
            
        except Exception as e:
            print(f" Failed to publish file: {e}")
            return False
    
    def get_queue_size(self, queue_name: Optional[str] = None) -> int:
       
        if not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")
        
        queue = queue_name or self.main_queue
        method = self.channel.queue_declare(
            queue=queue,
            durable=True,
            passive=True
        )
        return method.method.message_count
    
    def purge_queue(self, queue_name: Optional[str] = None) -> None:
        
        if not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")
        
        queue = queue_name or self.main_queue
        self.channel.queue_purge(queue=queue)
        print(f" Purged all messages from queue: {queue}")
    
    def consume_from_queue(
        self,
        callback: Callable,
        queue_name: Optional[str] = None,
        auto_ack: bool = False
    ) -> None:
     
        if not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")
        
        queue = queue_name or self.main_queue
        
        def on_message(ch, method, properties, body):
            try:
             
                if isinstance(body, bytes):
                    body = body.decode('utf-8')
                message = json.loads(body)
                callback(ch, method, properties, message)
                
            except Exception as e:
                print(f" Error in message callback: {e}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue,
            on_message_callback=on_message,
            auto_ack=auto_ack
        )
        
        print(f"\n Listening to queue: {queue}")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("\n\n  Stopping consumer...")
            self.channel.stop_consuming()


def test_enhanced_connection() -> bool:
  
    try:
        queue_mgr = queue_manager()
        queue_mgr.connect()
        
        print(f"\n Queue Status:")
        print(f"   Main Queue: {queue_mgr.get_queue_size(queue_mgr.main_queue)} messages")
        print(f"   Broken Queue: {queue_mgr.get_queue_size(queue_mgr.broken_queue)} messages")
        
        queue_mgr.disconnect()
        return True
    except Exception as e:
        print(f" Connection test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("TESTING ENHANCED RABBITMQ CONNECTION")
    print("="*60)
    
    if test_enhanced_connection():
        print("\n RabbitMQ is configured correctly")
    else:
        print("\n Cannot connect to RabbitMQ!")

        
