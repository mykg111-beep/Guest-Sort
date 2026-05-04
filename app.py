import streamlit as st
import pandas as pd

st.title("🏨 Hotel Guest Room Allocator")
st.markdown("Upload your guest list to automatically assign rooms based on priority.")

# 1. File Uploader for Guest CSV
uploaded_file = st.file_uploader("Choose your Guest CSV file", type="csv")

# 2. Select Booking Mode
mode = st.radio("Select Hotel Configuration:", (32, 48), index=1)

if uploaded_file is not None:
    # Load Room Inventory (Must be in same folder)
    rooms = pd.read_csv('Untitled spreadsheet - Sheet1 (1).csv')
    
    # Process allocation (Using our existing logic)
    def get_floor(n): return 0 if n <= 8 else (1 if n <= 16 else 2)
    rooms['Floor'] = rooms['Room #'].apply(get_floor)
    if mode == 32:
        rooms = rooms[rooms['Floor'] < 2].copy()
    
    rooms['Occupied'] = False
    rooms['Guest_Surname'] = "Empty"
    
    guests = pd.read_csv(uploaded_file)
    priority_map = {'Family': 1, 'Couple': 2, 'Single': 3}
    guests['Priority'] = guests['Guest Type'].map(priority_map)
    guests_sorted = guests.sort_values(by=['Disabled Access Needed?', 'Priority'], ascending=[False, True])

    for _, guest in guests_sorted.iterrows():
        # Match logic...
        mask = (rooms['Type'].str.contains('Disabled')) if guest['Disabled Access Needed?'] == 'Yes' else (rooms['Type'] == 'Family' if guest['Guest Type'] == 'Family' else rooms['Type'].str.contains('Double'))
        potential = rooms[mask & (~rooms['Occupied'])]
        if potential.empty: potential = rooms[~rooms['Occupied']]
        if not potential.empty:
            idx = potential.index[0]
            rooms.at[idx, 'Occupied'] = True
            rooms.at[idx, 'Guest_Surname'] = guest['Surname']

    # 3. Display and Download Result
    st.write("### ✅ Room Assignments")
    st.dataframe(rooms[['Room #', 'Room Name', 'Guest_Surname']])
    
    csv = rooms.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Final Allocation", data=csv, file_name="Final_Room_Assignments.csv", mime='text/csv')