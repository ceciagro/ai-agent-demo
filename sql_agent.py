import os
import sqlite3
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_community.callbacks import get_openai_callback
from langgraph.prebuilt import create_react_agent

# Tools
@tool
def query_database(sql: str) -> str:
    """Run a SQL query on the business DB and return results."""
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
    """Get column details for a table (use only if schema is unclear)."""
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
    """Get exchange rate for a currency vs ARS. E.g. 'oficial', 'blue', 'crypto'."""
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
    """Get current weather for a city."""
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
    """Get current Bitcoin price in USD."""
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
    """Get Bitcoin price for a past date (last 365 days). Date format: DD-MM-YYYY."""
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

DB SCHEMA:
- customers(id INTEGER, name TEXT, email TEXT, city TEXT)
- orders(id INTEGER, customer_id INTEGER, product TEXT, amount REAL, status TEXT, date TEXT)

Rules:
- Use LOWER() on both sides for text filters: WHERE LOWER(status) = LOWER('processing')
- For get_bitcoin_historical_price use DD-MM-YYYY format
- Only call get_table_schema if you need details not shown above"""


# Agent
agent = create_react_agent(llm, [query_database, get_table_schema, get_exchange_rate, get_weather, get_bitcoin_price, get_bitcoin_historical_price], prompt=system_prompt)



MAX_HISTORY_TURNS = 6  # keep last N human+assistant message pairs

def trim_history(messages, max_turns):
    """Keep only the last max_turns of human/assistant exchanges, dropping intermediate tool messages."""
    from langchain_core.messages import HumanMessage, AIMessage
    clean = [(i, m) for i, m in enumerate(messages) if isinstance(m, (HumanMessage, AIMessage)) and not getattr(m, "tool_calls", None)]
    if len(clean) > max_turns * 2:
        cutoff_idx = clean[-(max_turns * 2)][0]
        return messages[cutoff_idx:]
    return messages

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

        with get_openai_callback() as cb:
            result = agent.invoke({
                "messages": conversation_history
            })
        print(f"Agent: {result['messages'][-1].content}\n")
        print(f"[tokens] in={cb.prompt_tokens} out={cb.completion_tokens} total={cb.total_tokens} cost=${cb.total_cost:.4f}\n")

        conversation_history = trim_history(result["messages"], MAX_HISTORY_TURNS)