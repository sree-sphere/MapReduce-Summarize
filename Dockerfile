FROM python:3.11-slim
WORKDIR /app 

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
# Expose the port the app runs on
EXPOSE 8007

# Command to run the FastAPI application
CMD ["uvicorn", "src.endpoints:app", "--host", "0.0.0.0", "--port", "8009"]
