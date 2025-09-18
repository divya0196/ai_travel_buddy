import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.data_models import AgentMessage, MessageType, Priority

class BaseAgent(ABC):
    def __init__(self, agent_id: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.message_queue = asyncio.Queue()
        self.knowledge_base: Dict[str, Any] = {}
        self.is_active = False
        
    async def start(self):
        """Start the agent"""
        self.is_active = True
        print(f"[{self.agent_id}] Agent started")
        
    async def stop(self):
        """Stop the agent"""
        self.is_active = False
        print(f"[{self.agent_id}] Agent stopped")
        
    async def send_message(self, receiver: str, message_type: MessageType, 
                          data: Dict[str, Any], priority: Priority = Priority.MEDIUM):
        """Send message to another agent"""
        message = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            timestamp=datetime.now(),
            data=data,
            priority=priority
        )
        
        # In a real implementation, this would use a message broker
        print(f"[{self.agent_id}] Sending {message_type} to {receiver}: {data.get('query', 'No query')}")
        return message
        
    async def receive_message(self, message: AgentMessage):
        """Receive and queue message"""
        await self.message_queue.put(message)
        
    async def process_messages(self):
        """Process incoming messages"""
        while self.is_active:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                response = await self.handle_message(message)
                if response:
                    await self.send_response(message.sender, response)
            except asyncio.TimeoutError:
                continue
                
    async def send_response(self, receiver: str, response_data: Dict[str, Any]):
        """Send response back to requesting agent"""
        return await self.send_message(
            receiver, 
            MessageType.RESPONSE, 
            response_data, 
            Priority.HIGH
        )
        
    @abstractmethod
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle incoming message - must be implemented by subclasses"""
        pass
        
    @abstractmethod
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process specific request - must be implemented by subclasses"""
        pass
        
    def log(self, message: str):
        """Log agent activity"""
        print(f"[{self.agent_id}] {message}")
