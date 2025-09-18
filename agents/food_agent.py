import asyncio
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from models.data_models import AgentMessage, Restaurant, Location
from services.api_clients import YelpClient, ZomatoClient

class FoodAgent(BaseAgent):
    def __init__(self):
        super().__init__("food", ["restaurant_search", "cuisine_matching", "dietary_handling"])
        self.yelp_client = YelpClient()
        self.zomato_client = ZomatoClient()
        self.dietary_keywords = {
            "vegetarian": ["vegetarian", "veggie", "plant-based"],
            "vegan": ["vegan", "plant-based"],
            "gluten-free": ["gluten-free", "gluten free", "celiac"],
            "halal": ["halal", "muslim-friendly"],
            "kosher": ["kosher", "jewish"]
        }
        
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle incoming messages"""
        try:
            if message.message_type.value == "request":
                query_type = message.data.get("query_type")
                
                if query_type == "find_restaurants":
                    return await self.find_restaurants(message.data)
                elif query_type == "recommend_near_attractions":
                    return await self.recommend_near_attractions(message.data)
                elif query_type == "filter_by_dietary":
                    return await self.filter_by_dietary_restrictions(message.data)
                elif query_type == "get_local_specialties":
                    return await self.get_local_specialties(message.data)
                    
        except Exception as e:
            self.log(f"Error handling message: {str(e)}")
            return {"error": str(e)}
            
        return None
        
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method"""
        destination = request_data.get("destination")
        food_budget = request_data.get("food_budget")
        dietary_restrictions = request_data.get("dietary_restrictions", [])
        attraction_locations = request_data.get("attraction_locations", [])
        duration_days = request_data.get("duration_days", 2)
        
        self.log(f"Finding restaurants for {destination} with ${food_budget} budget")
        
        # Find restaurants for each day
        day1_restaurants = await self.find_day_restaurants(
            destination, attraction_locations[:len(attraction_locations)//2], 
            food_budget / 2, dietary_restrictions
        )
        
        day2_restaurants = await self.find_day_restaurants(
            destination, attraction_locations[len(attraction_locations)//2:], 
            food_budget / 2, dietary_restrictions
        )
        
        # Get local food recommendations
        local_specialties = await self.get_destination_specialties(destination)
        
        # Generate food tips
        food_tips = await self.generate_food_tips(destination, dietary_restrictions)
        
        return {
            "day1_restaurants": [r.dict() for r in day1_restaurants],
            "day2_restaurants": [r.dict() for r in day2_restaurants],
            "local_specialties": local_specialties,
            "food_tips": food_tips,
            "total_estimated_cost": sum(r.average_meal_cost for r in day1_restaurants + day2_restaurants),
            "dietary_accommodations": len(dietary_restrictions) > 0
        }
        
    async def find_restaurants(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Find restaurants based on criteria"""
        location = data.get("location")
        cuisine_type = data.get("cuisine_type")
        price_range = data.get("price_range", "$$")
        dietary_restrictions = data.get("dietary_restrictions", [])
        
        restaurants = await self.search_restaurants(
            location, cuisine_type, price_range, dietary_restrictions
        )
        
        return {
            "restaurants": [r.dict() for r in restaurants],
            "count": len(restaurants)
        }
        
    async def recommend_near_attractions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend restaurants near attractions"""
        attraction_locations = data.get("attraction_locations", [])
        budget_per_meal = data.get("budget_per_meal", 25)
        dietary_restrictions = data.get("dietary_restrictions", [])
        
        recommendations = {}
        
        for i, location in enumerate(attraction_locations):
            nearby_restaurants = await self.find_nearby_restaurants(
                location, budget_per_meal, dietary_restrictions
            )
            recommendations[f"attraction_{i+1}"] = [r.dict() for r in nearby_restaurants]
            
        return {"recommendations": recommendations}
        
    async def filter_by_dietary_restrictions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter restaurants by dietary restrictions"""
        restaurants = data.get("restaurants", [])
        restrictions = data.get("dietary_restrictions", [])
        
        filtered_restaurants = []
        
        for restaurant_data in restaurants:
            if await self.restaurant_meets_dietary_needs(restaurant_data, restrictions):
                filtered_restaurants.append(restaurant_data)
                
        return {
            "filtered_restaurants": filtered_restaurants,
            "original_count": len(restaurants),
            "filtered_count": len(filtered_restaurants)
        }
        
    async def get_local_specialties(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get local food specialties for destination"""
        destination = data.get("destination")
        
        specialties = await self.get_destination_specialties(destination)
        specialty_restaurants = await self.find_specialty_restaurants(destination, specialties)
        
        return {
            "local_specialties": specialties,
            "specialty_restaurants": [r.dict() for r in specialty_restaurants],
            "food_culture_tips": await self.get_food_culture_tips(destination)
        }
        
    async def find_day_restaurants(self, destination: str, attraction_locations: List[Location],
                                 daily_budget: float, dietary_restrictions: List[str]) -> List[Restaurant]:
        """Find restaurants for a specific day"""
        restaurants = []
        meals_per_day = 3  # breakfast, lunch, dinner
        budget_per_meal = daily_budget / meals_per_day
        
        # Find breakfast place
        breakfast_spots = await self.search_restaurants(
            destination, "cafe", "$", dietary_restrictions, meal_type="breakfast"
        )
        if breakfast_spots:
            restaurants.append(breakfast_spots[0])
            
        # Find lunch place near attractions
        if attraction_locations:
            mid_location = attraction_locations[len(attraction_locations)//2]
            lunch_spots = await self.find_nearby_restaurants(
                mid_location, budget_per_meal, dietary_restrictions, meal_type="lunch"
            )
            if lunch_spots:
                restaurants.append(lunch_spots[0])
                
        # Find dinner place
        dinner_spots = await self.search_restaurants(
            destination, "restaurant", "$$", dietary_restrictions, meal_type="dinner"
        )
        if dinner_spots:
            restaurants.append(dinner_spots[0])
            
        return restaurants
        
    async def search_restaurants(self, location: str, cuisine_type: str = None, 
                               price_range: str = "$$", dietary_restrictions: List[str] = None,
                               meal_type: str = None) -> List[Restaurant]:
        """Search for restaurants"""
        
        # Simulate API calls to restaurant services
        yelp_results = await self.yelp_client.search_restaurants(
            location, cuisine_type, price_range
        )
        zomato_results = await self.zomato_client.search_restaurants(
            location, cuisine_type, price_range
        )
        
        # Combine results
        all_restaurants = yelp_results + zomato_results
        
        # Filter by dietary restrictions
        if dietary_restrictions:
            all_restaurants = [r for r in all_restaurants 
                             if await self.restaurant_meets_dietary_needs(r.dict(), dietary_restrictions)]
            
        # Filter by meal type
        if meal_type:
            all_restaurants = [r for r in all_restaurants 
                             if await self.suitable_for_meal_type(r, meal_type)]
            
        # Sort by rating and return top results
        sorted_restaurants = sorted(all_restaurants, key=lambda x: x.rating, reverse=True)
        return sorted_restaurants[:5]
        
    async def find_nearby_restaurants(self, location: Location, budget_per_meal: float,
                                    dietary_restrictions: List[str], meal_type: str = None) -> List[Restaurant]:
        """Find restaurants near a specific location"""
        
        # Search within 1km radius
        nearby_restaurants = await self.search_restaurants(
            f"{location.latitude},{location.longitude}", 
            price_range=self.budget_to_price_range(budget_per_meal),
            dietary_restrictions=dietary_restrictions,
            meal_type=meal_type
        )
        
        return nearby_restaurants[:3]
        
    async def restaurant_meets_dietary_needs(self, restaurant_data: Dict[str, Any], 
                                           restrictions: List[str]) -> bool:
        """Check if restaurant meets dietary restrictions"""
        dietary_options = restaurant_data.get("dietary_options", [])
        
        for restriction in restrictions:
            keywords = self.dietary_keywords.get(restriction.lower(), [restriction.lower()])
            
            # Check if any keyword matches dietary options
            has_option = any(keyword in " ".join(dietary_options).lower() 
                           for keyword in keywords)
            
            if not has_option:
                return False
                
        return True
        
    async def suitable_for_meal_type(self, restaurant: Restaurant, meal_type: str) -> bool:
        """Check if restaurant is suitable for specific meal type"""
        meal_indicators = {
            "breakfast": ["cafe", "bakery", "breakfast", "brunch"],
            "lunch": ["restaurant", "cafe", "bistro", "lunch"],
            "dinner": ["restaurant", "fine dining", "dinner", "bar"]
        }
        
        indicators = meal_indicators.get(meal_type.lower(), [])
        restaurant_name_lower = restaurant.name.lower()
        cuisine_lower = restaurant.cuisine_type.lower()
        
        return any(indicator in restaurant_name_lower or indicator in cuisine_lower 
                  for indicator in indicators)
        
    async def get_destination_specialties(self, destination: str) -> List[Dict[str, str]]:
        """Get local food specialties for destination"""
        specialties_db = {
            "paris": [
                {"name": "Croissant", "description": "Buttery, flaky pastry perfect for breakfast"},
                {"name": "Coq au Vin", "description": "Classic French chicken braised in wine"},
                {"name": "Macarons", "description": "Colorful almond-based confection"}
            ],
            "tokyo": [
                {"name": "Sushi", "description": "Fresh fish over seasoned rice"},
                {"name": "Ramen", "description": "Japanese noodle soup"},
                {"name": "Takoyaki", "description": "Octopus balls from street vendors"}
            ],
            "rome": [
                {"name": "Carbonara", "description": "Pasta with eggs, cheese, and pancetta"},
                {"name": "Gelato", "description": "Italian-style ice cream"},
                {"name": "Pizza al Taglio", "description": "Roman-style rectangular pizza"}
            ]
        }
        
        return specialties_db.get(destination.lower(), [
            {"name": "Local Specialties", "description": "Ask locals for recommendations!"}
        ])
        
    async def find_specialty_restaurants(self, destination: str, 
                                       specialties: List[Dict[str, str]]) -> List[Restaurant]:
        """Find restaurants that serve local specialties"""
        specialty_restaurants = []
        
        for specialty in specialties[:2]:  # Limit to 2 specialties
            restaurants = await self.search_restaurants(
                destination, 
                cuisine_type=self.infer_cuisine_from_specialty(specialty["name"])
            )
            if restaurants:
                specialty_restaurants.append(restaurants[0])
                
        return specialty_restaurants
        
    async def generate_food_tips(self, destination: str, dietary_restrictions: List[str]) -> List[str]:
        """Generate food tips for the destination"""
        tips = [
            "Try local street food for authentic and budget-friendly meals",
            "Ask locals for their favorite hidden gem restaurants",
            "Check restaurant opening hours as they vary by country"
        ]
        
        if dietary_restrictions:
            tips.append("Download translation apps to communicate dietary restrictions")
            tips.append("Research local dietary options before arriving")
            
        destination_tips = {
            "paris": ["Lunch is typically served 12-2pm, dinner after 7:30pm"],
            "tokyo": ["Many restaurants are cash-only", "Tipping is not customary"],
            "rome": ["Cappuccino is only drunk in the morning", "Aperitivo time is 6-8pm"]
        }
        
        tips.extend(destination_tips.get(destination.lower(), []))
        
        return tips[:5]  # Limit to 5 tips
        
    async def get_food_culture_tips(self, destination: str) -> List[str]:
        """Get food culture tips for destination"""
        culture_tips = {
            "paris": [
                "French dining is leisurely - don't rush meals",
                "Bread is free at most restaurants",
                "Service charge is included in the bill"
            ],
            "tokyo": [
                "Slurping noodles is acceptable and shows appreciation",
                "Don't stick chopsticks upright in rice",
                "Many restaurants have plastic food displays"
            ],
            "rome": [
                "Romans eat dinner very late (after 8pm)",
                "Standing at a bar is cheaper than sitting at a table",
                "Each neighborhood has its own specialty dishes"
            ]
        }
        
        return culture_tips.get(destination.lower(), [
            "Research local dining customs before visiting",
            "Be respectful of local food traditions"
        ])
        
    def budget_to_price_range(self, budget: float) -> str:
        """Convert budget to price range symbol"""
        if budget <= 15:
            return "$"
        elif budget <= 30:
            return "$$" 
        elif budget <= 60:
            return "$$$"
        else:
            return "$$$$"
            
    def infer_cuisine_from_specialty(self, specialty_name: str) -> str:
        """Infer cuisine type from specialty dish name"""
        cuisine_mapping = {
            "croissant": "french",
            "coq au vin": "french", 
            "macarons": "french",
            "sushi": "japanese",
            "ramen": "japanese",
            "takoyaki": "japanese",
            "carbonara": "italian",
            "gelato": "italian",
            "pizza": "italian"
        }
        
        return cuisine_mapping.get(specialty_name.lower(), "local")
