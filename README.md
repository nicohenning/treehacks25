# Carbon Sequestration Factibility
## How to run?
Create a new virtual env
```bash
python3 -m venv .venv
```
Activate your virtualenv
```bash
source .venv/bin/activate
```
Install the dependencies from the `requirements.txt` file
```bash
pip3 install -r requirements.txt
```
To initialize the server
```bash
fastapi dev app/app.py
```

## Creating Docker Image
```bash
docker build -t runner .
```
```bash
docker run -p 80:80 runner
```
