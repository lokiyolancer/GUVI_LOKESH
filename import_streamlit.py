import streamlit as st
import mysql.connector
import pandas as pd

st.title("RETAIL ORDERS ANALYSIS")

# ✅ Database Connection Function
def get_connection():
    return mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="bBdMPga4tbKX2G8.root",
        password="7BDg7rhupeZAdIok",
        database="PROJECT",
    )

# ✅ Define Queries BEFORE Using Them
queries = {
    "Find top 10 highest revenue generating products": """
        SELECT od.sub_category, SUM(od.quantity * od.discount_price) AS total_revenue
        FROM orderlast od 
        GROUP BY od.sub_category 
        ORDER BY total_revenue DESC 
        LIMIT 10;""",
   
    "Find the top 5 cities with the highest profit margins": """SELECT orderfirst.city, SUM(orderlast.profit) AS total_profit
        FROM orderfirst
        JOIN orderlast ON orderfirst.order_id = `orderlast`.`order_id`
        GROUP BY orderfirst.city
        ORDER BY total_profit DESC
        LIMIT 5;""",
    
    "Calculate the total discount given for each category": """SELECT category, SUM(discount_price) AS total_discount
        FROM PROJECT.orderlast
        GROUP BY category;""",
    
    "Find the average sale price per product category": """
        SELECT category, AVG(sale_price) AS average_sale_price
        FROM orderlast
        GROUP BY category;""",
    
    "Find the region with the highest average sale price": """SELECT f.region, AVG(l.sale_price) AS averagesale_price
        FROM orderfirst f
        JOIN orderlast AS l ON f.order_id = l.order_id
        GROUP BY f.region
        ORDER BY AVG(l.sale_price) DESC;""",
    
    "Find the total profit per category": """SELECT category, SUM(profit) AS total_profit
        FROM orderlast
        GROUP BY category;""",
    
    "Identify the top 3 segments with the highest quantity of orders": """SELECT f.segment, SUM(l.quantity) AS total_quantity
        FROM orderfirst f
        JOIN orderlast l ON f.order_id = l.order_id
        GROUP BY f.segment
        ORDER BY total_quantity DESC;""",
    
    "Determine the average discount percentage given per region": """SELECT f.region, AVG(l.discount_percent) AS average_discount_percentage
        FROM orderfirst f
        JOIN orderlast l ON f.order_id = l.order_id
        GROUP BY f.region;""",  
    
    "Find the product category with the highest total profit": """SELECT category, SUM(profit) AS total_profit
        FROM orderlast
        GROUP BY category
        ORDER BY total_profit DESC;""",     
  
    "Calculate the total revenue generated per year": """SELECT YEAR(orderfirst.order_date) AS year, SUM(orderlast.sale_price) AS total_revenue
        FROM orderfirst
        JOIN orderlast ON orderfirst.order_id = orderlast.order_id
        GROUP BY YEAR(orderfirst.order_date);""",
    
    "Find total profit by top 5 states": """SELECT orderfirst.state, SUM(ol.profit) AS total_profit
        FROM orderfirst 
        JOIN orderlast ol ON orderfirst.order_id = ol.order_id
        GROUP BY orderfirst.state
        ORDER BY total_profit DESC LIMIT 5;""",
    
    "Find the total orders done by First Class, Second Class, and Standard Class in ship mode": """SELECT orderfirst.ship_mode, COUNT(*) AS Total_Orders
        FROM orderfirst
        WHERE orderfirst.ship_mode IN ('First Class', 'Second Class', 'Standard Class')
        GROUP BY orderfirst.ship_mode
        ORDER BY Total_Orders ASC;"""
}                                                  

# ✅ Query Selection
query_keys = list(queries.keys())
left_queries = query_keys[:6]  # First 6 queries for Left Side
right_queries = query_keys[6:]  # Next 6 queries for Right Side

# ✅ Create Sidebar Menu
st.sidebar.title("Query Selection")

menu = st.sidebar.radio("Choose a Query Type:", ["FIRST 10 QUERY", "LAST 10 QUERY"])

if menu == "Left Side Queries":
    selected_query_name = st.sidebar.selectbox("Select a Query", left_queries)
elif menu == "Right Side Queries":
    selected_query_name = st.sidebar.selectbox("Select a Query", right_queries)

# ✅ Execute and Display Query
if selected_query_name:
    selected_query = queries[selected_query_name]
    
    with st.spinner("Executing Query..."):
        connection = get_connection()
        mycursor = connection.cursor()
        mycursor.execute(selected_query)
        data = mycursor.fetchall()
        columns = [desc[0] for desc in mycursor.description]

        mycursor.close()
        connection.close()

        # ✅ Display SQL Query & DataFrame
        st.code(selected_query, language="sql")  # Show SQL query
        df = pd.DataFrame(data, columns=columns)
        st.dataframe(df)  # Show result as a table
