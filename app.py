import streamlit as st
import pandas as pd
import base64

# --- Background Setup ---
def set_background(image_file):
    try:
        with open(image_file, 'rb') as f: data = f.read()
        bin_str = base64.b64encode(data).decode()
        st.markdown(f'''<style>.stApp {{ background-image: url("data:image/jpg;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }} .block-container {{ background-color: rgba(255, 255, 255, 0.96); padding: 2rem 3rem; border-radius: 15px; margin-top: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }} h1 {{ text-align: center; color: #1a1a1a; font-family: 'Serif'; font-weight: bold; }}</style>''', unsafe_allow_html=True)
    except: pass

set_background('Front.jpg')

# --- Header ---
st.title("Brettargh Holt Mansion Guest Allocation")
st.write("") # This keeps the area blank as requested

# --- Configuration ---
mode = st.radio("Hotel Capacity:", options=[(32, "Max 32 (2 Floors)"), (48, "Max 48 (3 Floors)")], format_func=lambda x: x[1], index=1)
guest_limit = mode[0]
uploaded_file = st.file_uploader("Upload Guest CSV", type="csv")

if uploaded_file is not None:
    try:
        # Load Inventory and apply labels
        rooms_df = pd.read_csv('Untitled spreadsheet - Sheet1 (1).csv')
        superior_rooms = [2, 7, 8, 10, 11]
        rooms_df.loc[rooms_df['Room #'].isin(superior_rooms), 'Type'] = 'Superior Double'
        
        def get_floor(n): return 0 if n <= 8 else (1 if n <= 16 else 2)
        rooms_df['Floor'] = rooms_df['Room #'].apply(get_floor)
        rooms_df = rooms_df.sort_values(by=['Floor', 'Room #']).reset_index(drop=True)
        
        if guest_limit == 32:
            rooms_df = rooms_df[rooms_df['Floor'] < 2].copy()
        
        rooms_df['Occupied'] = False
        rooms_df['Guest_Surname'] = "Empty"
        
        guests_df = pd.read_csv(uploaded_file)
        
        # Priority mapping
        priority_map = {'Family': 3, 'Couple': 4, 'Single': 5}
        guests_df['Base_Priority'] = guests_df['Guest Type'].map(priority_map)
        
        # Sort for precision allocation
        guests_sorted = guests_df.sort_values(
            by=['Disabled Access Needed?', 'Superior Room?', 'Base_Priority'], 
            ascending=[False, False, True]
        )

        for _, guest in guests_sorted.iterrows():
            potential = pd.DataFrame()
            
            # Step 1: Ideal Match
            if guest['Disabled Access Needed?'] == 'Yes':
                potential = rooms_df[(rooms_df['Type'].str.contains('Disabled')) & (~rooms_df['Occupied'])]
            elif guest['Superior Room?'] == 'Yes':
                potential = rooms_df[(rooms_df['Type'] == 'Superior Double') & (~rooms_df['Occupied'])]
            elif guest['Guest Type'] == 'Family':
                potential = rooms_df[(rooms_df['Type'] == 'Family') & (~rooms_df['Occupied'])]
            elif guest.get('Willing to Share?') == 'Yes':
                potential = rooms_df[(rooms_df['Type'].str.contains('Twin')) & (~rooms_df['Occupied'])]
            else:
                potential = rooms_df[(rooms_df['Type'] == 'Standard Double') & (~rooms_df['Occupied'])]

            # Step 2: Fallback
            if potential.empty:
                if guest['Guest Type'] in ['Couple', 'Single'] or guest['Superior Room?'] == 'Yes':
                    potential = rooms_df[(rooms_df['Type'].str.contains('Double')) & (~rooms_df['Occupied'])]
                
            # Step 3: Last Resort
            if potential.empty:
                potential = rooms_df[~rooms_df['Occupied']]
            
            if not potential.empty:
                idx = potential.index[0]
                rooms_df.at[idx, 'Occupied'] = True
                rooms_df.at[idx, 'Guest_Surname'] = guest['Surname']

        st.write(f"### Results for {mode[1]}")
        st.dataframe(rooms_df[['Room #', 'Room Name', 'Type', 'Floor', 'Guest_Surname']].sort_values(by='Room #'), use_container_width=True)
        st.download_button("Download Allocation", rooms_df.to_csv(index=False).encode('utf-8'), "Allocation.csv", "text/csv", use_container_width=True)
            
    except Exception as e:
        st.error(f"Error: {e}")
