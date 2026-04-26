import os
import sqlite3
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
load_dotenv()

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



# LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# System prompt
system_prompt = """You are a helpful data assistant. 
You have access to a business database with two tables: customers and orders.
Always check the table schema first if you're unsure about column names.
Generate clean SQL queries and explain the results clearly.
When filtering by text fields, always use LOWER() on both sides to handle case differences.
Example: WHERE LOWER(status) = LOWER('processing')"""


# Agent
agent = create_react_agent(llm, [query_database, get_table_schema, get_exchange_rate, get_weather], prompt=system_prompt)



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
