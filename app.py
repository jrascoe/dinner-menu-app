import streamlit as st
import google.generativeai as genai

# --- 1. SETUP & CONFIGURATION ---

# PASTE YOUR API KEY HERE (Keep the quotes!)
# In a real deployed app, we would hide this, but for running locally this works.
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"] 

# Configure the AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. THE "BRAIN": YOUR PARAMETERS ---
# This is the secret sauce. The user won't see this, but the AI will obey it.
SYSTEM_INSTRUCTIONS = """
You are a specialized personal chef for a busy professional couple. 
You must create a dinner menu based on the ingredients provided.

STRICT PARAMETERS TO FOLLOW:
1. HEALTH: The meal must be generally healthy. Avoid deep-frying or heavy creams.
2. TIME: Total prep + cook time must be under 45 minutes.
3. PREFERENCE: If multiple options are possible, prioritize Mediterranean or Asian flavors.
4. FORMAT: 
   - Name of Dish
   - Estimated Time
   - Step-by-step instructions (keep them brief)
   - A "Missing Items" list if the user needs to buy 1-2 small things (like a lemon or herbs).
   
If the ingredients provided are truly impossible to make a meal with (e.g., just "ketchup and ice"), politely suggest ordering takeout.
"""

# --- 3. THE USER INTERFACE ---
st.set_page_config(page_title="The Dinner Decider", page_icon="🍽️")

st.title("🍽️ What's for Dinner?")
st.write("Enter the ingredients you have on hand. I'll handle the rest.")

# Two columns for a cleaner layout
col1, col2 = st.columns(2)

with col1:
    ingredients = st.text_area(
        "Ingredients available:", 
        placeholder="e.g., Chicken breast, spinach, half a lemon, rice...",
        height=150
    )

with col2:
    st.info("💡 **Tip:** You can also list leftovers or 'half a jar of salsa'.")
    dietary_override = st.checkbox("Vegetarian option only?", value=False)

# --- 4. THE LOGIC ---
if st.button("Generate Menu", type="primary"):
    if not ingredients:
        st.warning("Please enter at least one ingredient.")
    else:
        # We build the final prompt by combining your secret rules + user input
        final_prompt = f"{SYSTEM_INSTRUCTIONS}\n"
        
        if dietary_override:
            final_prompt += "\nUSER NOTE: The user requested this meal be Vegetarian, even if meat was listed.\n"
            
        final_prompt += f"\nUSER INGREDIENTS: {ingredients}"

        with st.spinner('Chef is thinking...'):
            try:
                response = model.generate_content(final_prompt)
                st.success("Here is your menu:")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"An error occurred: {e}")
