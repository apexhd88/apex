import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta

# Database Initialization
def init_database():
    conn = sqlite3.connect('flavorflow_erp.db')
    c = conn.cursor()
    
    # Create tables if not exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_name TEXT,
            product_name TEXT,
            quantity REAL,
            due_date TEXT,
            status TEXT,
            priority INTEGER
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY,
            material_name TEXT,
            current_stock REAL,
            unit TEXT,
            min_stock REAL,
            max_stock REAL
        )
    ''')
    
    conn.commit()
    conn.close()

# Sample Data Generation
def generate_sample_data():
    conn = sqlite3.connect('flavorflow_erp.db')
    c = conn.cursor()
    
    # Clear existing data
    c.execute('DELETE FROM orders')
    c.execute('DELETE FROM inventory')
    
    # Sample Inventory Materials
    materials = [
        ('Limonene (Natural)', 500, 'kg', 100, 1000),
        ('Orange Oil', 250, 'kg', 50, 500),
        ('Ethyl Butyrate', 100, 'kg', 20, 250),
        ('Propylene Glycol', 800, 'kg', 200, 1500)
    ]
    
    c.executemany('''
        INSERT INTO inventory 
        (material_name, current_stock, unit, min_stock, max_stock) 
        VALUES (?, ?, ?, ?, ?)
    ''', materials)
    
    # Sample Orders
    orders = [
        ('Beverage Co.', 'Citrus Flavor', 320, 
         (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'), 
         'Pending', 1),
        ('Personal Care Labs', 'Amber Woods Fragrance', 800, 
         (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d'), 
         'In Progress', 2),
        ('Dairy Desserts Inc.', 'Vanilla Cream', 500, 
         (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'), 
         'Pending', 1)
    ]
    
    c.executemany('''
        INSERT INTO orders 
        (customer_name, product_name, quantity, due_date, status, priority) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', orders)
    
    conn.commit()
    conn.close()

# Utility Functions
def get_orders():
    conn = sqlite3.connect('flavorflow_erp.db')
    df = pd.read_sql_query("SELECT * FROM orders", conn)
    conn.close()
    return df

def get_inventory():
    conn = sqlite3.connect('flavorflow_erp.db')
    df = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()
    return df

# Main Streamlit App
def main():
    st.set_page_config(page_title="FlavorFlow ERP", page_icon="🧪", layout="wide")
    
    # Initialize database
    init_database()
    generate_sample_data()
    
    # Sidebar Navigation
    st.sidebar.title("FlavorFlow ERP")
    menu = st.sidebar.radio("Navigation", [
        "Dashboard", 
        "Orders", 
        "Inventory", 
        "Production Planning"
    ])
    
    # Dashboard
    if menu == "Dashboard":
        st.title("Production Planning Dashboard")
        
        # KPI Columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Orders", len(get_orders()), "🛒")
        
        with col2:
            pending_orders = len(get_orders()[get_orders()['status'] == 'Pending'])
            st.metric("Pending Orders", pending_orders, "⏳")
        
        with col3:
            low_stock_items = len(get_inventory()[get_inventory()['current_stock'] < get_inventory()['min_stock']])
            st.metric("Low Stock Items", low_stock_items, "⚠️")
        
        with col4:
            st.metric("Production Capacity", "85%", "📊")
        
        # Order Status Visualization
        st.subheader("Order Status Overview")
        order_status = get_orders()['status'].value_counts()
        fig = px.pie(values=order_status.values, names=order_status.index, 
                     title="Order Status Distribution")
        st.plotly_chart(fig)
    
    # Orders Management
    elif menu == "Orders":
        st.title("Orders Management")
        
        # Display Orders
        orders_df = get_orders()
        st.dataframe(orders_df)
        
        # Create New Order
        st.subheader("Create New Order")
        with st.form("new_order_form"):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Customer Name")
                product_name = st.text_input("Product Name")
            
            with col2:
                quantity = st.number_input("Quantity", min_value=1)
                due_date = st.date_input("Due Date")
            
            priority = st.slider("Priority", 1, 5, 3)
            submit = st.form_submit_button("Create Order")
            
            if submit:
                conn = sqlite3.connect('flavorflow_erp.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO orders 
                    (customer_name, product_name, quantity, due_date, status, priority) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (customer_name, product_name, quantity, 
                      due_date.strftime('%Y-%m-%d'), 'Pending', priority))
                conn.commit()
                conn.close()
                st.success("Order Created Successfully!")
    
    # Inventory Management
    elif menu == "Inventory":
        st.title("Inventory Management")
        
        # Inventory Overview
        inventory_df = get_inventory()
        st.dataframe(inventory_df)
        
        # Stock Level Visualization
        st.subheader("Material Stock Levels")
        fig = px.bar(inventory_df, x='material_name', y='current_stock', 
                     color='current_stock', 
                     title="Current Stock Levels")
        st.plotly_chart(fig)
        
        # Low Stock Alerts
        low_stock = inventory_df[inventory_df['current_stock'] < inventory_df['min_stock']]
        if not low_stock.empty:
            st.warning("Low Stock Alerts:")
            st.dataframe(low_stock)
    
    # Production Planning
    elif menu == "Production Planning":
        st.title("Production Planning")
        
        # Scheduling Interface
        st.subheader("Production Schedule")
        orders_df = get_orders()
        
        # Simple Production Scheduling
        schedule_df = orders_df[orders_df['status'] == 'Pending'].copy()
        schedule_df['Estimated Start'] = pd.date_range(
            start=datetime.now(), 
            periods=len(schedule_df)
        )
        
        st.dataframe(schedule_df[['customer_name', 'product_name', 'quantity', 'Estimated Start']])
        
        # Capacity Planning Visualization
        st.subheader("Capacity Utilization")
        capacity_data = pd.DataFrame({
            'Area': ['Compounding', 'Filling'],
            'Utilization': [85, 70]
        })
        fig = px.bar(capacity_data, x='Area', y='Utilization', 
                     title="Production Line Capacity")
        st.plotly_chart(fig)

if __name__ == "__main__":
    main()
