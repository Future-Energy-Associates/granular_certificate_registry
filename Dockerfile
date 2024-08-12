FROM ubuntu:20.04

# Set environment variables to non-interactive to avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary dependencies
RUN apt update && apt install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    curl \
    nano \
    build-essential

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

# Install the package in editable mode
RUN /root/.local/bin/poetry install

# Set the command to run the application
CMD ["/root/.local/bin/poetry", "run", "uvicorn", "energytag.api.main:app", "--host", "0.0.0.0", "--port", "80"]