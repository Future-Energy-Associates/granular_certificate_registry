FROM ubuntu:22.04

# Set environment variables to non-interactive to avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary dependencies
RUN apt update && apt install -y \
    curl \
    nano \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    build-essential \
    libpq-dev \
    gcc \ 
    musl-dev

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set the working directory
WORKDIR /code

# Copy the project files
COPY ./pyproject.toml ./poetry.lock* /code/

# Install dependencies using Poetry
RUN /root/.local/bin/poetry install --no-root

# Copy the rest of the application code
COPY ./setup.py /code/setup.py
COPY ./src /code/src
COPY ./.env /code/.env
COPY ./frontend /code/frontend
COPY ./node_modules /code/node_modules
COPY ./tests /code/tests
COPY ./README.md /code/README.md

# Install the package in editable mode
RUN /root/.local/bin/poetry install

# Set the command to run the application
CMD ["/root/.local/bin/poetry", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "80"]