import os
import sqlite3
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
import requests

load_dotenv()

# Tools
@tool
def query_database(sql: str) -> str:
    """Execute a SQL query against the business database and return the results."""
    try:
        conn = sqlite3.connect("/app/business.db")
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
def get_exchange_rate(currency: str) -> str:
    """Get the current exchange rate for a currency against ARS."""
    try:
        response = requests.get("https://dolarapi.com/v1/dolares")
        data = response.json()
        for item in data:
            if item["casa"].lower() == currency.lower():
                return f"{item['casa']}: Buy ${item['compra']} - Sell ${item['venta']}"
        available = [item["casa"] for item in data]
        return f"Currency not found. Available: {', '.join(available)}"
    except Exception as e:
        return f"Error: {str(e)}"

# Agent
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
system_prompt = """You are a helpful data assistant.
You have access to a business database with two tables: customers and orders.
Always check the table schema first if you're unsure about column names.
When filtering by text fields, always use LOWER() on both sides.
Example: WHERE LOWER(status) = LOWER('processing')"""

agent = create_react_agent(llm, [query_database, get_exchange_rate], prompt=system_prompt)

def handler(event, context):
    question = event.get("question", "")
    if not question:
        return {"statusCode": 400, "body": "No question provided"}
    
    result = agent.invoke({
        "messages": [HumanMessage(content=question)]
    })
    
    return {
        "statusCode": 200,
        "body": result["messages"][-1].content
    }