# Dockerfile to install and run a development environment for the project
# Will run in localstack container

FROM python:3.10-slim

WORKDIR /app

# Copy the local_setup.py script
COPY local_setup.py .

# Copy lambda functions directory
COPY lambda lambda

COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Sleep for 10 seconds to allow localstack to start 
# and then run the local_setup.py script
# Then sleep to keep the container running
CMD sleep 5 && python local_setup.py && sleep infinity