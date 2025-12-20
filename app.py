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

def generate_single_meal_fix(day, situation):
    """Regenerates just ONE day's meal."""
    prompt = f"""
    Create a single PESCATARIAN dinner idea for {day}.
    Logistics: {situation}.
    Format: Meal Name | Prep Time | Why it fits.
    """
    try:
        return model.generate_content(prompt).text
    except:
        return "Error generating meal."

def generate_master_shopping_list(plan_json):
    prompt = f"""
    Look at this meal plan: {json.dumps(plan_json)}
    TASK: Create a consolidated MASTER SHOPPING LIST.
    - Group by section (Produce, Pantry, Seafood).
    """
    return model.generate_content(prompt).text

def generate_full_recipe(meal_summary):
    prompt = f"Write a full recipe for: {meal_summary}. Include Ingredients and Steps."
    return model.generate_content(prompt).text

# --- 4. APP CONFIGURATION ---
st.set_page_config(page_title="Dinner App", page_icon="🍽️", layout="centered")

# --- 5. MAIN INTERFACE ---

st.title("🍽️ Dinner Plans")

# --- SECTION A: SETUP ---
with st.expander("⚙️ WEEKLY SETUP (Click to Hide/Show)", expanded=True):
    st.info("Diet: **Pescatarian**")
    
    special_requests = st.text_area("📝 Chef's Notes", height=70, placeholder="e.g. Impossible burgers one night")
    
    st.markdown("##### Schedule")
    
    all_possible_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    user_schedule = {}
    
    for day in all_possible_days:
        c1, c2 = st.columns([1.5, 2.5])
        
        with c1:
            default_check = day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            is_active = st.checkbox(day, value=default_check)
            
        with c2:
            if is_active:
                user_schedule[day] = st.selectbox(
                    "Logistics",
                    options=["Sprint (<20m)", "Relay (Staggered)", "Leisure (Slow)", "Takeout"],
                    key=f"select_{day}",
                    label_visibility="collapsed"
                )

# --- SECTION B: ACTIONS ---
st.markdown("---") 

if st.button("🚀 PLAN SELECTED DAYS", type="primary", use_container_width=True):
    if not user_schedule:
        st.warning("Please select at least one day above.")
    else:
        with st.spinner("Chef is planning..."):
            st.session_state.recipes = {} 
            st.session_state.shopping_list = ""
            plan_data = generate_week_plan(user_schedule, special_requests)
            if plan_data:
                st.session_state.weekly_plan = plan_data

if st.session_state.weekly_plan:
    if st.button("🛒 Create Shopping List", use_container_width=True):
        with st.spinner("Writing list..."):
            st.session_state.shopping_list = generate_master_shopping_list(st.session_state.weekly_plan)

# --- SECTION C: RESULTS ---

# SHOPPING LIST DRAWER
if st.session_state.shopping_list:
    with st.expander("🛒 VIEW SHOPPING LIST", expanded=False):
        st.markdown(st.session_state.shopping_list)
        st.caption("Copy list below:")
        st.code(st.session_state.shopping_list, language=None)

# FEED
if st.session_state.weekly_plan:
    st.write("") 
    
    planned_days = list(st.session_state.weekly_plan.keys())
    
    for day in planned_days:
        if "Takeout" in user_schedule.get(day, ""):
            st.info(f"**{day}**: 🥡 Takeout Night")
            continue

        current_meal = st.session_state.weekly_plan[day]
        
        with st.container(border=True):
            st.subheader(day)
            st.caption(f"Strategy: {user_schedule.get(day)}")
            st.markdown(f"**{current_meal}**")
            
            # CONTROL ROW (Swap | Recipe)
            col_swap, col_recipe = st.columns(2)
            
            # 1. SWAP BUTTON
            if col_swap.button("🔄 Swap", key=f"swap_{day}", use_container_width=True):
                # Clear recipe if existed
                if day in st.session_state.recipes: 
                    del st.session_state.recipes[day]
                # Regenerate just this day
                with st.spinner("Rethinking..."):
                    st.session_state.weekly_plan[day] = generate_single_meal_fix(day, user_schedule.get(day))
                    st.rerun()

            # 2. RECIPE BUTTON
            # If no recipe loaded, show "Get Recipe"
            if day not in st.session_state.recipes:
                if col_recipe.button(f"👩‍🍳 Recipe", key=f"btn_{day}", use_container_width=True):
                    st.session_state.recipes[day] = generate_full_recipe(current_meal)
                    st.rerun()
            
            # 3. RECIPE DISPLAY (If loaded)
            if day in st.session_state.recipes:
                st.markdown("---")
                st.markdown("##### 📖 Recipe")
                st.markdown(st.session_state.recipes[day])
                
                st.divider()
                st.caption("👇 Tap icon to copy:")
                st.code(st.session_state.recipes[day], language=None)
