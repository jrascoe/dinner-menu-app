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
    The Architect: Plans the week with ingredient efficiency in mind.
    """
    system_prompt = f"""
    You are a smart meal planner for a PESCATARIAN family.
    
    YOUR TASK:
    Create a cohesive meal plan for Monday - Friday.
    
    INPUTS:
    1. SCHEDULE: {json.dumps(user_schedule)}
    2. REQUESTS: "{special_requests}"
    
    STRATEGY - ZERO WASTE:
    - Plan meals that share fresh ingredients (e.g., if Monday uses half a bunch of cilantro, use the rest on Thursday).
    - Ensure ingredients are practical (don't buy a whole jar of spice for 1 tsp).
    
    DEFINITIONS:
    - "The Sprint": < 20 mins. High heat, stir fry, tacos.
    - "The Relay": Staggered eating. Slow Cooker, Casseroles, Soups.
    - "The Leisure": Complex cooking allowed.
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "Monday": "Meal Name | Prep Time | Brief Description (mentioning reused ingredients if applicable)",
        "Tuesday": "...",
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
    """Reads the whole week and creates one organized list."""
    prompt = f"""
    Look at this weekly meal plan: 
    {json.dumps(plan_json)}
    
    TASK:
    Create a consolidated MASTER SHOPPING LIST.
    - Combine items (e.g. don't list 'Onion' twice, say '2 Onions').
    - Group by section (Produce, Pantry, Seafood, Dairy).
    - Exclude common staples (Salt, Pepper, Oil).
    """
    return model.generate_content(prompt).text

def generate_full_recipe(meal_summary):
    prompt = f"Write a full recipe for: {meal_summary}. Include Ingredients and Steps."
    return model.generate_content(prompt).text

# --- 4. SIDEBAR ---
st.set_page_config(page_title="Zero Waste Planner", page_icon="♻️", layout="wide")

with st.sidebar:
    st.header("♻️ Zero Waste Planner")
    st.info("🔒 Diet: **Pescatarian**")
    
    special_requests = st.text_area(
        "📝 Chef's Notes", 
        placeholder="e.g., 'Use up the big bag of carrots', 'Impossible burgers one night'...",
        height=100
    )
    
    st.divider()
    st.subheader("The Schedule")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    user_schedule = {}
    for day in days:
        user_schedule[day] = st.selectbox(
            f"{day}",
            options=["The Sprint (Quick)", "The Relay (Staggered)", "The Leisure (Complex)", "Takeout"],
            key=f"select_{day}"
        )

# --- 5. MAIN INTERFACE ---
st.title("📅 The Week Ahead")

col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🚀 Plan Week (Optimize Ingredients)", type="primary"):
        with st.spinner("Chef is checking prices and expiration dates..."):
            st.session_state.recipes = {} 
            st.session_state.shopping_list = "" # Clear old list
            
            plan_data = generate_week_plan(user_schedule, special_requests)
            if plan_data:
                st.session_state.weekly_plan = plan_data

with col2:
    # Button to generate shopping list ONLY if plan exists
    if st.session_state.weekly_plan:
        if st.button("🛒 Generate Shopping List"):
            with st.spinner("Consolidating items..."):
                st.session_state.shopping_list = generate_master_shopping_list(st.session_state.weekly_plan)

# --- 6. DISPLAY SECTION ---

# If we have a shopping list, show it at the very top (toggleable)
if st.session_state.shopping_list:
    with st.expander("🛒 **VIEW MASTER SHOPPING LIST**", expanded=False):
        st.markdown(st.session_state.shopping_list)

# Display Day Cards
if st.session_state.weekly_plan:
    st.divider()
    cols = st.columns(3)
    
    for i, day in enumerate(days):
        col = cols[i % 3]
        with col:
            if "Takeout" in user_schedule[day]:
                st.info(f"**{day}**: 🥡 Takeout / Leftovers")
                continue

            if day in st.session_state.weekly_plan:
                current_meal = st.session_state.weekly_plan[day]
                
                # Card
                container = st.container(border=True)
                container.subheader(day)
                container.caption(user_schedule[day])
                container.write(current_meal)
                
                # Recipe Button
                if container.button("👩‍🍳 Recipe", key=f"rec_{day}"):
                    st.session_state.recipes[day] = generate_full_recipe(current_meal)
                    st.rerun()
                
                # Show Recipe
                if day in st.session_state.recipes:
                    with container.expander("📖 View", expanded=True):
                        st.markdown(st.session_state.recipes[day])
