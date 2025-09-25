import os
import json
import asyncio
from typing import TypedDict, Annotated, List, Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class TripType(Enum):
    LEISURE = "leisure"
    BUSINESS = "business"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"

class BudgetRange(Enum):
    BUDGET = "budget"
    MODERATE = "moderate"
    LUXURY = "luxury"

@dataclass
class TravelPreferences:
    transportation: str
    accommodation_type: str
    dietary_restrictions: List[str]
    accessibility_needs: List[str]
    budget_range: BudgetRange

class PlannerState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], "The messages in the conversation"]
    city: str
    country: str
    interests: List[str]
    itinerary: str
    duration: int
    trip_type: TripType
    budget_range: BudgetRange
    preferences: Dict[str, Any]
    weather_info: Dict[str, Any]
    local_events: List[Dict[str, Any]]
    estimated_cost: float
    error_log: List[str]
    performance_metrics: Dict[str, float]

class TravelPlannerService:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_retries=3
        )
        self.performance_metrics = {}
        
    async def get_weather_data(self, city: str, country: str) -> Dict[str, Any]:
        """Simulate weather API call - in production, integrate with OpenWeatherMap"""
        try:
            # Simulate API response
            return {
                "temperature": "22°C",
                "condition": "Partly Cloudy",
                "forecast": "Pleasant weather expected",
                "best_time_to_visit": "Morning and evening"
            }
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            return {"error": str(e)}
    
    async def get_local_events(self, city: str, duration: int) -> List[Dict[str, Any]]:
        """Simulate events API call - in production, integrate with Eventbrite/local APIs"""
        try:
            # Simulate event data
            return [
                {
                    "name": f"Local Festival in {city}",
                    "date": "2024-12-01",
                    "type": "Cultural",
                    "price": "Free"
                }
            ]
        except Exception as e:
            logger.error(f"Events API error: {str(e)}")
            return []
    
    def calculate_estimated_cost(self, state: PlannerState) -> float:
        """Calculate estimated trip cost based on duration, city, and budget range"""
        try:
            base_cost_per_day = {
                BudgetRange.BUDGET: 50,
                BudgetRange.MODERATE: 150,
                BudgetRange.LUXURY: 400
            }
            
            city_multiplier = {
                "paris": 1.5, "london": 1.4, "tokyo": 1.3,
                "new york": 1.6, "bangkok": 0.7, "mumbai": 0.5
            }
            
            multiplier = city_multiplier.get(state['city'].lower(), 1.0)
            daily_cost = base_cost_per_day.get(state['budget_range'], 150)
            
            return round(daily_cost * state['duration'] * multiplier, 2)
        except Exception as e:
            logger.error(f"Cost calculation error: {str(e)}")
            return 0.0

# Initialize service
travel_service = TravelPlannerService()

# Enhanced prompt templates
itinerary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI travel planning assistant with expertise in creating personalized, detailed itineraries.

    Create a comprehensive {duration}-day trip itinerary for {city}, {country} based on:
    - User interests: {interests}
    - Trip type: {trip_type}
    - Budget range: {budget_range}
    - Weather info: {weather_info}
    - Local events: {local_events}
    - Estimated budget: ${estimated_cost}

    Structure your response as follows:
    
    # {duration}-Day {trip_type} Trip to {city}, {country}
    
    ## Trip Overview
    - **Budget Range**: {budget_range}
    - **Estimated Total Cost**: ${estimated_cost}
    - **Weather**: {weather_info}
    - **Best Times to Visit**: Based on weather and crowd patterns
    
    ## Daily Itinerary
    
    ### Day 1: [Theme]
    **Morning (9:00 AM - 12:00 PM)**
    - 🏛️ [Activity] - [Location] ($cost estimate)
      - Duration: X hours
      - Why visit: [Brief description]
      - Tips: [Practical advice]
    
    **Afternoon (12:00 PM - 5:00 PM)**
    - 🍽️ Lunch: [Restaurant] - [Cuisine type] ($cost)
    - 🎯 [Activity] - [Location] ($cost)
    
    **Evening (5:00 PM - 10:00 PM)**
    - 🌆 [Activity/Experience]
    - 🍽️ Dinner: [Restaurant recommendation]
    
    **Transportation**: [Daily transport method and cost]
    **Daily Budget**: $[amount]
    
    [Repeat for each day]
    
    ## Local Events & Special Experiences
    {local_events}
    
    ## Practical Information
    - **Getting Around**: Transportation options and costs
    - **Local Currency**: Exchange rates and payment methods
    - **Cultural Etiquette**: Important local customs
    - **Emergency Contacts**: Essential numbers
    - **Language Tips**: Key phrases
    
    ## Budget Breakdown
    - Accommodation: $[amount]
    - Transportation: $[amount]  
    - Food & Dining: $[amount]
    - Activities & Attractions: $[amount]
    - Shopping & Miscellaneous: $[amount]
    - **Total Estimated Cost**: ${estimated_cost}
    
    Make the itinerary personalized, practical, and engaging while staying within the specified budget range."""),
    ("human", "Create my personalized itinerary."),
])

# Enhanced node functions
async def validate_input(state: PlannerState) -> PlannerState:
    """Validate and enrich input data"""
    start_time = datetime.now()
    errors = []
    
    try:
        # Validation logic
        if not state.get('city'):
            errors.append("City is required")
        if not state.get('interests'):
            errors.append("Interests are required")
        if state.get('duration', 0) < 1:
            errors.append("Duration must be at least 1 day")
        
        # Set defaults
        if 'country' not in state:
            state['country'] = "Unknown"
        if 'trip_type' not in state:
            state['trip_type'] = TripType.LEISURE
        if 'budget_range' not in state:
            state['budget_range'] = BudgetRange.MODERATE
            
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            **state,
            "error_log": errors,
            "performance_metrics": {
                **state.get("performance_metrics", {}),
                "validation_time": processing_time
            }
        }
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            **state,
            "error_log": errors + [str(e)]
        }

async def gather_travel_data(state: PlannerState) -> PlannerState:
    """Gather weather and events data asynchronously"""
    start_time = datetime.now()
    
    try:
        # Gather data concurrently
        weather_task = travel_service.get_weather_data(state['city'], state['country'])
        events_task = travel_service.get_local_events(state['city'], state['duration'])
        
        weather_info, local_events = await asyncio.gather(weather_task, events_task)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            **state,
            "weather_info": weather_info,
            "local_events": local_events,
            "performance_metrics": {
                **state.get("performance_metrics", {}),
                "data_gathering_time": processing_time
            }
        }
    except Exception as e:
        logger.error(f"Data gathering error: {str(e)}")
        return {
            **state,
            "error_log": state.get("error_log", []) + [f"Data gathering failed: {str(e)}"]
        }

async def create_enhanced_itinerary(state: PlannerState) -> PlannerState:
    """Create detailed itinerary with cost estimation"""
    start_time = datetime.now()
    
    try:
        # Calculate estimated cost
        estimated_cost = travel_service.calculate_estimated_cost(state)
        
        # Prepare context for LLM
        context = {
            "city": state['city'],
            "country": state['country'],
            "interests": ", ".join(state['interests']),
            "duration": state['duration'],
            "trip_type": state.get('trip_type', TripType.LEISURE).value,
            "budget_range": state.get('budget_range', BudgetRange.MODERATE).value,
            "weather_info": json.dumps(state.get('weather_info', {})),
            "local_events": json.dumps(state.get('local_events', [])),
            "estimated_cost": estimated_cost
        }
        
        # Generate itinerary
        response = await asyncio.to_thread(
            lambda: travel_service.llm.invoke(
                itinerary_prompt.format_messages(**context)
            )
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if not response or not response.content:
            raise ValueError("Empty response from LLM")
        
        return {
            **state,
            "itinerary": response.content,
            "estimated_cost": estimated_cost,
            "messages": state.get('messages', []) + [AIMessage(content=response.content)],
            "performance_metrics": {
                **state.get("performance_metrics", {}),
                "itinerary_generation_time": processing_time,
                "total_processing_time": sum(state.get("performance_metrics", {}).values()) + processing_time
            }
        }
    except Exception as e:
        logger.error(f"Itinerary generation error: {str(e)}")
        error_message = f"Error generating itinerary: {str(e)}"
        return {
            **state,
            "itinerary": error_message,
            "error_log": state.get("error_log", []) + [error_message]
        }

# Build the enhanced graph
def build_travel_planner_graph():
    """Build and return the travel planner state graph"""
    graph = StateGraph(PlannerState)
    
    # Add nodes
    graph.add_node("validate_input", validate_input)
    graph.add_node("gather_travel_data", gather_travel_data)
    graph.add_node("create_enhanced_itinerary", create_enhanced_itinerary)
    
    # Define workflow
    graph.set_entry_point("validate_input")
    graph.add_edge("validate_input", "gather_travel_data")
    graph.add_edge("gather_travel_data", "create_enhanced_itinerary")
    graph.add_edge("create_enhanced_itinerary", END)
    
    return graph.compile()

# Initialize the compiled graph
app = build_travel_planner_graph()

async def run_travel_planner(state: PlannerState) -> PlannerState:
    """
    Run the enhanced travel planner with the given state.
    Returns the final state after processing with performance metrics.
    """
    try:
        logger.info(f"Starting enhanced travel planner with state: {state}")
        
        # Ensure state has all required fields with defaults
        default_state = {
            "messages": [],
            "city": "",
            "country": "",
            "interests": [],
            "itinerary": "",
            "duration": 1,
            "trip_type": TripType.LEISURE,
            "budget_range": BudgetRange.MODERATE,
            "preferences": {},
            "weather_info": {},
            "local_events": [],
            "estimated_cost": 0.0,
            "error_log": [],
            "performance_metrics": {}
        }
        
        # Merge with provided state
        final_state = {**default_state, **state}
        
        # Process through the graph
        async for output in app.astream(final_state):
            if isinstance(output, dict):
                for node_name, node_output in output.items():
                    if node_output and isinstance(node_output, dict):
                        final_state.update(node_output)
                        logger.info(f"Processed node: {node_name}")
        
        logger.info(f"Travel planner completed. Performance: {final_state.get('performance_metrics', {})}")
        return final_state
        
    except Exception as e:
        logger.error(f"Error in run_travel_planner: {str(e)}")
        error_message = f"System error: {str(e)}"
        return {
            **state,
            "itinerary": error_message,
            "error_log": [error_message]
        }

# Synchronous wrapper for backward compatibility
def run_travel_planner_sync(state: PlannerState) -> PlannerState:
    """Synchronous wrapper for the async travel planner"""
    return asyncio.run(run_travel_planner(state))
