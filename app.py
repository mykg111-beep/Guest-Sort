import streamlit as st
import pandas as pd
import base64

# --- Function to Set Background (Requires image_0.png as background.jpg in repo) ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{bin_str}");
        background-size: cover;
    }}
    
    /* Overlay for Readability */
    .block-container {{
        background-color: rgba(255, 255, 255, 0.85);
        padding: 2rem 3rem !rem;
        border-radius: 10px;
    }}
    
    /* Center the title */
    h1 {{
        text-align: center;
        color: #2c3e50; /* Adjust color as needed */
    }}
    
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Try to set background (handles case where image is missing locally)
try:
    set_background('background.jpg') # <-- Download the provided image and save it as background.jpg
except FileNotFoundError:
    st.warning("Background image not found. Ensure 'background.jpg' is in the repository.")


# --- MAIN APP TITLE (UPDATED) ---
st.title("🏰 Brettargh Holt Mansion Guest Allocation")
st.markdown("Upload your guest list below to automatically assign rooms based on priority and availability.")

st.markdown("---") # Visual separator

# --- Uploader Section ---
uploaded_file = st.file_uploader("📂 Choose your Guest CSV file", type="csv")

# --- Configuration Mode ---
st.write("### ⚙️ Select Configuration:")
# Updated radio label and options
mode = st.radio(
    "Choose your booked plan:", 
    options=[(32, "Ground & First Floors Only (Max 32 Guests)"), 
             (48, "All 3 Floors (Max 48 Guests)")],
    format_func=lambda x: x[1], # Display the friendly text
    index=1 # Default to 48 guests
)

# Extract just the numerical limit (32 or 48)
guest_limit = mode[0]


st.markdown("---") # Visual separator

# --- Logic and Output ---
if uploaded_file is not None:
    try:
        # Load Room Inventory (Must be 'Untitled spreadsheet - Sheet1 (1).csv' in repo)
        rooms_df = pd.read_csv('Untitled spreadsheet - Sheet1 (1).csv')
        
        # Load Guests from Upload
        guests_df = pd.read_csv(uploaded_file)
        
        # Basic validation
        required_cols = ['Surname', 'Guest Type', 'Disabled Access Needed?', 'Willing to Share?']
        if not all(col in guests_df.columns for col in required_cols):
            st.error(f"Upload Error: Your CSV must contain these columns: {', '.join(required_cols)}")
        else:
            # --- Allocation Logic ---
            
            # Floor assignment logic (Rooms 1-8: 0, 9-16: 1, 17+: 2)
            def get_floor(n): return 0 if n <= 8 else (1 if n <= 16 else 2)
            rooms_df['Floor'] = rooms_df['Room #'].apply(get_floor)
            
            # Apply guest plan filter
            if guest_limit == 32:
                rooms_df = rooms_df[rooms_df['Floor'] < 2].copy()
            else:
                rooms_df = rooms_df.copy()
            
            rooms_df['Occupied'] = False
            rooms_df['Guest_Surname'] = "Empty"
            
            # Priority mapping
            priority_map = {'Family': 1, 'Couple': 2, 'Single': 3}
            guests_df['Priority'] = guests_df['Guest Type'].map(priority_map)
            # Sort by Disability priority first, then guest type
            guests_sorted = guests_df.sort_values(
                by=['Disabled Access Needed?', 'Priority'], 
                ascending=[False, True]
            )

            for _, guest in guests_sorted.iterrows():
                # 1. Match based on disability
                if guest['Disabled Access Needed?'] == 'Yes':
                    mask = (rooms_df['Type'].str.contains('Disabled'))
                # 2. Match Family
                elif guest['Guest Type'] == 'Family':
                    mask = (rooms_df['Type'] == 'Family')
                # 3. Match Single Sharers
                elif guest['Willing to Share?'] == 'Yes':
                    mask = (rooms_df['Type'].str.contains('Twin'))
                # 4. Standard match (Couple or Solo Single)
                else:
                    mask = (rooms_df['Type'].str.contains('Double'))
                
                # Filter for matching rooms that aren't occupied
                potential = rooms_df[mask & (~rooms_df['Occupied'])]
                
                # Fallback: if no priority room is free, use ANY free room
                if potential.empty:
                    potential = rooms_df[~rooms_df['Occupied']]
                
                if not potential.empty:
                    idx = potential.index[0]
                    rooms_df.at[idx, 'Occupied'] = True
                    rooms_df.at[idx, 'Guest_Surname'] = guest['Surname']

            # --- Display Result ---
            st.write("### ✅ Final Room Allocation")
            st.write(f"Showing allocation for: {mode[1]} mode.")
            
            # Display sorted by Room #
            st.dataframe(
                rooms_df[['Room #', 'Room Name', 'Type', 'Floor', 'Guest_Surname']].sort_values(by='Room #'),
                use_container_width=True
            )
            
            # Prepare Download Button
            csv = rooms_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download This Allocation (CSV)",
                data=csv,
                file_name=f"{guest_limit}_Guest_Allocation.csv",
                mime='text/csv',
                use_container_width=True
            )
            
            st.success("Allocation processed! You can download the results above.")
            
    except Exception as e:
        st.error(f"An error occurred during processing: {e}")
else:
    st.info("Upload your guest list CSV to begin the allocation process.")
