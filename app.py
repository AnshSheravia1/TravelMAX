import streamlit as st
from main import run_travel_planner, PlannerState
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(
    page_title="TravelMAX - Day Trip Planner",
    page_icon="✈️",
    layout="wide"
)

st.title("TravelMAX - Trip Planner")
st.write("Plan your perfect trip!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_state" not in st.session_state:
    st.session_state.current_state = {
        "messages": [],
        "city": "",
        "interests": [],
        "itinerary": "",
        "duration": 1
    }

# Input fields
city = st.text_input("Enter the city you want to visit:")

# Trip duration selection
duration = st.selectbox(
    "How many days will you be staying?",
    options=[1, 2, 3, 4, 5, 6, 7],
    format_func=lambda x: f"{x} {'day' if x == 1 else 'days'}"
)

interests = st.text_input("Enter your interests (comma-separated):")

if st.button("Generate Itinerary"):
    if not city or not interests:
        st.error("Please fill in both city and interests fields!")
    else:
        # Create initial state with duration
        initial_state = {
            "messages": [HumanMessage(content=f"I want to plan a {duration}-day trip to {city}.")],
            "city": city,
            "interests": [interest.strip() for interest in interests.split(',')],
            "itinerary": "",
            "duration": duration
        }
        
        # Run the planner
        with st.spinner(f"Generating your {duration}-day itinerary..."):
            try:
                final_state = run_travel_planner(initial_state)
                if final_state:
                    # Handle nested state structure
                    if "create_itinerary" in final_state:
                        actual_state = final_state["create_itinerary"]
                    else:
                        actual_state = final_state
                        
                    st.session_state.current_state = actual_state
                    st.session_state.messages = actual_state.get("messages", [])
                
                if actual_state and actual_state.get('itinerary'):
                    if "Error" in actual_state['itinerary'] or "Failed" in actual_state['itinerary']:
                        st.error(actual_state['itinerary'])
                    else:
                        # Display the itinerary in a nice container
                        st.success(f"✨ Your {duration}-Day Trip Itinerary for {city}")
                        st.markdown("---")
                        st.markdown(actual_state["itinerary"])
                        
                        # Add a download button for the itinerary
                        st.download_button(
                            label="📥 Download Itinerary",
                            data=actual_state["itinerary"],
                            file_name=f"itinerary_{city.lower().replace(' ', '_')}_{duration}_days.txt",
                            mime="text/plain"
                        )
                else:
                    st.error("Failed to generate itinerary. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.error("Please try again with different inputs.")
                if st.checkbox("Show Detailed Error Information"):
                    st.exception(e)

# Display conversation history in an expander
#if st.session_state.messages:
#    with st.expander("📝 Conversation History"):
 #       for message in st.session_state.messages:
  #          if isinstance(message, HumanMessage):
   ##        else:
     #           st.write(f"🤖 Assistant: {message.content}")

# Debug information (only visible in development)
#if st.checkbox("Show Debug Information"):
 #   st.write("Current State:", st.session_state.current_state)
  #  st.write("Session State:", st.session_state)
   # if st.session_state.current_state and st.session_state.current_state.get('itinerary'):
    #    st.write("Itinerary Content:", st.session_state.current_state['itinerary']) 