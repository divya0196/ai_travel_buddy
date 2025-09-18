import asyncio
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.master_coordinator import MasterCoordinatorAgent
from models.data_models import TripRequest, TravelItinerary
from config import config

# FastAPI app
app = FastAPI(
    title="AI Weekend Travel Buddy",
    description="Multi-agent system for generating personalized 2-day travel itineraries",
    version="1.0.0"
)

# Global coordinator instance
coordinator: Optional[MasterCoordinatorAgent] = None

class TripPlanRequest(BaseModel):
    destination: str
    budget: float
    interests: Optional[List[str]] = []
    dietary_restrictions: Optional[List[str]] = []
    accommodation_type: Optional[str] = "hotel"
    transport_preference: Optional[str] = "public"

class TripPlanResponse(BaseModel):
    success: bool
    itinerary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the multi-agent system"""
    global coordinator
    coordinator = MasterCoordinatorAgent()
    await coordinator.start()
    print("🤖 AI Weekend Travel Buddy started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the multi-agent system"""
    global coordinator
    if coordinator:
        await coordinator.stop()
    print("🛑 AI Weekend Travel Buddy stopped")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Weekend Travel Buddy is running!",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    global coordinator
    
    agent_status = {}
    if coordinator:
        for agent_name, agent in coordinator.agents.items():
            agent_status[agent_name] = {
                "active": agent.is_active,
                "capabilities": agent.capabilities
            }
    
    return {
        "status": "healthy" if coordinator and coordinator.is_active else "unhealthy",
        "coordinator_active": coordinator.is_active if coordinator else False,
        "agents": agent_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/plan-trip", response_model=TripPlanResponse)
async def plan_trip(request: TripPlanRequest):
    """Generate a 2-day travel itinerary"""
    global coordinator
    
    if not coordinator or not coordinator.is_active:
        raise HTTPException(status_code=503, detail="Travel buddy system not available")
    
    try:
        # Create trip request
        trip_request = TripRequest(
            destination=request.destination,
            budget=request.budget,
            duration_days=2,
            interests=request.interests,
            dietary_restrictions=request.dietary_restrictions,
            accommodation_type=request.accommodation_type,
            transport_preference=request.transport_preference
        )
        
        # Generate itinerary
        start_time = datetime.now()
        result = await coordinator.process_request(trip_request.dict())
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if result.get("success"):
            return TripPlanResponse(
                success=True,
                itinerary=result["itinerary"],
                processing_time=f"{processing_time:.2f} seconds"
            )
        else:
            return TripPlanResponse(
                success=False,
                error=result.get("error", "Unknown error occurred"),
                processing_time=f"{processing_time:.2f} seconds"
            )
            
    except Exception as e:
        print(f"Error planning trip: {str(e)}")
        return TripPlanResponse(
            success=False,
            error=f"Failed to generate itinerary: {str(e)}"
        )

@app.get("/destinations")
async def get_popular_destinations():
    """Get list of popular destinations"""
    return {
        "popular_destinations": [
            {"name": "Paris", "country": "France", "cost_level": "High"},
            {"name": "Tokyo", "country": "Japan", "cost_level": "Medium-High"},
            {"name": "Rome", "country": "Italy", "cost_level": "Medium"},
            {"name": "Bangkok", "country": "Thailand", "cost_level": "Low"},
            {"name": "Berlin", "country": "Germany", "cost_level": "Medium"},
            {"name": "London", "country": "UK", "cost_level": "High"},
            {"name": "Barcelona", "country": "Spain", "
