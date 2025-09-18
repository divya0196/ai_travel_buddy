from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AgentMessage(BaseModel):
    sender: str
    receiver: str
    message_type: MessageType
    timestamp: datetime
    data: Dict[str, Any]
    priority: Priority = Priority.MEDIUM

class Location(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    city: str
    country: str

class Attraction(BaseModel):
    id: str
    name: str
    description: str
    location: Location
    category: str
    rating: float
    price: float
    opening_hours: Dict[str, str]
    visit_duration: int  # minutes
    popularity_score: float
    image_url: Optional[str] = None

class Restaurant(BaseModel):
    id: str
    name: str
    cuisine_type: str
    location: Location
    rating: float
    price_range: str  # $, $$, $$$, $$$$
    average_meal_cost: float
    opening_hours: Dict[str, str]
    specialties: List[str]
    dietary_options: List[str]

class BudgetAllocation(BaseModel):
    total_budget: float
    accommodation: float
    food: float
    activities: float
    transport: float
    contingency: float = 0.0

class TripRequest(BaseModel):
    destination: str
    budget: float
    duration_days: int = 2
    interests: List[str] = []
    dietary_restrictions: List[str] = []
    accommodation_type: str = "hotel"
    transport_preference: str = "public"

class ItineraryItem(BaseModel):
    time: str
    activity: str
    location: Location
    duration: int  # minutes
    cost: float
    type: str  # attraction, restaurant, transport
    notes: Optional[str] = None

class DayPlan(BaseModel):
    day: int
    date: str
    items: List[ItineraryItem]
    total_cost: float
    estimated_walking_distance: float  # km

class TravelItinerary(BaseModel):
    destination: str
    total_budget: float
    total_cost: float
    days: List[DayPlan]
    budget_breakdown: BudgetAllocation
    recommendations: List[str]
    emergency_contacts: List[str]
