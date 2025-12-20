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
    """The Architect: Plans ONLY for the days selected."""
    system_prompt = f"""
    You are a smart meal planner for a PESCATARIAN family.
    TASK: Create a cohesive meal plan ONLY for the days listed below.
    
    INPUTS:
    1. SCHEDULE: {json.dumps(user_schedule)}
    2. REQUESTS: "{special_requests}"
    
    STRATEGY:
    - Plan meals that share fresh ingredients across the selected days.
    - Ensure strictly Pescatarian (Fish/Veggie) meals.
    
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
    Look at this meal plan: {json.dumps(plan_json)}
    TASK: Create a consolidated MASTER SHOPPING LIST.
    - Combine items (e.g. '2 Onions').
    - Group by section (Produce, Pantry, Seafood).
    """
    return model.generate_content(prompt).text

def generate_full_recipe(meal_summary):
    prompt = f"Write a full recipe for: {meal_summary}. Include Ingredients and Steps."
    return model.generate_content(prompt).text

# --- 4. MOBILE CONFIGURATION ---
# Note: layout="centered" looks better on mobile than "wide"
st.set_page_config(page_title="Dinner App", page_icon="🥘", layout="centered")

# --- 5. SIDEBAR (SETTINGS) ---
# On mobile, this lives in the > arrow at the top left
with st.sidebar:
    st.header("⚙️ Setup")
    st.info("Diet: **Pescatarian**")
    
    special_requests = st.text_area("📝 Chef's Notes", height=80)
    
    st.subheader("Select Days")
    all_possible_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    user_schedule = {}
    
    for day in all_possible_days:
        # Default M-F checked
        default_check = day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        if st.checkbox(day, value=default_check):
            user_schedule[day] = st.selectbox(
                f"{day} Vibe",
                options=["Sprint (<20m)", "Relay (Staggered)", "Leisure (Slow)", "Takeout"],
                key=f"select_{day}"
            )

# --- 6. MAIN MOBILE INTERFACE ---

st.title("🥘 Dinner Plans")

# ACTION BUTTONS (Top of screen)
# We use full_width containers so buttons are easy to tap
if st.button("🚀 Plan Selected Days", type="primary", use_container_width=True):
    if not user_schedule:
        st.warning("Open the sidebar (top left) to select days!")
    else:
        with st.spinner("Planning..."):
            st.session_state.recipes = {} 
            st.session_state.shopping_list = ""
            plan_data = generate_week_plan(user_schedule, special_requests)
            if plan_data:
                st.session_state.weekly_plan = plan_data

if st.session_state.weekly_plan:
    if st.button("🛒 Create Shopping List", use_container_width=True):
        with st.spinner("Writing list..."):
            st.session_state.shopping_list = generate_master_shopping_list(st.session_state.weekly_plan)

# SHOPPING LIST DRAWER
if st.session_state.shopping_list:
    with st.expander("🛒 VIEW SHOPPING LIST", expanded=False):
        st.markdown(st.session_state.shopping_list)

# THE FEED (Vertical Scroll)
if st.session_state.weekly_plan:
    st.markdown("---")
    
    # We iterate through the planned days in order
    planned_days = list(st.session_state.weekly_plan.keys())
    
    for day in planned_days:
        # Visual Spacer
        
        # LOGIC: Check for takeout
        if "Takeout" in user_schedule.get(day, ""):
            st.info(f"**{day}**: 🥡 Takeout Night")
            continue

        # MEAL CARD
        current_meal = st.session_state.weekly_plan[day]
        
        with st.container(border=True):
            # Header
            st.subheader(day)
            st.caption(f"Strategy: {user_schedule.get(day)}")
            
            # Meal Description
            st.markdown(f"**{current_meal}**")
            
            # Recipe Toggle
            # If we don't have the recipe, show button. If we do, show content.
            if day not in st.session_state.recipes:
                if st.button(f"👩‍🍳 Get Recipe", key=f"btn_{day}", use_container_width=True):
                    st.session_state.recipes[day] = generate_full_recipe(current_meal)
                    st.rerun()
            else:
                st.markdown("---")
                st.markdown("##### 📖 Recipe")
                st.markdown(st.session_state.recipes[day])
                # Option to hide it or regenerate could go here
