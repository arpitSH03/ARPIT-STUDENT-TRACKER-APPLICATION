import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime

# Constants for file storage
CSV_FILE = 'student_expenses.csv'
BUDGET_FILE = 'budget.txt'

# Predefined student-centric categories
CATEGORIES = [
    "College/Tuition Fees",
    "Hostel/Rent Accommodation",
    "Mess/Groceries/Food",
    "Books, Notes & Stationery",
    "Transport/Commute (Bus/Train/Fuel)",
    "Subscriptions (Spotify/Netflix, etc.)",
    "Canteen & Outings (Socializing)",
    "Emergency/Medical",
    "Miscellaneous/Other"
]

def load_data():
    """Load expense data from CSV file."""
    if not os.path.exists(CSV_FILE):
        # Create empty DataFrame with required columns if file doesn't exist
        df = pd.DataFrame(columns=['ID', 'Date', 'Amount', 'Description', 'Category'])
        df.to_csv(CSV_FILE, index=False)
        return df
    return pd.read_csv(CSV_FILE)

def save_data(df):
    """Save expense data to CSV file."""
    df.to_csv(CSV_FILE, index=False)

def load_budget():
    """Load the monthly budget limit."""
    if not os.path.exists(BUDGET_FILE):
        return 1000.0  # Default budget
    with open(BUDGET_FILE, 'r') as f:
        try:
            return float(f.read().strip())
        except ValueError:
            return 1000.0

def save_budget(amount):
    """Save the monthly budget limit."""
    with open(BUDGET_FILE, 'w') as f:
        f.write(str(amount))

def init_app():
    """Initialize Streamlit page configuration."""
    st.set_page_config(page_title="Student Expense Tracker", page_icon="🎓", layout="wide")

def main():
    # Only call set_page_config once at the start
    # Setting it in a helper function helps keep code clean
    
    st.title("🎓 Student Expense Tracker")
    
    # ---------------- Sidebar - Budget Setup ----------------
    st.sidebar.header("⚙️ Settings")
    current_budget = load_budget()
    
    with st.sidebar.form("budget_form"):
        st.subheader("Set Monthly Allowance")
        budget_input = st.number_input("Budget (₹)", min_value=0.0, value=current_budget, step=10.0)
        budget_submitted = st.form_submit_button("Update Budget")
        if budget_submitted:
            save_budget(budget_input)
            st.success("Budget updated successfully!")
            current_budget = budget_input
            
    # Load expense data
    df = load_data()
    
    # Convert 'Date' column to datetime safely for filtering
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
    
    # ---------------- Process Current Month Data ----------------
    now = datetime.datetime.now()
    current_month = now.month
    current_year = now.year
    
    if not df.empty:
        current_month_df = df[(df['Date'].dt.month == current_month) & (df['Date'].dt.year == current_year)]
    else:
        current_month_df = pd.DataFrame(columns=df.columns)
        
    total_expenses = current_month_df['Amount'].sum() if not current_month_df.empty else 0.0
    remaining_budget = current_budget - total_expenses
    
    # ---------------- Dashboard View ----------------
    st.header("📊 Dashboard")
    
    # KPI Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Expenses (This Month)", f"₹{total_expenses:,.2f}")
    with col2:
        st.metric("Monthly Budget", f"₹{current_budget:,.2f}")
    with col3:
        if remaining_budget < 0:
            st.metric("Remaining Budget", f"₹{remaining_budget:,.2f}", delta="Budget Exceeded!", delta_color="inverse")
            st.error("⚠️ Budget Exceeded! You have spent more than your monthly allowance.")
        else:
            st.metric("Remaining Budget", f"₹{remaining_budget:,.2f}", delta=f"Remaining", delta_color="normal")
            
    # Interactive Pie Chart
    if not current_month_df.empty and total_expenses > 0:
        st.subheader("Expenses Breakdown")
        category_totals = current_month_df.groupby('Category')['Amount'].sum().reset_index()
        fig = px.pie(
            category_totals, 
            values='Amount', 
            names='Category', 
            hole=0.4,
            title="Where your money went this month"
        )
        # Update chart layout for a cleaner look
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses recorded for this month yet. Add some below to see the chart!")
        
    st.divider()
    
    # ---------------- Add Expense Form ----------------
    st.header("➕ Add New Expense")
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.date.today())
            amount = st.number_input("Amount (₹)", min_value=0.01, format="%.2f")
        with col2:
            category = st.selectbox("Category", CATEGORIES)
            description = st.text_input("Description (Optional)")
            
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            new_id = int(df['ID'].max() + 1) if not df.empty else 1
            new_row = pd.DataFrame({
                'ID': [new_id],
                'Date': [pd.to_datetime(date)],
                'Amount': [amount],
                'Description': [description],
                'Category': [category]
            })
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success(f"Successfully added ₹{amount:.2f} for {category}!")
            st.rerun()

    st.divider()
    
    # ---------------- Recent Transactions ----------------
    st.header("📝 Recent Transactions")
    if not df.empty:
        # Sort by date descending
        df_sorted = df.sort_values(by='Date', ascending=False)
        recent_df = df_sorted.head(10)
        
        # Display as a table with delete buttons
        header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([2, 2, 3, 3, 1])
        header_col1.markdown("**Date**")
        header_col2.markdown("**Amount**")
        header_col3.markdown("**Category**")
        header_col4.markdown("**Description**")
        header_col5.markdown("**Action**")
        
        st.markdown("<hr style='margin: 0px; margin-bottom: 10px;'/>", unsafe_allow_html=True)
        
        for index, row in recent_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 3, 1])
            col1.write(row['Date'].strftime('%Y-%m-%d'))
            col2.write(f"₹{row['Amount']:,.2f}")
            col3.write(row['Category'])
            col4.write(row['Description'])
            
            # Delete functionality
            if col5.button("Delete", key=f"del_{row['ID']}"):
                # Remove the item
                df = df[df['ID'] != row['ID']]
                save_data(df)
                st.rerun()
                
    else:
        st.write("No transactions found.")

if __name__ == "__main__":
    init_app()
    main()
