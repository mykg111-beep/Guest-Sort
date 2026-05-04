import streamlit as st
import pandas as pd
import base64

# --- Function to Set Background (Uses Front.jpg) ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(image_file):
    bin_str = get_base64_of_bin_file(image_file)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{bin_str}");
        background-size: cover;
        background-attachment: fixed;
    }}
    
    /* Overlay for Readability */
    .block-container {{
        background-color: rgba(255, 255, 255, 0.90);
        padding: 2rem 3rem;
        border-radius: 15px;
        margin-top: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    
    h1 {{
        text-align: center;
        color: #1a1a1a;
        font-family: 'Serif';
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Attempt to set the background using Front.jpg
try:
    set_background('Front.jpg')
except FileNotFoundError:
    st.warning("Background image 'Front.jpg' not found. Please ensure it is in the same directory.")

# --- Updated Title ---
st.title("Brettargh Holt Mansion Guest Allocation")
st.markdown("Upload your guest list to automatically assign rooms based on priority.")

st.markdown("---")

# --- Simplified Configuration Selection ---
st.write("### Select Configuration")
mode = st.radio(
    "Choose the hotel capacity for this booking:",
    options=[(32, "Max 32 (2 Floors)"), (48, "Max 48 (3 Floors)")],
    format_func=lambda x: x[1],
    index=1
)

guest_limit = mode[0]

# --- File Uploader ---
uploaded_file = st.file_uploader("Upload Guest CSV File", type="csv")

st.markdown("---")

if uploaded_file is not None:
    try:
        # Load internal room inventory
        rooms_df = pd.read_csv('Untitled spreadsheet - Sheet1 (1).csv')
        guests_df = pd.read_csv(uploaded_file)
        
        # Floor logic
        def get_floor(n): return 0 if n <= 8 else (1 if n <= 16 else 2)
        rooms_df['Floor'] = rooms_df['Room #'].apply(get_floor)
        
        # Apply capacity filter
        if guest_limit == 32:
            rooms_df = rooms_df[rooms_df['Floor'] < 2].copy()
        else:
            rooms_df = rooms_df.copy()
            
        rooms_df['Occupied'] = False
        rooms_df['Guest_Surname'] = "Empty"
        
        # Priority logic
        priority_map = {'Family': 1, 'Couple': 2, 'Single': 3}
        guests_df['Priority'] = guests_df['Guest Type'].map(priority_map)
        guests_sorted = guests_df.sort_values(
            by=['Disabled Access Needed?', 'Priority'], 
            ascending=[False, True]
        )

        for _, guest in guests_sorted.iterrows():
            if guest['Disabled Access Needed?'] == 'Yes':
                mask = (rooms_df['Type'].str.contains('Disabled'))
            elif guest['Guest Type'] == 'Family':
                mask = (rooms_df['Type'] == 'Family')
            elif guest['Willing to Share?'] == 'Yes':
                mask = (rooms_df['Type'].str.contains('Twin'))
            else:
                mask = (rooms_df['Type'].str.contains('Double'))
            
            potential = rooms_df[mask & (~rooms_df['Occupied'])]
            if potential.empty:
                potential = rooms_df[~rooms_df['Occupied']]
            
            if not potential.empty:
                idx = potential.index[0]
                rooms_df.at[idx, 'Occupied'] = True
                rooms_df.at[idx, 'Guest_Surname'] = guest['Surname']

        # --- Results Display ---
        st.write(f"### {mode[1]} Results")
        st.dataframe(
            rooms_df[['Room #', 'Room Name', 'Type', 'Floor', 'Guest_Surname']].sort_values(by='Room #'),
            use_container_width=True
        )
        
        csv_data = rooms_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Room Assignments",
            data=csv_data,
            file_name="Brettargh_Holt_Allocation.csv",
            mime='text/csv',
            use_container_width=True
        )
            
    except Exception as e:
        st.error(f"Error processing files: {e}")
