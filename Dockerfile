# Use official Python image
FROM python:3.11-slim

# Install OS dependencies and Microsoft SQL Server ODBC Driver
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc \
    unixodbc-dev \
    libpq-dev \
    curl \
    gnupg2 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Verify ODBC installation and add configuration
RUN echo "[ODBC Driver 18 for SQL Server]\n\
Description=Microsoft ODBC Driver 18 for SQL Server\n\
Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.1.so.1.1\n\
UsageCount=1" >> /etc/odbcinst.ini

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose port 8000 for Django
EXPOSE 8000

# Default command (can be overridden by docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]