import random
from typing import List, Dict, Any, Optional
from models.data_models import Attraction, Restaurant, Location

# Mock API clients for demonstration
# In production, these would make real API calls

class GooglePlacesClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
    async def search_attractions(self, destination: str, interests: List[str]) -> List[Attraction]:
        """Mock Google Places API search"""
        
        # Mock attraction data
        mock_attractions = [
            {
                "id": f"place_{random.randint(1000, 9999)}",
                "name": "Historic Museum",
                "description": "Explore the rich history and culture",
                "category": "museum",
                "rating": round(random.uniform(4.0, 5.0), 1),
                "price": random.choice([0, 10, 15, 20, 25]),
                "visit_duration": random.choice([90, 120, 150, 180]),
                "popularity_score": random.uniform(0.7, 1.0)
            },
            {
                "id": f"place_{random.randint(1000, 9999)}",
                "name": "Central Park",
                "description": "Beautiful green space in the city center",
                "category": "park",
                "rating": round(random.uniform(4.0, 5.0), 1),
                "price": 0,
                "visit_duration": random.choice([60, 90, 120]),
                "popularity_score": random.uniform(0.8, 1.0)
            },
            {
                "id": f"place_{random.randint(1000, 9999)}",
                "name": "Art Gallery",
                "description": "Contemporary and classical art collections",
                "category": "museum",
                "rating": round(random.uniform(3.5, 5.0), 1),
                "price": random.choice([12, 18, 25]),
                "visit_duration": random.choice([90, 120, 150]),
                "popularity_score": random.uniform(0.6, 0.9)
            },
            {
                "id": f"place_{random.randint(1000, 9999)}",
                "name": "Historic Cathedral",
                "description": "Stunning architecture and religious history",
                "category": "monument",
                "rating": round(random.uniform(4.0, 5.0), 1),
                "price": random.choice([0, 5, 8]),
                "visit_duration": random.choice([60, 90, 120]),
                "popularity_score": random.uniform(0.7, 0.95)
            }
        ]
        
        attractions = []
        for mock_data in mock_attractions:
            location = Location(
                name=mock_data["name"],
                address=f"123 Main St, {destination}",
                latitude=random.uniform(-90, 90),
                longitude=random.uniform(-180, 180),
                city=destination,
                country="Unknown"
            )
            
            attraction = Attraction(
                **mock_data,
                location=location,
                opening_hours={
                    "monday": "09:00-17:00",
                    "tuesday": "09:00-17:00",
                    "wednesday": "09:00-17:00",
                    "thursday": "09:00-17:00",
                    "friday": "09:00-17:00",
                    "saturday": "10:00-18:00",
                    "sunday": "10:00-16:00"
                },
                image_url=f"https://example.com/image_{mock_data['id']}.jpg"
            )
            attractions.append(attraction)
            
        return attractions

class TripAdvisorClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
    async def search_attractions(self, destination: str, interests: List[str]) -> List[Attraction]:
        """Mock TripAdvisor API search"""
        
        # Return different mock data than Google Places
        mock_attractions = [
            {
                "id": f"ta_{random.randint(1000, 9999)}",
                "name": "City Walking Tour",
                "description": "Discover hidden gems with a local guide",
                "category": "tour",
                "rating": round(random.uniform(4.0, 5.0), 1),
                "price": random.choice([20, 25, 30, 35]),
                "visit_duration": random.choice([120, 150, 180]),
                "popularity_score": random.uniform(0.75, 0.95)
            },
            {
                "id": f"ta_{random.randint(1000, 9999)}",
                "name": "Observation Deck",
                "description": "Panoramic views of the entire city",
                "category": "viewpoint",
                "rating": round(random.uniform(4.0, 5.0), 1),
                "price": random.choice([15, 20, 25]),
                "visit_duration": random.choice([60, 90]),
                "popularity_score": random.uniform(0.8, 1.0)
            }
        ]
        
        attractions = []
        for mock_data in mock_attractions:
            location = Location(
                name=mock_data["name"],
                address=f"456 Tourist Ave, {destination}",
                latitude=random.uniform(-90, 90),
                longitude=random.uniform(-180, 180),
                city=destination,
                country="Unknown"
            )
            
            attraction = Attraction(
                **mock_data,
                location=location,
                opening_hours={
                    "monday": "08:00-20:00",
                    "tuesday": "08:00-20:00",
                    "wednesday": "08:00-20:00",
                    "thursday": "08:00-20:00",
                    "friday": "08:00-20:00",
                    "saturday": "08:00-20:00",
                    "sunday": "09:00-19:00"
                },
                image_url=f"https://tripadvisor.com/image_{mock_data['id']}.jpg"
            )
            attractions.append(attraction)
            
        return attractions

class YelpClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
    async def search_restaurants(self, location: str, cuisine_type: str = None, 
                               price_range: str = "$$") -> List[Restaurant]:
        """Mock Yelp API search"""
        
        cuisines = ["italian", "french", "asian", "american", "mexican", "indian"]
        selected_cuisine = cuisine_type or random.choice(cuisines)
        
        mock_restaurants = [
            {
                "id": f"yelp_{random.randint(1000, 9999)}",
                "name": f"The {selected_cuisine.title()} Corner",
                "cuisine_type": selected_cuisine,
                "rating": round(random.uniform(3.5, 5.0), 1),
                "price_range": price_range,
                "average_meal_cost": self._price_range_to_cost(price_range),
                "specialties": [f"Signature {selected_cuisine} dish", f"Chef's special"],
                "dietary_options": ["vegetarian options available"]
            },
            {
                "id": f"yelp_{random.randint(1000, 9999)}",
                "name": f"Bistro {random.choice(['Central', 'Modern', 'Classic'])}",
                "cuisine_type": selected_cuisine,
                "rating": round(random.uniform(3.8, 4.8), 1),
                "price_range": price_range,
                "average_meal_cost": self._price_range_to_cost(price_range),
                "specialties": [f"Local {selected_cuisine} cuisine"],
                "dietary_options": ["vegan options", "gluten-free available"]
            }
        ]
        
        restaurants = []
        for mock_data in mock_restaurants:
            location_obj = Location(
                name=mock_data["name"],
                address=f"789 Restaurant Row, {location}",
                latitude=random.uniform(-90, 90),
                longitude=random.uniform(-180, 180),
                city=location,
                country="Unknown"
            )
            
            restaurant = Restaurant(
                **mock_data,
                location=location_obj,
                opening_hours={
                    "monday": "11:00-22:00",
                    "tuesday": "11:00-22:00",
                    "wednesday": "11:00-22:00",
                    "thursday": "11:00-22:00",
                    "friday": "11:00-23:00",
                    "saturday": "10:00-23:00",
                    "sunday": "10:00-21:00"
                }
            )
            restaurants.append(restaurant)
            
        return restaurants
        
    def _price_range_to_cost(self, price_range: str) -> float:
        """Convert price range to average cost"""
        cost_mapping = {
            "$": random.uniform(10, 20),
            "$$": random.uniform(20, 40),
            "$$$": random.uniform(40, 70),
            "$$$$": random.uniform(70, 120)
        }
        return round(cost_mapping.get(price_range, 25), 2)

class ZomatoClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
    async def search_restaurants(self, location: str, cuisine_type: str = None, 
                               price_range: str = "$$") -> List[Restaurant]:
        """Mock Zomato API search"""
        
        cuisines = ["thai", "chinese", "mediterranean", "japanese", "greek"]
        selected_cuisine = cuisine_type or random.choice(cuisines)
        
        mock_restaurants = [
            {
                "id": f"zomato_{random.randint(1000, 9999)}",
                "name": f"{selected_cuisine.title()} Garden",
                "cuisine_type": selected_cuisine,
                "rating": round(random.uniform(3.8, 4.9), 1),
                "price_range": price_range,
                "average_meal_cost": self._price_range_to_cost(price_range),
                "specialties": [f"Authentic {selected_cuisine} flavors"],
                "dietary_options": ["halal options", "vegetarian friendly"]
            }
        ]
        
        restaurants = []
        for mock_data in mock_restaurants:
            location_obj = Location(
                name=mock_data["name"],
                address=f"321 Food Street, {location}",
                latitude=random.uniform(-90, 90),
                longitude=random.uniform(-180, 180),
                city=location,
                country="Unknown"
            )
            
            restaurant = Restaurant(
                **mock_data,
                location=location_obj,
                opening_hours={
                    "monday": "12:00-22:00",
                    "tuesday": "12:00-22:00",
                    "wednesday": "12:00-22:00",
                    "thursday": "12:00-22:00",
                    "friday": "12:00-23:00",
                    "saturday": "12:00-23:00",
                    "sunday": "12:00-21:00"
                }
            )
            restaurants.append(restaurant)
            
        return restaurants
        
    def _price_range_to_cost(self, price_range: str) -> float:
        """Convert price range to average cost"""
        cost_mapping = {
            "$": random.uniform(8, 18),
            "$$": random.uniform(18, 35),
            "$$$": random.uniform(35, 65),
            "$$$$": random.uniform(65, 110)
        }
        return round(cost_mapping.get(price_range, 22), 2)
