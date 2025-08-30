# Use official Python image
FROM python:3.11-slim


# Install OS dependencies
RUN apt-get update && apt-get install -y \
   gcc \
   g++ \
   unixodbc \
   unixodbc-dev \
   libpq-dev \
   curl \
   gnupg \
   ca-certificates \
   apt-transport-https \
   && rm -rf /var/lib/apt/lists/*


# Add Microsoft repo and install ODBC Driver 18
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg \
   && echo "deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
   && apt-get update \
   && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
   && rm -rf /var/lib/apt/lists/*


# Configure ODBC driver
RUN echo "[ODBC Driver 18 for SQL Server]\n\
Description=Microsoft ODBC Driver 18 for SQL Server\n\
Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.1.so.1.1\n\
UsageCount=1" >> /etc/odbcinst.ini


# Set working directory
WORKDIR /app


# Copy project files
COPY . .


# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Expose port 8000 for Django
EXPOSE 8000


# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

