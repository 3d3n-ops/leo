#!/bin/bash

# Install Playwright browsers
playwright install --with-deps

# Start the application
uvicorn main:app --host 0.0.0.0 --port $PORT
