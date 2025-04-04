import streamlit as st
import mysql.connector
import pandas as pd

st.title("RETAIL ORDERS ANALYSIS")


def get_connection():
    return mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="bBdMPga4tbKX2G8.root",
        password="7BDg7rhupeZAdIok",
        database="PROJECT",
    )

queries = {
    "1.Find top 10 highest revenue generating products": """
        SELECT od.sub_category, SUM(od.quantity * od.discount_price) AS total_revenue
        FROM orderlast od 
        GROUP BY od.sub_category 
        ORDER BY total_revenue DESC 
        LIMIT 10;""",
   
    "2.Find the top 5 cities with the highest profit margins": """SELECT orderfirst.city, SUM(orderlast.profit) AS total_profit
        FROM orderfirst
        JOIN orderlast ON orderfirst.order_id = orderlast.order_id
        GROUP BY orderfirst.city
        ORDER BY total_profit DESC
        LIMIT 5;""",
    
    "3.Calculate the total discount given for each category": """SELECT category, SUM(discount_price) AS total_discount
        FROM PROJECT.orderlast
        GROUP BY category;""",
    
    "4.Find the average sale price per product category": """
        SELECT category, AVG(sale_price) AS average_sale_price
        FROM orderlast
        GROUP BY category;""",
    
    "5.Find the region with the highest average sale price": """SELECT f.region, AVG(l.sale_price) AS averagesale_price
        FROM orderfirst f
        JOIN orderlast AS l ON f.order_id = l.order_id
        GROUP BY f.region
        ORDER BY AVG(l.sale_price) DESC;""",
    
    "6.Find the total profit per category": """SELECT category, SUM(profit) AS total_profit
        FROM orderlast
        GROUP BY category;""",
    
    "7.Identify the top 3 segments with the highest quantity of orders": """SELECT f.segment, SUM(l.quantity) AS total_quantity
        FROM orderfirst f
        JOIN orderlast l ON f.order_id = l.order_id
        GROUP BY f.segment
        ORDER BY total_quantity DESC;""",
    
    "8.Determine the average discount percentage given per region": """SELECT f.region, AVG(l.discount_percent) AS average_discount_percentage
        FROM orderfirst f
        JOIN orderlast l ON f.order_id = l.order_id
        GROUP BY f.region;""",  
    
    "9.Find the product category with the highest total profit": """SELECT category, SUM(profit) AS total_profit
        FROM orderlast
        GROUP BY category
        ORDER BY total_profit DESC;""",     
  
    "10.Calculate the total revenue generated per year": """SELECT YEAR(orderfirst.order_date) AS year, SUM(orderlast.sale_price) AS total_revenue
        FROM orderfirst
        JOIN orderlast ON orderfirst.order_id = orderlast.order_id
        GROUP BY YEAR(orderfirst.order_date);""",
    
    "11.Find top 5 states with highest profit": """SELECT f.state, SUM(l.profit) AS total_profit
        FROM orderfirst f
        JOIN orderlast l ON f.order_id = l.order_id
        GROUP BY f.state
        ORDER BY total_profit DESC LIMIT 5;""",
    
    "12.Find the total orders done by First Class, Second Class, and Standard Class in ship mode": """SELECT orderfirst.ship_mode, COUNT(*) AS Total_Orders
        FROM orderfirst
        WHERE orderfirst.ship_mode IN ('First Class', 'Second Class', 'Standard Class')
        GROUP BY orderfirst.ship_mode
        ORDER BY Total_Orders ASC;""",
    
    "13.Find the top 3 months with the highest total sales":"""SELECT MONTH(f.order_date) AS month, SUM(l.sale_price) AS total_sales
        FROM orderfirst f
        JOIN orderlast l ON f.order_id = l.order_id
        GROUP BY MONTH(f.order_date)
        ORDER BY total_sales DESC
        LIMIT 3;""",

    "14.Find the top 4 states with highest orders":"""SELECT state, COUNT(order_id) AS total_orders
        FROM orderfirst
        GROUP BY state
        ORDER BY total_orders DESC
        LIMIT 4;""",
    
    "15.Calculate the total discount amount per region":"""SELECT f.region, SUM(l.discount_price) AS total_discount_given
        FROM orderfirst f
        JOIN orderlast l ON f.order_id = l.order_id
        GROUP BY f.region
        ORDER BY total_discount_given DESC;""",
    
    "16.List the customer segment with the highest total quantity of orders":"""SELECT f.segment, SUM(l.quantity) AS total_quantity
        FROM orderfirst f
        JOIN orderlast l ON f.order_id = l.order_id
        GROUP BY f.segment
        ORDER BY total_quantity DESC;""",
    
    "17.Find the average profit per order for shipping mode(First,Second and Standard class)":"""SELECT f.ship_mode, AVG(l.profit) AS avg_profit_per_order
        FROM orderfirst f
        JOIN orderlast l ON f.order_id = l.order_id
        WHERE f.ship_mode IN ('First Class', 'Second Class', 'Standard Class')
        GROUP BY f.ship_mode
        ORDER BY avg_profit_per_order DESC;""",

    "18.Find the top 5 cities with the highest total number of orders":"""SELECT city, COUNT(order_id) AS total_orders
        FROM orderfirst
        GROUP BY city
        ORDER BY total_orders DESC
        LIMIT 5;""",

    "19.Find the most frequently ordered product category":"""SELECT category, SUM(quantity) AS total_quantity
        FROM orderlast
        GROUP BY category
        ORDER BY total_quantity DESC
        LIMIT 3;""",

    "20.Find the total profit per product sub-category":"""SELECT sub_category, SUM(profit) AS total_profit
        FROM orderlast
        GROUP BY sub_category
        ORDER BY total_profit DESC;"""
}                                                  

query_keys = list(queries.keys())
left_queries = query_keys[:10]  
right_queries = query_keys[10:] 

st.sidebar.title("Query Selection")
menu = st.sidebar.radio("SELECT BETWEEN:", ["GIVEN 10 QUERIES", "ADDITIONAL 10 QUERIERS"])
if menu == "GIVEN 10 QUERIES":
    selected_query_name = st.sidebar.selectbox("Select a Query", left_queries)
elif menu == "ADDITIONAL 10 QUERIERS":
    selected_query_name = st.sidebar.selectbox("Select a Query", right_queries)

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

        
        st.code(selected_query, language="sql")  
        df = pd.DataFrame(data, columns=columns)
        st.dataframe(df) 
