import streamlit as st
import pandas as pd
import base64

# --- Background Setup ---
def set_background(image_file):
    try:
        with open(image_file, 'rb') as f: data = f.read()
        bin_str = base64.b64encode(data).decode()
        st.markdown(f'''<style>.stApp {{ background-image: url("data:image/jpg;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }} .block-container {{ background-color: rgba(255, 255, 255, 0.92); padding: 2rem 3rem; border-radius: 15px; margin-top: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }} h1 {{ text-align: center; color: #1a1a1a; font-family: 'Serif'; }} .capacity-warning {{ background-color: #ff4b4b; color: white; padding: 1rem; border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 1rem; border: 2px solid white; }}</style>''', unsafe_allow_html=True)
    except: pass

set_background('Front.jpg')

# --- Header ---
st.title("Brettargh Holt Mansion Guest Allocation")
st.markdown("Automatic room assignment including Superior Double selection.")

# --- Configuration ---
st.write("### Select Configuration")
mode = st.radio("Hotel Capacity:", options=[(32, "Max 32 (2 Floors)"), (48, "Max 48 (3 Floors)")], format_func=lambda x: x[1], index=1)
guest_limit = mode[0]

uploaded_file = st.file_uploader("Upload Guest CSV", type="csv")
st.markdown("---")

if uploaded_file is not None:
    try:
        # Load Updated Room Inventory (with Superior labels)
        rooms_df = pd.read_csv('Untitled spreadsheet - Sheet1 (1).csv')
        guests_df = pd.read_csv(uploaded_file)
        
        def get_floor(n): return 0 if n <= 8 else (1 if n <= 16 else 2)
        rooms_df['Floor'] = rooms_df['Room #'].apply(get_floor)
        rooms_df = rooms_df.sort_values(by=['Floor', 'Room #']).reset_index(drop=True)
        
        if guest_limit == 32:
            rooms_df = rooms_df[rooms_df['Floor'] < 2].copy()
        
        rooms_df['Occupied'] = False
        rooms_df['Guest_Surname'] = "Empty"
        
        # Priority mapping: Superior requests are processed after Disabled but before Standard
        priority_map = {'Family': 1, 'Couple': 2, 'Single': 3}
        guests_df['Priority'] = guests_df['Guest Type'].map(priority_map)
        # Sort so Disabled and Superior requests are handled first
        guests_sorted = guests_df.sort_values(
            by=['Disabled Access Needed?', 'Superior Room?', 'Priority'], 
            ascending=[False, False, True]
        )

        for _, guest in guests_sorted.iterrows():
            # Match Logic
            if guest['Disabled Access Needed?'] == 'Yes':
                mask = rooms_df['Type'].str.contains('Disabled')
            elif guest['Superior Room?'] == 'Yes':
                mask = rooms_df['Type'] == 'Superior Double'
            elif guest['Guest Type'] == 'Family':
                mask = (rooms_df['Type'] == 'Family')
            elif guest.get('Willing to Share?') == 'Yes':
                mask = rooms_df['Type'].str.contains('Twin')
            else:
                mask = rooms_df['Type'].str.contains('Double')
            
            # Try to give them their preference
            potential = rooms_df[mask & (~rooms_df['Occupied'])]
            
            # Fallback: If no superior room left, give them any available room
            if potential.empty:
                potential = rooms_df[~rooms_df['Occupied']]
            
            if not potential.empty:
                idx = potential.index[0]
                rooms_df.at[idx, 'Occupied'] = True
                rooms_df.at[idx, 'Guest_Surname'] = guest['Surname']

        st.write(f"### Results for {mode[1]}")
        st.dataframe(rooms_df[['Room #', 'Room Name', 'Type', 'Floor', 'Guest_Surname']].sort_values(by='Room #'), use_container_width=True)
        st.download_button("Download Assignments", rooms_df.to_csv(index=False).encode('utf-8'), "Allocation.csv", "text/csv", use_container_width=True)
            
    except Exception as e:
        st.error(f"Error: {e}")
