import streamlit as st
import google.generativeai as genai
import json

# --- 1. SETUP ---
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Missing API Key. Please add it to .streamlit/secrets.toml")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. SESSION STATE ---
if 'weekly_plan' not in st.session_state:
    st.session_state.weekly_plan = {}
if 'recipes' not in st.session_state:
    st.session_state.recipes = {}
if 'shopping_list' not in st.session_state:
    st.session_state.shopping_list = ""

# --- 3. HELPER FUNCTIONS ---

def generate_week_plan(user_schedule, special_requests):
    """
    The Architect: Plans ONLY for the days selected in user_schedule.
    """
    system_prompt = f"""
    You are a smart meal planner for a PESCATARIAN family.
    
    YOUR TASK:
    Create a cohesive meal plan ONLY for the days listed in the schedule below.
    
    INPUTS:
    1. SCHEDULE: {json.dumps(user_schedule)}
    2. REQUESTS: "{special_requests}"
    
    STRATEGY - ZERO WASTE:
    - Plan meals that share fresh ingredients across the selected days.
    
    DEFINITIONS:
    - "The Sprint": < 20 mins. High heat, stir fry, tacos.
    - "The Relay": Staggered eating. Slow Cooker, Casseroles, Soups.
    - "The Leisure": Complex cooking allowed.
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "DayName": "Meal Name | Prep Time | Brief Description",
        ...
    }}
    """
    try:
        response = model.generate_content(system_prompt)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"Planning Error: {e}")
        return {}

def generate_master_shopping_list(plan_json):
    prompt = f"""
    Look at this meal plan: 
    {json.dumps(plan_json)}
    
    TASK:
    Create a consolidated MASTER SHOPPING LIST.
    - Combine items (e.g. don't list 'Onion' twice, say '2 Onions').
    - Group by section (Produce, Pantry, Seafood, Dairy).
    """
    return model.generate_content(prompt).text

def generate_full_recipe(meal_summary):
    prompt = f"Write a full recipe for: {meal_summary}. Include Ingredients and Steps."
    return model.generate_content(prompt).text

# --- 4. SIDEBAR ---
st.set_page_config(page_title="Flexible Planner", page_icon="🗓️", layout="wide")

with st.sidebar:
    st.header("🗓️ Plan Your Week")
    st.info("🔒 Diet: **Pescatarian**")
    
    special_requests = st.text_area(
        "📝 Chef's Notes", 
        placeholder="e.g., 'Use up the spinach', 'Impossible burgers one night'...",
        height=100
    )
    
    st.divider()
    st.subheader("Select Days to Plan")
    
    # We define the possible days, but user chooses which to activate
    all_possible_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    user_schedule = {}
    
    for day in all_possible_days:
        # 1. The Checkbox (Default is checked for Mon-Fri, unchecked for Sat/Sun)
        is_active = st.checkbox(day, value=(day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]))
        
        # 2. If checked, show the Vibe Selector
        if is_active:
            user_schedule[day] = st.selectbox(
                f"{day} Logistics",
                options=["The Sprint (Quick)", "The Relay (Staggered)", "The Leisure (Complex)", "Takeout"],
                key=f"select_{day}"
            )

# --- 5. MAIN INTERFACE ---
st.title("🗓️ The Flexible Planner")

col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🚀 Plan Selected Days", type="primary"):
        if not user_schedule:
            st.warning("Please select at least one day in the sidebar!")
        else:
            with st.spinner("Chef is planning..."):
                st.session_state.recipes = {} 
                st.session_state.shopping_list = ""
                
                plan_data = generate_week_plan(user_schedule, special_requests)
                if plan_data:
                    st.session_state.weekly_plan = plan_data

with col2:
    if st.session_state.weekly_plan:
        if st.button("🛒 Generate Shopping List"):
            with st.spinner("Consolidating items..."):
                st.session_state.shopping_list = generate_master_shopping_list(st.session_state.weekly_plan)

# --- 6. DISPLAY SECTION ---

# Shopping List
if st.session_state.shopping_list:
    with st.expander("🛒 **VIEW SHOPPING LIST**", expanded=False):
        st.markdown(st.session_state.shopping_list)

# Day Cards
if st.session_state.weekly_plan:
    st.divider()
    
    # We use the keys from the PLAN, not the default list, to ensure order matches user selection
    planned_days = list(st.session_state.weekly_plan.keys())
    
    cols = st.columns(3)
    
    for i, day in enumerate(planned_days):
        col = cols[i % 3]
        with col:
            # Skip logic for Takeout if you want, or keep it to remind you
            if "Takeout" in user_schedule.get(day, ""):
                st.info(f"**{day}**: 🥡 Takeout")
                continue

            current_meal = st.session_state.weekly_plan[day]
            
            container = st.container(border=True)
            container.subheader(day)
            # Safe get in case day isn't in schedule (shouldn't happen but good practice)
            container.caption(user_schedule.get(day, "Custom"))
            container.write(current_meal)
            
            if container.button("👩‍🍳 Recipe", key=f"rec_{day}"):
                st.session_state.recipes[day] = generate_full_recipe(current_meal)
                st.rerun()
            
            if day in st.session_state.recipes:
                with container.expander("📖 View", expanded=True):
                    st.markdown(st.session_state.recipes[day])
