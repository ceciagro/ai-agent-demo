# AI SQL Agent with LangGraph

A conversational AI agent that queries a business database using natural language, built with LangGraph and OpenAI.

## Features

- Natural language to SQL queries
- Conversational memory across questions
- Real-time exchange rate (dolarapi.com)
- Real-time weather data (OpenWeatherMap)
- Case-insensitive query handling

## Tech Stack

- Python 3.11
- LangGraph
- LangChain
- OpenAI GPT-3.5
- SQLite

## Setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Set environment variables
5. Run the agent

## Installation

```bash
git clone https://github.com/ceciagro/ai-agent-demo
cd ai-agent-demo
python3 -m venv venv
source venv/bin/activate
pip install langchain langchain-openai langgraph requests
