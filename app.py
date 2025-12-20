import streamlit as st
import google.generativeai as genai

# --- 1. SETUP ---
# Grab the key from the "Safe Box" (Secrets)
# Ensure your .streamlit/secrets.toml file has GOOGLE_API_KEY defined
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Missing API Key in secrets.toml")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. SESSION STATE (The Memory) ---
# This holds the menu so it doesn't vanish when you click buttons
if 'weekly_plan' not in st.session_state:
    st.session_state.weekly_plan = {}

# --- 3. CONFIGURATION ---
st.set_page_config(page_title="Weekly Logistics Planner", page_icon="📅", layout="wide")

st.title("📅 The Week Ahead")
st.markdown("""
**The Philosophy:** Don't plan based on what you *crave*. Plan based on *time and logistics*.
* **The Sprint:** Quick, 15-20 min meals. Everyone eats now.
* **The Relay:** Slow cooker or room-temp meals. People eat at different times.
* **The Leisure:** You have time to enjoy cooking (e.g., Sunday dinner).
""")

# --- 4. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Global Settings")
    st.info("🔒 Diet is hard-coded to: **Pescatarian**")
    
    # We store the "situations" for each day here
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    user_schedule = {}
    
    st.subheader("Schedule Your Week")
    for day in days:
        user_schedule[day] = st.selectbox(
            f"{day}'s Vibe:",
            options=["The Sprint (Quick)", "The Relay (Flexible Time)", "The Leisure (Complex)", "Takeout/Leftovers"],
            key=f"select_{day}"
        )

# --- 5. HELPER FUNCTIONS ---

def generate_single_meal(day, situation):
    """Asks AI for a single meal based on the specific situation."""
    
    # Hidden Chef Logic
    system_prompt = f"""
    You are a meal planner for a busy PESCATARIAN family.
    
    TASK: Create a dinner idea for {day}.
    CONTEXT: The logistics for this day are: '{situation}'.
    
    DEFINITIONS:
    - "The Sprint": Must take < 20 mins. High heat, stir fry, tacos, sheet pan.
    - "The Relay": Must allow staggered eating. Casseroles, Slow Cooker, Soup, or Salad that doesn't wilt.
    - "The Leisure": Complex, multi-step cooking is allowed.
    
    OUTPUT FORMAT:
    Return ONLY the meal details in this format:
    **Meal Name**
    *Time:* [Prep Time]
    *Why it fits:* [One sentence explanation]
    *Key Ingredients:* [List of 3-5 main items]
    """
    
    try:
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# --- 6. MAIN INTERFACE ---

# The Big "Generate Week" Button
if st.button("🚀 Plan My Whole Week", type="primary"):
    with st.spinner("Chef is reviewing your calendar..."):
        for day in days:
            situation = user_schedule[day]
            if "Takeout" in situation:
                st.session_state.weekly_plan[day] = "🥡 **Takeout / Leftovers Night**\n*Relax, you earned it.*"
            else:
                st.session_state.weekly_plan[day] = generate_single_meal(day, situation)

# Display the Cards
if st.session_state.weekly_plan:
    st.divider()
    
    # Create columns for a grid layout (3 columns per row looks good)
    cols = st.columns(3)
    
    for i, day in enumerate(days):
        # Determine which column to place this card in
        col = cols[i % 3]
        
        with col:
            # Check if we have a plan for this day
            if day in st.session_state.weekly_plan:
                current_meal = st.session_state.weekly_plan[day]
                
                # THE CARD UI
                container = st.container(border=True)
                container.subheader(f"{day}")
                container.caption(f"Logistics: {user_schedule[day]}")
                container.markdown(current_meal)
                
                # THE "REROLL" BUTTON
                # If the user clicks this, we ONLY regenerate this specific day
                if container.button(f"🔄 Change {day}", key=f"btn_reroll_{day}"):
                    with st.spinner(f"Rethinking {day}..."):
                        new_meal = generate_single_meal(day, user_schedule[day])
                        st.session_state.weekly_plan[day] = new_meal
                        st.rerun() # Refresh the page to show the new meal
