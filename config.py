import os
from typing import Dict, Any

class Config:
    # API Keys (use environment variables in production)
    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "demo_key")
    YELP_API_KEY = os.getenv("YELP_API_KEY", "demo_key")
    TRIPADVISOR_API_KEY = os.getenv("TRIPADVISOR_API_KEY", "demo_key")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///travel_buddy.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Agent Configuration
    AGENT_TIMEOUT = 30  # seconds
    MAX_ATTRACTIONS_PER_DAY = 4
    MAX_RESTAURANTS_PER_DAY = 3
    
    # Budget Distribution (percentages)
    DEFAULT_BUDGET_ALLOCATION = {
        "accommodation": 0.45,
        "food": 0.27,
        "activities": 0.18,
        "transport": 0.10
    }

config = Config()
