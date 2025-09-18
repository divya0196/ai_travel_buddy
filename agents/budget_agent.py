import asyncio
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from models.data_models import AgentMessage, BudgetAllocation
from config import config

class BudgetAgent(BaseAgent):
    def __init__(self):
        super().__init__("budget", ["budget_allocation", "cost_estimation", "optimization"])
        self.cost_models = self.load_cost_models()
        
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle incoming messages"""
        try:
            if message.message_type.value == "request":
                query_type = message.data.get("query_type")
                
                if query_type == "allocate_budget":
                    return await self.allocate_budget(message.data)
                elif query_type == "validate_costs":
                    return await self.validate_costs(message.data)
                elif query_type == "optimize_spending":
                    return await self.optimize_spending(message.data)
                elif query_type == "estimate_costs":
                    return await self.estimate_costs(message.data)
                    
        except Exception as e:
            self.log(f"Error handling message: {str(e)}")
            return {"error": str(e)}
            
        return None
        
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method"""
        total_budget = request_data.get("budget")
        destination = request_data.get("destination")
        duration_days = request_data.get("duration_days", 2)
        accommodation_type = request_data.get("accommodation_type", "hotel")
        
        self.log(f"Processing budget allocation for ${total_budget} in {destination}")
        
        # Create budget allocation
        allocation = await self.create_budget_allocation(
            total_budget, destination, duration_days, accommodation_type
        )
        
        # Estimate costs for different categories
        cost_estimates = await self.estimate_category_costs(destination, duration_days)
        
        # Validate if budget is sufficient
        budget_analysis = await self.analyze_budget_feasibility(allocation, cost_estimates)
        
        return {
            "budget_allocation": allocation.dict(),
            "cost_estimates": cost_estimates,
            "budget_analysis": budget_analysis,
            "recommendations": await self.generate_budget_recommendations(allocation, cost_estimates)
        }
        
    async def allocate_budget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate budget across categories"""
        total_budget = data.get("total_budget")
        preferences = data.get("preferences", {})
        
        # Use custom allocation if provided, otherwise use defaults
        allocation_ratios = {**config.DEFAULT_BUDGET_ALLOCATION, **preferences}
        
        allocation = BudgetAllocation(
            total_budget=total_budget,
            accommodation=total_budget * allocation_ratios["accommodation"],
            food=total_budget * allocation_ratios["food"],
            activities=total_budget * allocation_ratios["activities"],
            transport=total_budget * allocation_ratios["transport"],
            contingency=total_budget * 0.05  # 5% contingency
        )
        
        return {
            "allocation": allocation.dict(),
            "per_day_budget": {
                "accommodation": allocation.accommodation / 2,
                "food": allocation.food / 2,
                "activities": allocation.activities / 2,
                "transport": allocation.transport / 2
            }
        }
        
    async def validate_costs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if proposed costs fit within budget"""
        budget_allocation = data.get("budget_allocation")
        proposed_costs = data.get("proposed_costs", {})
        
        validation_results = {}
        total_overspend = 0
        
        for category, allocated_amount in budget_allocation.items():
            if category == "total_budget":
                continue
                
            proposed_amount = proposed_costs.get(category, 0)
            is_within_budget = proposed_amount <= allocated_amount
            overspend = max(0, proposed_amount - allocated_amount)
            
            validation_results[category] = {
                "allocated": allocated_amount,
                "proposed": proposed_amount,
                "within_budget": is_within_budget,
                "overspend": overspend,
                "percentage_used": (proposed_amount / allocated_amount) * 100 if allocated_amount > 0 else 0
            }
            
            total_overspend += overspend
            
        return {
            "validation_results": validation_results,
            "total_overspend": total_overspend,
            "budget_feasible": total_overspend == 0,
            "adjustments_needed": await self.suggest_adjustments(validation_results) if total_overspend > 0 else []
        }
        
    async def optimize_spending(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize spending to fit within budget"""
        current_costs = data.get("current_costs")
        budget_limits = data.get("budget_limits")
        priorities = data.get("priorities", {})
        
        optimized_costs = {}
        saved_amount = 0
        
        # Sort categories by priority (lower priority gets cut first)
        sorted_categories = sorted(current_costs.items(), 
                                 key=lambda x: priorities.get(x[0], 5))
        
        for category, cost in sorted_categories:
            budget_limit = budget_limits.get(category, 0)
            
            if cost > budget_limit:
                reduction_needed = cost - budget_limit
                optimized_cost = budget_limit
                saved_amount += reduction_needed
                
                optimized_costs[category] = {
                    "original_cost": cost,
                    "optimized_cost": optimized_cost,
                    "savings": reduction_needed,
                    "optimization_applied": True
                }
            else:
                optimized_costs[category] = {
                    "original_cost": cost,
                    "optimized_cost": cost,
                    "savings": 0,
                    "optimization_applied": False
                }
                
        return {
            "optimized_costs": optimized_costs,
            "total_savings": saved_amount,
            "optimization_suggestions": await self.generate_optimization_suggestions(optimized_costs)
        }
        
    async def estimate_costs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate costs for specific items or categories"""
        destination = data.get("destination")
        items = data.get("items", [])
        category = data.get("category")
        
        estimated_costs = {}
        
        for item in items:
            if category == "attractions":
                estimated_costs[item] = await self.estimate_attraction_cost(destination, item)
            elif category == "restaurants":
                estimated_costs[item] = await self.estimate_restaurant_cost(destination, item)
            elif category == "accommodation":
                estimated_costs[item] = await self.estimate_accommodation_cost(destination, item)
            elif category == "transport":
                estimated_costs[item] = await self.estimate_transport_cost(destination, item)
                
        return {
            "estimated_costs": estimated_costs,
            "total_estimated": sum(estimated_costs.values()),
            "cost_confidence": "medium"  # In real app, this would be calculated
        }
        
    async def create_budget_allocation(self, total_budget: float, destination: str, 
                                     duration_days: int, accommodation_type: str) -> BudgetAllocation:
        """Create detailed budget allocation"""
        
        # Adjust allocation based on destination cost level
        destination_multiplier = await self.get_destination_cost_multiplier(destination)
        
        # Base allocation
        base_allocation = config.DEFAULT_BUDGET_ALLOCATION.copy()
        
        # Adjust for accommodation type
        if accommodation_type == "hostel":
            base_allocation["accommodation"] *= 0.6
            base_allocation["activities"] += base_allocation["accommodation"] * 0.4
        elif accommodation_type == "luxury":
            base_allocation["accommodation"] *= 1.5
            base_allocation["food"] *= 0.8
            base_allocation["activities"] *= 0.8
            
        return BudgetAllocation(
            total_budget=total_budget,
            accommodation=total_budget * base_allocation["accommodation"] * destination_multiplier,
            food=total_budget * base_allocation["food"] * destination_multiplier,
            activities=total_budget * base_allocation["activities"],
            transport=total_budget * base_allocation["transport"],
            contingency=total_budget * 0.05
        )
        
    async def estimate_category_costs(self, destination: str, duration_days: int) -> Dict[str, Dict[str, float]]:
        """Estimate costs for different categories"""
        multiplier = await self.get_destination_cost_multiplier(destination)
        
        return {
            "accommodation": {
                "budget": 40 * duration_days * multiplier,
                "mid_range": 80 * duration_days * multiplier,
                "luxury": 200 * duration_days * multiplier
            },
            "food": {
                "budget": 30 * duration_days * multiplier,
                "mid_range": 60 * duration_days * multiplier,
                "luxury": 120 * duration_days * multiplier
            },
            "activities": {
                "budget": 20 * duration_days,
                "mid_range": 50 * duration_days,
                "luxury": 100 * duration_days
            },
            "transport": {
                "public": 10 * duration_days * multiplier,
                "taxi": 40 * duration_days * multiplier,
                "car_rental": 60 * duration_days * multiplier
            }
        }
        
    async def analyze_budget_feasibility(self, allocation: BudgetAllocation, 
                                       cost_estimates: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Analyze if the budget allocation is feasible"""
        
        analysis = {
            "accommodation_feasible": allocation.accommodation >= cost_estimates["accommodation"]["budget"],
            "food_feasible": allocation.food >= cost_estimates["food"]["budget"],
            "activities_feasible": allocation.activities >= cost_estimates["activities"]["budget"],
            "transport_feasible": allocation.transport >= cost_estimates["transport"]["public"],
        }
        
        overall_feasible = all(analysis.values())
        
        return {
            **analysis,
            "overall_feasible": overall_feasible,
            "feasibility_score": sum(analysis.values()) / len(analysis),
            "risk_level": "low" if overall_feasible else "medium"
        }
        
    async def generate_budget_recommendations(self, allocation: BudgetAllocation, 
                                            cost_estimates: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate budget recommendations"""
        recommendations = []
        
        if allocation.accommodation < cost_estimates["accommodation"]["budget"]:
            recommendations.append("Consider staying in hostels or budget accommodations to stay within budget")
            
        if allocation.food > cost_estimates["food"]["mid_range"]:
            recommendations.append("You have room for mid-range to upscale dining experiences")
            
        if allocation.activities < cost_estimates["activities"]["budget"]:
            recommendations.append("Look for free activities like parks, museums with free days, or walking tours")
            
        if len(recommendations) == 0:
            recommendations.append("Your budget allocation looks balanced for a comfortable trip")
            
        return recommendations
        
    async def suggest_adjustments(self, validation_results: Dict[str, Any]) -> List[str]:
        """Suggest budget adjustments"""
        adjustments = []
        
        for category, result in validation_results.items():
            if not result["within_budget"]:
                overspend = result["overspend"]
                adjustments.append(f"Reduce {category} spending by ${overspend:.2f}")
                
        return adjustments
        
    async def generate_optimization_suggestions(self, optimized_costs: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        
        for category, data in optimized_costs.items():
            if data["optimization_applied"]:
                savings = data["savings"]
                suggestions.append(f"Save ${savings:.2f} on {category} by choosing budget-friendly options")
                
        return suggestions
        
    async def estimate_attraction_cost(self, destination: str, attraction: str) -> float:
        """Estimate cost for specific attraction"""
        # Simulate cost estimation based on attraction type and destination
        base_costs = {
            "museum": 15,
            "park": 5,
            "monument": 10,
            "tour": 30,
            "activity": 25
        }
        
        multiplier = await self.get_destination_cost_multiplier(destination)
        attraction_type = "activity"  # Default, could be improved with classification
        
        return base_costs.get(attraction_type, 20) * multiplier
        
    async def estimate_restaurant_cost(self, destination: str, restaurant: str) -> float:
        """Estimate cost for restaurant meal"""
        multiplier = await self.get_destination_cost_multiplier(destination)
        base_meal_cost = 25  # Average meal cost
        
        return base_meal_cost * multiplier
        
    async def estimate_accommodation_cost(self, destination: str, accommodation: str) -> float:
        """Estimate accommodation cost per night"""
        multiplier = await self.get_destination_cost_multiplier(destination)
        base_accommodation_cost = 80  # Average per night
        
        return base_accommodation_cost * multiplier
        
    async def estimate_transport_cost(self, destination: str, transport: str) -> float:
        """Estimate transport cost"""
        multiplier = await self.get_destination_cost_multiplier(destination)
        
        transport_costs = {
            "public_transit": 5,
            "taxi": 20,
            "uber": 15,
            "rental_car": 40
        }
        
        return transport_costs.get(transport, 15) * multiplier
        
    async def get_destination_cost_multiplier(self, destination: str) -> float:
        """Get cost multiplier based on destination"""
        # Simulate cost level database
        cost_multipliers = {
            "paris": 1.3,
            "london": 1.4,
            "tokyo": 1.2,
            "bangkok": 0.6,
            "new york": 1.5,
            "berlin": 1.0,
            "rome": 1.1
        }
        
        return cost_multipliers.get(destination.lower(), 1.0)
        
    def load_cost_models(self) -> Dict[str, Any]:
        """Load cost prediction models"""
        # Placeholder for ML models
        return {
            "accommodation_model": None,
            "food_model": None,
            "activity_model": None,
            "transport_model": None
        }
