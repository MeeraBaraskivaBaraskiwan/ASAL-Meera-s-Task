
import pika
import json
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import time
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config

class QueueManager:
 
    
    def __init__(  self,  host: Optional[str] = None, port: Optional[int] = None,
        queue_name: Optional[str] = None, username: Optional[str] = None,
        password: Optional[str] = None ):
        
        self.host = host or config.RABBITMQ_HOST
        self.port = port or config.RABBITMQ_PORT
        self.queue_name = queue_name or config.RABBITMQ_QUEUE
        self.username = username or config.RABBITMQ_USER
        self.password = password or config.RABBITMQ_PASSWORD
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
    
    
    def connect(self) -> None:
      
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters( host=self.host, port=self.port,
                credentials=credentials,  heartbeat=600, blocked_connection_timeout=300 )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare( queue=self.queue_name,  durable=True   )
            
            print(f" Connected to RabbitMQ at {self.host}:{self.port}")
            print(f" Queue: {self.queue_name}")
            
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def disconnect(self) -> None:
   
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print(" Disconnected from RabbitMQ")
    
    def publish_file(self, filepath: Path) -> bool:
 
        if not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")
        
        try:
            message: Dict[str, Any] = { 'filepath': str(filepath),
                'filename': filepath.name, 'timestamp': time.time() }
            
            self.channel.basic_publish(  exchange='', routing_key=self.queue_name,
                body=json.dumps(message), properties=pika.BasicProperties(  delivery_mode=2,  ) )
            
            print(f"Published to queue: {filepath.name}")
            return True
            
        except Exception as e:
            print(f" Failed to publish file: {e}")
            return False
    
    def consume_files(  self, callback: Callable[[Path], None], auto_ack: bool = False ) -> None:
    
        if not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")
        
        def on_message(ch, method, properties, body):
    
            try:
                message = json.loads(body)
                filepath = Path(message['filepath'])
                
                print(f"\n Received from queue: {filepath.name}")
            
                callback(filepath)
                
               
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    print(f" Acknowledged: {filepath.name}")
                    
            except Exception as e:
                print(f" Error processing message: {e}")
          
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        

        self.channel.basic_qos(prefetch_count=1)
       
        self.channel.basic_consume( queue=self.queue_name, on_message_callback=on_message,  auto_ack=auto_ack )
        
        print(f"\n Waiting for messages in queue: {self.queue_name}")
      
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("\n\n Stopping consumer...")
            self.channel.stop_consuming()
    
    def get_queue_size(self) -> int:
   
        if not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")
        
        method = self.channel.queue_declare(  queue=self.queue_name,  durable=True, passive=True   )
        return method.method.message_count
    
    def purge_queue(self) -> None:
 
        if not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")
        
        self.channel.queue_purge(queue=self.queue_name)
        print(f" Purged all messages from queue: {self.queue_name}")


def test_connection(host: Optional[str] = None, port: Optional[int] = None) -> bool:
    try:
        queue_mgr = QueueManager(host=host, port=port)
        queue_mgr.connect()
        queue_mgr.disconnect()
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("TESTING RABBITMQ CONNECTION")
    print("="*60)
    
    if test_connection():
        print("\n RabbitMQ is running")
    else:
        print("\n Cannot connect to RabbitMQ!")
       




        