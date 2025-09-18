import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent
from agents.explorer_agent import ExplorerAgent
from agents.budget_agent import BudgetAgent
from agents.food_agent import FoodAgent
from models.data_models import (
    AgentMessage, MessageType, Priority, TripRequest, 
    TravelItinerary, DayPlan, ItineraryItem, BudgetAllocation
)

class MasterCoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("master_coordinator", ["orchestration", "synthesis", "quality_control"])
        
        # Initialize sub-agents
        self.explorer_agent = ExplorerAgent()
        self.budget_agent = BudgetAgent()
        self.food_agent = FoodAgent()
        
        self.agents = {
            "explorer": self.explorer_agent,
            "budget": self.budget_agent,
            "food": self.food_agent
        }
        
    async def start(self):
        """Start all agents"""
        await super().start()
        
        # Start all sub-agents
        for agent in self.agents.values():
            await agent.start()
            
        self.log("All agents started successfully")
        
    async def stop(self):
        """Stop all agents"""
        # Stop all sub-agents
        for agent in self.agents.values():
            await agent.stop()
            
        await super().stop()
        self.log("All agents stopped")
        
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle incoming messages"""
        # Master coordinator typically doesn't receive messages from other agents
        # It orchestrates the workflow
        return None
        
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main orchestration method - this is the entry point"""
        try:
            # Validate and parse request
            trip_request = TripRequest(**request_data)
            
            self.log(f"Processing trip request for {trip_request.destination}")
            
            # Phase 1: Parallel Information Gathering
            phase1_results = await self.phase1_information_gathering(trip_request)
            
            # Phase 2: Cross-Agent Communication and Validation
            phase2_results = await self.phase2_cross_agent_communication(
                trip_request, phase1_results
            )
            
            # Phase 3: Optimization
            phase3_results = await self.phase3_optimization(
                trip_request, phase2_results
            )
            
            # Phase 4: Final Synthesis
            final_itinerary = await self.phase4_final_synthesis(
                trip_request, phase3_results
            )
            
            return {
                "success": True,
                "itinerary": final_itinerary.dict(),
                "processing_time": datetime.now().isoformat(),
                "agent_contributions": {
                    "explorer": len(phase1_results["attractions"]),
                    "budget": 1,  # budget allocation
                    "food": len(phase1_results["restaurants"])
                }
            }
            
        except Exception as e:
            self.log(f"Error processing request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def phase1_information_gathering(self, trip_request: TripRequest) -> Dict[str, Any]:
        """Phase 1: Parallel information gathering from all agents"""
        self.log("Phase 1: Starting parallel information gathering")
        
        # Create tasks for parallel execution
        tasks = []
        
        # Explorer Agent Task
        explorer_task = asyncio.create_task(
            self.explorer_agent.process_request({
                "destination": trip_request.destination,
                "interests": trip_request.interests,
                "duration_days": trip_request.duration_days,
                "budget_per_activity": trip_request.budget * 0.18 / 4  # Rough estimate
            })
        )
        tasks.append(("explorer", explorer_task))
        
        # Budget Agent Task
        budget_task = asyncio.create_task(
            self.budget_agent.process_request({
                "budget": trip_request.budget,
                "destination": trip_request.destination,
                "duration_days": trip_request.duration_days,
                "accommodation_type": trip_request.accommodation_type
            })
        )
        tasks.append(("budget", budget_task))
        
        # Food Agent Task - will be updated with locations later
        food_task = asyncio.create_task(
            self.food_agent.process_request({
                "destination": trip_request.destination,
                "food_budget": trip_request.budget * 0.27,  # Rough estimate
                "dietary_restrictions": trip_request.dietary_restrictions,
                "duration_days": trip_request.duration_days,
                "attraction_locations": []  # Will be updated in phase 2
            })
        )
        tasks.append(("food", food_task))
        
        # Wait for all tasks to complete
        results = {}
        for agent_name, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=30)
                results[agent_name] = result
                self.log(f"Phase 1: {agent_name} agent completed")
            except asyncio.TimeoutError:
                self.log(f"Phase 1: {agent_name} agent timed out")
                results[agent_name] = {"error": "timeout"}
            except Exception as e:
                self.log(f"Phase 1: {agent_name} agent error: {str(e)}")
                results[agent_name] = {"error": str(e)}
                
        # Extract key information for cross-communication
        attractions = results.get("explorer", {}).get("attractions", [])
        budget_allocation = results.get("budget", {}).get("budget_allocation", {})
        restaurants = results.get("food", {}).get("day1_restaurants", []) + results.get("food", {}).get("day2_restaurants", [])
        
        return {
            "attractions": attractions,
            "budget_allocation": budget_allocation,
            "restaurants": restaurants,
            "raw_results": results
        }
        
    async def phase2_cross_agent_communication(self, trip_request: TripRequest, 
                                             phase1_results: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Cross-agent communication and validation"""
        self.log("Phase 2: Starting cross-agent communication")
        
        attractions = phase1_results["attractions"]
        budget_allocation = phase1_results["budget_allocation"]
        
        # Task 1: Budget validates Explorer's costs
        attraction_costs = [a.get("price", 0) for a in attractions]
        budget_validation = await self.budget_agent.handle_message(
            await self.send_message("budget", MessageType.REQUEST, {
                "query_type": "validate_costs",
                "budget_allocation": budget_allocation,
                "proposed_costs": {
                    "activities": sum(attraction_costs)
                }
            })
        )
        
        # Task 2: Food Agent aligns with attraction locations
        attraction_locations = [a.get("location", {}) for a in attractions]
        updated_food_recommendations = await self.food_agent.handle_message(
            await self.send_message("food", MessageType.REQUEST, {
                "query_type": "recommend_near_attractions",
                "attraction_locations": attraction_locations,
                "budget_per_meal": budget_allocation.get("food", 0) / 6,  # 3 meals x 2 days
                "dietary_restrictions": trip_request.dietary_restrictions
            })
        )
        
        # Task 3: Explorer adjusts based on budget constraints
        if budget_validation and not budget_validation.get("budget_feasible", True):
            adjusted_attractions = await self.explorer_agent.handle_message(
                await self.send_message("explorer", MessageType.REQUEST, {
                    "query_type": "find_attractions",
                    "destination": trip_request.destination,
                    "interests": trip_request.interests,
                    "budget_per_activity": budget_allocation.get("activities", 0) / 4
                })
            )
            attractions = adjusted_attractions.get("attractions", attractions)
            
        return {
            "validated_attractions": attractions,
            "budget_validation": budget_validation,
            "updated_restaurants": updated_food_recommendations,
            "cross_communication_complete": True
        }
        
    async def phase3_optimization(self, trip_request: TripRequest, 
                                phase2_results: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Route and time optimization"""
        self.log("Phase 3: Starting optimization")
        
        attractions = phase2_results["validated_attractions"]
        
        # Optimize routes for each day
        mid_point = len(attractions) // 2
        day1_attractions = attractions[:mid_point]
        day2_attractions = attractions[mid_point:]
        
        # Get optimized routes
        day1_route = await self.explorer_agent.handle_message(
            await self.send_message("explorer", MessageType.REQUEST, {
                "query_type": "optimize_route",
                "attraction_ids": [a.get("id", f"attr_{i}") for i, a in enumerate(day1_attractions)],
                "start_location": None
            })
        )
        
        day2_route = await self.explorer_agent.handle_message(
            await self.send_message("explorer", MessageType.REQUEST, {
                "query_type": "optimize_route", 
                "attraction_ids": [a.get("id", f"attr_{i}") for i, a in enumerate(day2_attractions)],
                "start_location": None
            })
        )
        
        return {
            "day1_optimized_route": day1_route,
            "day2_optimized_route": day2_route,
            "optimization_complete": True
        }
        
    async def phase4_final_synthesis(self, trip_request: TripRequest, 
                                   phase3_results: Dict[str, Any]) -> TravelItinerary:
        """Phase 4: Synthesize final itinerary"""
        self.log("Phase 4: Synthesizing final itinerary")
        
        # Create day plans
        day1_plan = await self.create_day_plan(
            1, 
            phase3_results.get("day1_optimized_route", {}),
            trip_request
        )
        
        day2_plan = await self.create_day_plan(
            2,
            phase3_results.get("day2_optimized_route", {}), 
            trip_request
        )
        
        # Calculate total costs
        total_cost = day1_plan.total_cost + day2_plan.total_cost
        
        # Create budget breakdown
        budget_breakdown = BudgetAllocation(
            total_budget=trip_request.budget,
            accommodation=trip_request.budget * 0.45,
            food=trip_request.budget * 0.27,
            activities=trip_request.budget * 0.18,
            transport=trip_request.budget * 0.10
        )
        
        # Generate recommendations
        recommendations = await self.generate_final_recommendations(
            trip_request, [day1_plan, day2_plan], total_cost
        )
        
        # Create final itinerary
        itinerary = TravelItinerary(
            destination=trip_request.destination,
            total_budget=trip_request.budget,
            total_cost=total_cost,
            days=[day1_plan, day2_plan],
            budget_breakdown=budget_breakdown,
            recommendations=recommendations,
            emergency_contacts=await self.get_emergency_contacts(trip_request.destination)
        )
        
        self.log("Phase 4: Final synthesis complete")
        return itinerary
        
    async def create_day_plan(self, day_number: int, route_data: Dict[str, Any], 
                            trip_request: TripRequest) -> DayPlan:
        """Create a day plan from route data"""
        
        # Get base date
        base_date = datetime.now() + timedelta(days=7)  # Assume trip is next week
        day_date = base_date + timedelta(days=day_number - 1)
        
        items = []
        total_cost = 0
        
        # Extract route information
        optimized_route = route_data.get("optimized_route", [])
        
        for route_item in optimized_route:
            attraction = route_item.get("attraction", {})
            
            # Create itinerary item
            item = ItineraryItem(
                time=route_item.get("estimated_arrival", "09:00"),
                activity=attraction.get("name", "Unknown Activity"),
                location=attraction.get("location", {}),
                duration=attraction.get("visit_duration", 120),
                cost=attraction.get("price", 0),
                type="attraction",
                notes=attraction.get("description", "")[:100]  # Truncate description
            )
            
            items.append(item)
            total_cost += item.cost
            
        # Add meal items (simplified)
        meal_cost = (trip_request.budget * 0.27) / 4  # Budget per meal
        
        items.insert(0, ItineraryItem(
            time="08:00",
            activity="Breakfast",
            location={},
            duration=60,
            cost=meal_cost * 0.5,  # Breakfast is usually cheaper
            type="restaurant",
            notes="Start your day with local breakfast"
        ))
        
        items.insert(len(items)//2 + 1, ItineraryItem(
            time="12:30", 
            activity="Lunch",
            location={},
            duration=90,
            cost=meal_cost,
            type="restaurant",
            notes="Lunch break near attractions"
        ))
        
        items.append(ItineraryItem(
            time="19:00",
            activity="Dinner", 
            location={},
            duration=120,
            cost=meal_cost * 1.5,  # Dinner is usually more expensive
            type="restaurant",
            notes="End your day with local cuisine"
        ))
        
        total_cost += meal_cost * 3
        
        return DayPlan(
            day=day_number,
            date=day_date.strftime("%Y-%m-%d"),
            items=items,
            total_cost=total_cost,
            estimated_walking_distance=route_data.get("total_distance", 5.0)
        )
        
    async def generate_final_recommendations(self, trip_request: TripRequest, 
                                           day_plans: List[DayPlan], 
                                           total_cost: float) -> List[str]:
        """Generate final recommendations for the trip"""
        recommendations = []
        
        # Budget recommendations
        budget_utilization = (total_cost / trip_request.budget) * 100
        if budget_utilization < 80:
            recommendations.append(f"You're using {budget_utilization:.0f}% of your budget - consider adding more activities or upgrading meals")
        elif budget_utilization > 95:
            recommendations.append("You're at budget limit - consider having some meals at budget-friendly places")
            
        # Activity recommendations
        total_activities = sum(len([item for item in day.items if item.type == "attraction"]) 
                             for day in day_plans)
        if total_activities < 4:
            recommendations.append("Consider adding free activities like parks or walking tours")
            
        # General recommendations
        recommendations.extend([
            "Download offline maps before traveling",
            "Keep digital and physical copies of important documents",
            "Check weather forecast and pack accordingly",
            "Learn basic phrases in the local language"
        ])
        
        return recommendations[:5]  # Limit to 5 recommendations
        
    async def get_emergency_contacts(self, destination: str) -> List[str]:
        """Get emergency contacts for destination"""
        # This would typically query a database of emergency contacts
        emergency_contacts = {
            "paris": ["Police: 17", "Medical: 15", "Fire: 18", "Tourist Hotline: +33 1 42 86 43 43"],
            "tokyo": ["Police: 110", "Fire/Medical: 119", "Tourist Hotline: +81 3 3201 3331"],
            "rome": ["Police: 113", "Medical: 118", "Fire: 115", "Tourist Police: +39 06 4686 2987"]
        }
        
        return emergency_contacts.get(destination.lower(), [
            "Check local emergency numbers upon arrival",
            "Contact your country's embassy in case of emergencies"
        ])

    async def create_travel_itinerary(self, trip_request: TripRequest) -> TravelItinerary:
        """Public method to create a complete travel itinerary"""
        self.log(f"Creating itinerary for {trip_request.destination}")
        
        result = await self.process_request(trip_request.dict())
        
        if result.get("success"):
            return TravelItinerary(**result["itinerary"])
        else:
            raise Exception(f"Failed to create itinerary: {result.get('error', 'Unknown error')}")
