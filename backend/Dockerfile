# backend/Dockerfile

# 1. Use a modern, slim Python base
FROM python:3.11-slim

# 2. Set the working directory
WORKDIR /app

# 3. Install uv
RUN pip install uv

# 4. Copy requirements file and install dependencies
# This is done first to leverage Docker's layer caching
COPY requirements.txt requirements.txt
# --- THIS LINE IS UPDATED ---
RUN uv pip install --system --no-cache-dir -r requirements.txt

# 5. Copy the application source code
COPY ./src /app/src

# 6. Expose the port the app runs on
EXPOSE 8000

# 7. The command to run the application
# Use --host 0.0.0.0 to make it accessible outside the container
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]