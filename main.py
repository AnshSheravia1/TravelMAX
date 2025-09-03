import os
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv('GROQ_API_KEY')

class PlannerState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], "The messages in the conversation"]
    city: str
    interests: List[str]
    itinerary: str
    duration: int

llm = ChatGroq(model="llama-3.1-8b-instant")

itinerary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful travel assistant. Create a detailed {duration}-day trip itinerary for {city} based on the user's interests: {interests}.
    
    Please structure your response in the following format:
    
    # {duration}-Day Trip Itinerary for {city}
    
    ## Day 1
    ### Morning
    - [Time] Activity 1
    - [Time] Activity 2
    
    ### Afternoon
    - [Time] Activity 3
    - [Time] Activity 4
    
    ### Evening
    - [Time] Activity 5
    - [Time] Activity 6
    
    ### Food & Dining
    - [Time] Restaurant/Cafe recommendation
    - [Time] Restaurant/Cafe recommendation
    
    [Repeat the above structure for each day]
    
    ## Additional Tips
    - Tip 1
    - Tip 2
    
    Make sure to:
    1. Include specific locations, addresses, and estimated times for each activity
    2. Consider travel time between locations
    3. Group activities by area to minimize travel
    4. Include a mix of popular attractions and local experiences
    5. Consider opening hours and best times to visit each location
    - 6. Include a variety of dining options that match the user's interests
    - 7. Add practical tips for getting around the city
    
    For multi-day trips, ensure activities are logically grouped and consider:
    - Starting with major attractions on the first day
    - Grouping activities by neighborhood/area
    - Including some flexibility in the schedule
    - Suggesting evening activities for each day
    - Including a mix of indoor and outdoor activities
    - Considering weather-appropriate activities"""),
    ("human", "Create an itinerary for my trip."),
])

def input_city(state: PlannerState) -> PlannerState:
    return {
        "messages": state.get('messages', []) + [HumanMessage(content=f"I want to visit {state['city']}")],
        "city": state.get('city', ''),
        "interests": state.get('interests', []),
        "itinerary": state.get('itinerary', ''),
        "duration": state.get('duration', 1)
    }

def input_interests(state: PlannerState) -> PlannerState:
    return {
        "messages": state.get('messages', []) + [HumanMessage(content=f"My interests are: {', '.join(state['interests'])}")],
        "city": state.get('city', ''),
        "interests": state.get('interests', []),
        "itinerary": state.get('itinerary', ''),
        "duration": state.get('duration', 1)
    }

def create_itinerary(state: PlannerState) -> PlannerState:
    try:
        print(f"Generating {state.get('duration', 1)}-day itinerary for {state['city']} with interests: {state['interests']}")
        response = llm.invoke(itinerary_prompt.format_messages(
            city=state['city'],
            interests=", ".join(state['interests']),
            duration=state.get('duration', 1)
        ))
        
        if not response or not response.content:
            print("Empty response from LLM")
            return {
                "messages": state.get('messages', []) + [AIMessage(content="Failed to generate itinerary. The AI model returned an empty response.")],
                "city": state.get('city', ''),
                "interests": state.get('interests', []),
                "itinerary": "Failed to generate itinerary. The AI model returned an empty response.",
                "duration": state.get('duration', 1)
            }
        
        print(f"LLM Response: {response.content[:100]}...")  # Print first 100 chars of response
        
        return {
            "messages": state.get('messages', []) + [AIMessage(content=response.content)],
            "city": state.get('city', ''),
            "interests": state.get('interests', []),
            "itinerary": response.content,
            "duration": state.get('duration', 1)
        }
    except Exception as e:
        print(f"Error in create_itinerary: {str(e)}")
        error_message = f"Error generating itinerary: {str(e)}"
        return {
            "messages": state.get('messages', []) + [AIMessage(content=error_message)],
            "city": state.get('city', ''),
            "interests": state.get('interests', []),
            "itinerary": error_message,
            "duration": state.get('duration', 1)
        }

graph = StateGraph(PlannerState)

graph.add_node("input_city", input_city)
graph.add_node("input_interests", input_interests)
graph.add_node("create_itinerary", create_itinerary)

graph.set_entry_point("input_city")

graph.add_edge("input_city", "input_interests")
graph.add_edge("input_interests", "create_itinerary")
graph.add_edge("create_itinerary", END)

app = graph.compile()

def run_travel_planner(state: PlannerState):
    """
    Run the travel planner with the given state.
    Returns the final state after processing.
    """
    try:
        # Ensure state has all required fields
        if not isinstance(state, dict):
            state = {}
        
        if "messages" not in state:
            state["messages"] = []
        if "city" not in state:
            state["city"] = ""
        if "interests" not in state:
            state["interests"] = []
        if "itinerary" not in state:
            state["itinerary"] = ""
        if "duration" not in state:
            state["duration"] = 1

        print(f"Starting travel planner with state: {state}")
        
        # Process the state through the graph
        final_state = None
        for output in app.stream(state):
            if isinstance(output, dict):
                # If the output is nested under create_itinerary, extract it
                if "create_itinerary" in output:
                    final_state = output["create_itinerary"]
                elif "__end__" in output:
                    final_state = output["__end__"]
                else:
                    final_state = output
                print(f"Updated state: {final_state}")
        
        # Ensure we have an itinerary
        if final_state and isinstance(final_state, dict):
            if "itinerary" in final_state and final_state["itinerary"]:
                return final_state
            elif "messages" in final_state:
                # Extract itinerary from the last AI message
                for message in reversed(final_state["messages"]):
                    if isinstance(message, AIMessage) and message.content:
                        final_state["itinerary"] = message.content
                        return final_state
        
        # If we get here, something went wrong
        error_message = "Unable to generate itinerary. Please try again."
        return {
            "messages": state.get('messages', []) + [AIMessage(content=error_message)],
            "city": state.get('city', ''),
            "interests": state.get('interests', []),
            "itinerary": error_message,
            "duration": state.get('duration', 1)
        }
    except Exception as e:
        print(f"Error in run_travel_planner: {str(e)}")
        error_message = f"An error occurred: {str(e)}"
        return {
            "messages": state.get('messages', []) + [AIMessage(content=error_message)],
            "city": state.get('city', ''),
            "interests": state.get('interests', []),
            "itinerary": error_message,
            "duration": state.get('duration', 1)
        }
