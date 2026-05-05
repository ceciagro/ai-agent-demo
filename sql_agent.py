import os
import sqlite3
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Tools
@tool
def query_database(sql: str) -> str:
    """Execute a SQL query against the business database and return the results."""
    try:
        conn = sqlite3.connect("business.db")
        conn.create_function("LOWER", 1, str.lower)
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()

        if not results:
            return "No results found."

        rows = []
        for row in results:
            row_dict = {columns[i]: row[i] for i in range(len(columns))}
            rows.append(str(row_dict))
        return "\n".join(rows)

    except Exception as e:
        return f"Error executing query: {str(e)}"

@tool
def get_table_schema(table_name: str) -> str:
    """Get the schema of a table to understand its structure before querying."""
    try:
        conn = sqlite3.connect("business.db")
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        return str(columns)
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_exchange_rate(currency: str) -> str:
    """Get the current exchange rate for a currency against ARS (Argentine Peso)."""
    import requests
    try:
        response = requests.get("https://dolarapi.com/v1/dolares")
        data = response.json()
        
        for item in data:
            if item["casa"].lower() == currency.lower():
                return f"{item['casa']}: Buy ${item['compra']} - Sell ${item['venta']}"
        
        available = [item["casa"] for item in data]
        return f"Currency not found. Available: {', '.join(available)}"
    except Exception as e:
        return f"Error fetching exchange rate: {str(e)}"

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    import requests
    api_key = os.getenv("OPENWEATHER_API_KEY")
    try:
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": api_key,
                "units": "metric",
                "lang": "en"
            }
        )

        data = response.json()
        if data.get("cod") != 200:
            return f"City not found: {city}"
        
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        return f"{city}: {description}, {temp}°C, humidity {humidity}%"
    except Exception as e:
        return f"Error fetching weather: {str(e)}"
    
@tool
def get_bitcoin_price() -> str:
    """Get the current Bitcoin price in USD."""
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"},
            timeout=10
        )
        data = response.json()
        price = data["bitcoin"]["usd"]
        return f"Bitcoin current price: ${price:,.2f} USD"
    except Exception as e:
        return f"Error fetching Bitcoin price: {str(e)}"

@tool
def get_bitcoin_historical_price(date: str) -> str:
    """Get the Bitcoin price for a specific date. Date format: DD-MM-YYYY. Example: 10-04-2026."""
    from datetime import datetime, timedelta
    try:
        date_obj = datetime.strptime(date, "%d-%m-%Y")
        cutoff = datetime.now() - timedelta(days=365)
        
        if date_obj < cutoff:
            return f"Historical data is only available for the last 365 days. The earliest available date is {cutoff.strftime('%B %d, %Y')}."
        
        response = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/history",
            params={"date": date, "localization": False},
            timeout=10
        )
        data = response.json()
        price = data["market_data"]["current_price"]["usd"]
        return f"Bitcoin price on {date}: ${price:,.2f} USD"
    except Exception as e:
        return f"Error: {str(e)}"
    
# LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# System prompt
system_prompt = """You are a helpful data assistant. 
You have access to a business database with two tables: customers and orders.
Always check the table schema first if you're unsure about column names.
When filtering by text fields, always use LOWER() on both sides.
Example: WHERE LOWER(status) = LOWER('processing')
When using get_bitcoin_historical_price, always convert the date to DD-MM-YYYY format. For example, April 10 2025 = 10-04-2025."""


# Agent
agent = create_react_agent(llm, [query_database, get_table_schema, get_exchange_rate, get_weather, get_bitcoin_price, get_bitcoin_historical_price], prompt=system_prompt)



# Interactive loop
if __name__ == "__main__":
    print("SQL Agent ready! Ask me anything about the database.")
    print("Type 'exit' to quit.\n")
    
    conversation_history = []
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        
        conversation_history.append(HumanMessage(content=user_input))
        
        result = agent.invoke({
            "messages": conversation_history
        })
        
        conversation_history = result["messages"]
        print(f"Agent: {result['messages'][-1].content}\n")