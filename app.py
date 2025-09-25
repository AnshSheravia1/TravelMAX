import streamlit as st
import asyncio
import json
from datetime import datetime
import plotly.express as px
import pandas as pd
from main import (
    run_travel_planner_sync, 
    PlannerState, 
    TripType, 
    BudgetRange,
    TravelPreferences
)
from langchain_core.messages import HumanMessage, AIMessage

# Page configuration
st.set_page_config(
    page_title="TravelMAX - AI-Powered Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🌍 TravelMAX - AI-Powered Trip Planner</h1>
    <p>Intelligent travel planning with real-time data integration and cost optimization</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_state" not in st.session_state:
        st.session_state.current_state = {}
    if "planning_history" not in st.session_state:
        st.session_state.planning_history = []
    if "performance_data" not in st.session_state:
        st.session_state.performance_data = []

initialize_session_state()

# Sidebar for advanced options
with st.sidebar:
    st.header("⚙️ Advanced Settings")
    
    # Trip type selection
    trip_type = st.selectbox(
        "Trip Type",
        options=[t.value for t in TripType],
        format_func=lambda x: x.title(),
        help="Select the type of trip you're planning"
    )
    
    # Budget range
    budget_range = st.selectbox(
        "Budget Range",
        options=[b.value for b in BudgetRange],
        format_func=lambda x: x.title(),
        help="Select your budget preference"
    )
    
    # Additional preferences
    st.subheader("Travel Preferences")
    transportation = st.multiselect(
        "Preferred Transportation",
        ["Walking", "Public Transit", "Taxi/Uber", "Rental Car", "Bicycle"],
        default=["Walking", "Public Transit"]
    )
    
    dietary_restrictions = st.multiselect(
        "Dietary Restrictions",
        ["None", "Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher"],
        default=["None"]
    )
    
    # Performance monitoring toggle
    show_metrics = st.checkbox("Show Performance Metrics", value=False)

# Main input section
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Trip Details")
    
    # Input fields in columns
    input_col1, input_col2 = st.columns(2)
    
    with input_col1:
        city = st.text_input("🏙️ Destination City", placeholder="e.g., Paris")
        country = st.text_input("🌍 Country", placeholder="e.g., France")
    
    with input_col2:
        duration = st.selectbox(
            "📅 Trip Duration",
            options=list(range(1, 15)),
            format_func=lambda x: f"{x} {'day' if x == 1 else 'days'}"
        )
        
        interests = st.text_input(
            "🎯 Interests", 
            placeholder="e.g., museums, food, nightlife, history",
            help="Comma-separated list of your interests"
        )

with col2:
    st.subheader("📊 Quick Stats")
    if st.session_state.current_state:
        state = st.session_state.current_state
        st.metric("Last Trip Duration", f"{state.get('duration', 0)} days")
        st.metric("Estimated Cost", f"${state.get('estimated_cost', 0):.2f}")
        st.metric("Processing Time", f"{state.get('performance_metrics', {}).get('total_processing_time', 0):.2f}s")

# Generate itinerary button
if st.button("🚀 Generate AI-Powered Itinerary", type="primary", use_container_width=True):
    if not city or not interests:
        st.error("⚠️ Please fill in both city and interests fields!")
    else:
        # Prepare the state
        initial_state = {
            "messages": [HumanMessage(content=f"I want to plan a {duration}-day {trip_type} trip to {city}, {country}.")],
            "city": city,
            "country": country or "Unknown",
            "interests": [interest.strip() for interest in interests.split(',')],
            "itinerary": "",
            "duration": duration,
            "trip_type": TripType(trip_type),
            "budget_range": BudgetRange(budget_range),
            "preferences": {
                "transportation": transportation,
                "dietary_restrictions": dietary_restrictions
            }
        }
        
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Input validation
            status_text.text("🔍 Validating input data...")
            progress_bar.progress(25)
            
            # Step 2: Data gathering
            status_text.text("🌤️ Gathering weather and events data...")
            progress_bar.progress(50)
            
            # Step 3: Itinerary generation
            status_text.text("🤖 Generating personalized itinerary...")
            progress_bar.progress(75)
            
            # Run the planner
            final_state = run_travel_planner_sync(initial_state)
            progress_bar.progress(100)
            status_text.text("✅ Itinerary generated successfully!")
            
            if final_state:
                st.session_state.current_state = final_state
                st.session_state.messages = final_state.get("messages", [])
                
                # Add to history
                st.session_state.planning_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "city": city,
                    "country": country,
                    "duration": duration,
                    "estimated_cost": final_state.get("estimated_cost", 0),
                    "trip_type": trip_type
                })
                
                # Store performance data
                if final_state.get("performance_metrics"):
                    st.session_state.performance_data.append(final_state["performance_metrics"])
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Display results
                if final_state.get('error_log'):
                    st.warning(f"⚠️ Some issues occurred: {', '.join(final_state['error_log'])}")
                
                if final_state.get('itinerary'):
                    if any(keyword in final_state['itinerary'] for keyword in ["Error", "Failed", "error"]):
                        st.error(final_state['itinerary'])
                    else:
                        # Success display
                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.success(f"✨ Your {duration}-Day {trip_type.title()} Trip to {city}, {country}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Display itinerary
                        st.markdown("---")
                        st.markdown(final_state["itinerary"])
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.download_button(
                                label="📥 Download Itinerary",
                                data=final_state["itinerary"],
                                file_name=f"itinerary_{city.lower().replace(' ', '_')}_{duration}_days.md",
                                mime="text/markdown"
                            )
                        
                        with col2:
                            if st.button("📊 View Analytics"):
                                st.session_state.show_analytics = True
                        
                        with col3:
                            if st.button("💾 Save to History"):
                                st.success("Saved to planning history!")
                else:
                    st.error("Failed to generate itinerary. Please try again.")
                    
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"An error occurred: {str(e)}")
            if st.checkbox("Show Detailed Error Information"):
                st.exception(e)

# Analytics Section
if show_metrics and st.session_state.performance_data:
    st.markdown("---")
    st.subheader("📈 Performance Analytics")
    
    # Convert performance data to DataFrame
    df = pd.DataFrame(st.session_state.performance_data)
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Processing time chart
            fig_time = px.line(
                df.reset_index(), 
                x='index', 
                y='total_processing_time',
                title="Processing Time Over Requests",
                labels={'index': 'Request Number', 'total_processing_time': 'Time (seconds)'}
            )
            st.plotly_chart(fig_time, use_container_width=True)
        
        with col2:
            # Performance metrics table
            st.write("**Latest Performance Metrics**")
            if df.shape[0] > 0:
                latest_metrics = df.iloc[-1]
                for metric, value in latest_metrics.items():
                    st.metric(metric.replace('_', ' ').title(), f"{value:.3f}s")

# Planning History
if st.session_state.planning_history:
    with st.expander("🗂️ Planning History"):
        history_df = pd.DataFrame(st.session_state.planning_history)
        st.dataframe(
            history_df[['timestamp', 'city', 'country', 'duration', 'estimated_cost', 'trip_type']], 
            use_container_width=True
        )
        
        if len(history_df) > 1:
            # Cost trend chart
            fig_cost = px.line(
                history_df.reset_index(), 
                x='index', 
                y='estimated_cost',
                title="Trip Cost Trends",
                labels={'index': 'Trip Number', 'estimated_cost': 'Cost ($)'}
            )
            st.plotly_chart(fig_cost, use_container_width=True)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🔧 Built with:**")
    st.markdown("- LangGraph for workflow orchestration")
    st.markdown("- Groq LLM for AI generation")
    
with col2:
    st.markdown("**📊 Features:**")
    st.markdown("- Real-time data integration")
    st.markdown("- Performance monitoring")
    
with col3:
    st.markdown("**💡 Advanced:**")
    st.markdown("- Async processing")
    st.markdown("- Cost optimization")

# System information in expander
with st.expander("🔍 System Information", expanded=False):
    st.json({
        "session_state_keys": list(st.session_state.keys()),
        "total_planning_requests": len(st.session_state.planning_history),
        "current_timestamp": datetime.now().isoformat(),
        "performance_tracking": bool(st.session_state.performance_data)
    })