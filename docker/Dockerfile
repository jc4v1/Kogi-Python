FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone the repo (keeps build reproducible without sending context)
RUN git clone https://github.com/jc4v1/Kogi-Python.git .

# Upgrade pip and build wheels for all requirements
RUN pip install --no-cache-dir pip -r requirements.txt

EXPOSE 8866

# Start voila (bind to all interfaces inside container)
CMD ["voila", "--no-browser", "--port=8866", "KogiApp.ipynb", "--Voila.ip=0.0.0.0"]
