FROM python:3.9.16

# Install some basic utilities.
# SHELL ["/bin/bash", "--login", "-c"]
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    sudo \
    git \
    bzip2 \
    libx11-6 \
    build-essential \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

 # Create a working directory.
RUN mkdir /app
WORKDIR /app

COPY . /app/
RUN pip install -r requirements.txt

CMD ["hypercorn", "main:app", "--bind", "[::]:8080"]