# Carbon Sequestration Feasibility

A web application to analyze and visualize carbon sequestration potential across different geographical regions.

## Features
- Analyze carbon sequestration potential
- Interactive visualization of data
- Region-based analysis

## Prerequisites
- Python 3.x
- Docker (optional)

## Local Development Setup

### 1. Virtual Environment Setup
Create and activate a new virtual environment:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 3. Start the Server
```bash
fastapi dev app/app.py
```

The application will be available at `http://localhost:8000`

## Docker Deployment

### 1. Build the Docker Image
```bash
docker build -t runner .
```

### 2. Run the Container
```bash
docker run --env-file .env -p 80:80 runner
```

The application will be available at `http://localhost:80`

## Environment Variables
Make sure to create a `.env` file with the required environment variables before running the application.

## Contributing
Feel free to submit issues and pull requests.

## License
[MIT License](LICENSE)
