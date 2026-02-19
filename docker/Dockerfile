FROM python:3.11

ENV PYTHONUNBUFFERED=1

# Upgrade pip
RUN pip install --upgrade pip

WORKDIR /opt

# Clone the repository
RUN git clone https://github.com/jc4v1/Kogi-Python.git

WORKDIR /opt/Kogi-Python

# Install python requirements and ensure voila is installed
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8866

# Start voila serving the requested notebook without opening a browser
CMD ["voila", "--no-browser", "--port=8866", "KogiApp.ipynb", "--Voila.ip='0.0.0.0'"]
