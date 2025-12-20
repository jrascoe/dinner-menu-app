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

# --- SECTION A: SETUP (Stacked at Top) ---
# We use an expander that defaults to expanded=True so it's visible on load
with st.expander("⚙️ WEEKLY SETUP (Click to Hide/Show)", expanded=True):
    st.info("Diet: **Pescatarian**")
    
    special_requests = st.text_area("📝 Chef's Notes", height=70, placeholder="e.g. Impossible burgers one night")
    
    st.markdown("##### Schedule")
    
    all_possible_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    user_schedule = {}
    
    for day in all_possible_days:
        # Create two columns per day row to save vertical space
        # Col 1 = Checkbox (Day Name), Col 2 = Dropdown (Vibe)
        c1, c2 = st.columns([1.5, 2.5])
        
        with c1:
            # Default M-F checked
            default_check = day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            is_active =
