FROM katemaher/crunchflow:optimized210
WORKDIR /app
RUN apt-get update && apt-get install -y python3-venv
RUN python3 -m venv venv
COPY requirements.txt .
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 80
CMD ["uvicorn", "main.app:app", "--host", "0.0.0.0", "--port", "80"]
