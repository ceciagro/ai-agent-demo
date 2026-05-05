#!/bin/bash
export $(cat .env | xargs)
python3 sql_agent.py