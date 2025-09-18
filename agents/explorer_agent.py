import asyncio
import random
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from models.data_models import AgentMessage, Attraction, Location
from services.api_clients import GooglePlacesClient, TripAdvisorClient
from utils.helpers import calculate_distance, optimize_route

class ExplorerAgent(BaseAgent):
    def __init__(self):
        super().__init__("explorer", ["attraction_search", "route_optimization", "scheduling"])
        self.places_client = GooglePlacesClient()
        self.tripadvisor_client = TripAdvisorClient()
        
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle incoming messages"""
        try:
            if message.message_type.value == "request":
                query_type = message.data.get("query_type")
                
                if query_type == "find_attractions":
                    return await self.find_attractions(message.data)
                elif query_type == "optimize_route":
                    return await self.optimize_route(message.data)
                elif query_type == "get_attraction_details":
                    return await self.get_attraction_details(message.data)
                    
        except Exception as e:
            self.log(f"Error handling message: {str(e)}")
            return {"error": str(e)}
            
        return None
        
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method"""
        destination = request_data.get("destination")
        interests = request_data.get("interests", [])
        duration_days = request_data.get("duration_days", 2)
        budget_per_activity = request_data.get("budget_per_activity", 50)
        
        self.log(f"Finding attractions for {destination}")
        
        # Find attractions
        attractions = await self.search_attractions(destination, interests, budget_per_activity)
        
        # Optimize for 2-day itinerary
        day1_attractions, day2_attractions = await self.distribute_attractions(attractions, duration_days)
        
        # Optimize routes for each day
        day1_route = await self.create_optimized_route(day1_attractions)
        day2_route = await self.create_optimized_route(day2_attractions)
        
        return {
            "attractions": attractions,
            "day1_route": day1_route,
            "day2_route": day2_route,
            "total_estimated_cost": sum(a.price for a in attractions),
            "estimated_travel_time": await self.calculate_total_travel_time([day1_route, day2_route])
        }
        
    async def search_attractions(self, destination: str, interests: List[str], 
                               max_price: float) -> List[Attraction]:
        """Search for attractions based on destination and interests"""
        attractions = []
        
        # Simulate API calls to multiple services
        places_results = await self.places_client.search_attractions(destination, interests)
        tripadvisor_results = await self.tripadvisor_client.search_attractions(destination, interests)
        
        # Combine and deduplicate results
        all_results = places_results + tripadvisor_results
        unique_attractions = self.deduplicate_attractions(all_results)
        
        # Filter by price and rank by popularity
        filtered_attractions = [a for a in unique_attractions if a.price <= max_price]
        ranked_attractions = sorted(filtered_attractions, 
                                  key=lambda x: x.popularity_score, reverse=True)
        
        return ranked_attractions[:8]  # Top 8 attractions for 2 days
        
    async def find_attractions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Find attractions based on request"""
        destination = data.get("destination")
        interests = data.get("interests", [])
        budget = data.get("budget_per_activity", 50)
        
        attractions = await self.search_attractions(destination, interests, budget)
        
        return {
            "attractions": [a.dict() for a in attractions],
            "count": len(attractions)
        }
        
    async def optimize_route(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize route for given attractions"""
        attraction_ids = data.get("attraction_ids", [])
        start_location = data.get("start_location")
        
        # Get attraction details
        attractions = [await self.get_attraction_by_id(aid) for aid in attraction_ids]
        attractions = [a for a in attractions if a]  # Filter None values
        
        # Optimize route using traveling salesman approach
        optimized_route = await self.create_optimized_route(attractions, start_location)
        
        return {
            "optimized_route": optimized_route,
            "total_distance": await self.calculate_route_distance(optimized_route),
            "estimated_time": await self.calculate_route_time(optimized_route)
        }
        
    async def get_attraction_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about specific attraction"""
        attraction_id = data.get("attraction_id")
        attraction = await self.get_attraction_by_id(attraction_id)
        
        if attraction:
            return attraction.dict()
        return {"error": "Attraction not found"}
        
    def deduplicate_attractions(self, attractions: List[Attraction]) -> List[Attraction]:
        """Remove duplicate attractions based on name and location"""
        unique_attractions = {}
        for attraction in attractions:
            key = f"{attraction.name.lower()}_{attraction.location.city.lower()}"
            if key not in unique_attractions:
                unique_attractions[key] = attraction
                
        return list(unique_attractions.values())
        
    async def distribute_attractions(self, attractions: List[Attraction], 
                                   days: int) -> tuple[List[Attraction], List[Attraction]]:
        """Distribute attractions across days"""
        if days != 2:
            raise ValueError("Currently only supports 2-day trips")
            
        mid_point = len(attractions) // 2
        day1_attractions = attractions[:mid_point]
        day2_attractions = attractions[mid_point:]
        
        return day1_attractions, day2_attractions
        
    async def create_optimized_route(self, attractions: List[Attraction], 
                                   start_location: Optional[Location] = None) -> List[Dict[str, Any]]:
        """Create optimized route for attractions"""
        if not attractions:
            return []
            
        if len(attractions) == 1:
            return [{
                "attraction": attractions[0].dict(),
                "order": 1,
                "estimated_arrival": "09:00",
                "estimated_departure": "11:00"
            }]
            
        # Simple optimization: sort by geographical proximity
        optimized = optimize_route([a.location for a in attractions], start_location)
        
        route = []
        current_time = 9 * 60  # 9 AM in minutes
        
        for i, attraction in enumerate(optimized):
            arrival_time = f"{current_time // 60:02d}:{current_time % 60:02d}"
            departure_time = f"{(current_time + attraction.visit_duration) // 60:02d}:{(current_time + attraction.visit_duration) % 60:02d}"
            
            route.append({
                "attraction": attraction.dict(),
                "order": i + 1,
                "estimated_arrival": arrival_time,
                "estimated_departure": departure_time
            })
            
            current_time += attraction.visit_duration + 30  # 30 min travel buffer
            
        return route
        
    async def calculate_total_travel_time(self, routes: List[List[Dict[str, Any]]]) -> int:
        """Calculate total travel time for all routes"""
        total_time = 0
        for route in routes:
            for i in range(len(route) - 1):
                # Simulate travel time calculation
                total_time += 30  # 30 minutes average between attractions
        return total_time
        
    async def calculate_route_distance(self, route: List[Dict[str, Any]]) -> float:
        """Calculate total distance for route"""
        total_distance = 0.0
        for i in range(len(route) - 1):
            loc1 = route[i]["attraction"]["location"]
            loc2 = route[i + 1]["attraction"]["location"]
            total_distance += calculate_distance(
                (loc1["latitude"], loc1["longitude"]),
                (loc2["latitude"], loc2["longitude"])
            )
        return total_distance
        
    async def calculate_route_time(self, route: List[Dict[str, Any]]) -> int:
        """Calculate total time for route including visits and travel"""
        total_time = 0
        for item in route:
            total_time += item["attraction"]["visit_duration"]
            total_time += 30  # Travel time buffer
        return total_time
        
    async def get_attraction_by_id(self, attraction_id: str) -> Optional[Attraction]:
        """Get attraction by ID - simulate database lookup"""
        # In real implementation, this would query the database
        return None  # Placeholder
