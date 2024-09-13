FROM python:3.11.4-slim

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
# RUN curl -sSL https://install.python-poetry.org | python3 -
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 && \
cd /usr/local/bin && \
ln -s /opt/poetry/bin/poetry && \
poetry config virtualenvs.create false

# Set the working directory
WORKDIR /code

# Copy the project files
COPY ./pyproject.toml ./poetry.lock* ./

# Install dependencies using Poetry
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

ENV PYTHONPATH=/code

# Copy the rest of the application code
COPY ./setup.py ./setup.py
COPY ./gc_registry ./gc_registry/
COPY ./.env ./.env
COPY ./frontend ./frontend/
COPY ./README.md ./README.md
COPY ./Makefile ./Makefile
COPY ./alembic.ini ./alembic.ini

CMD ["uvicorn", "gc_registry.main:app", "--host", "0.0.0.0", "--port", "8000"]
