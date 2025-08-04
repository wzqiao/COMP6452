# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory (for SQLite database)
RUN mkdir -p instance

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Create a startup script with database initialization and blockchain sync
RUN echo '#!/bin/bash\n\
echo "Initializing database..."\n\
python init_db.py\n\
echo "Database initialized"\n\
\n\
echo "Syncing blockchain data..."\n\
timeout 180 bash -c "echo 'N' | python sync_contract_data.py" || {\n\
    echo "Warning: Blockchain sync failed or timed out, continuing without sync..."\n\
}\n\
echo "Blockchain sync completed (or skipped)"\n\
\n\
echo "Starting application..."\n\
python app.py' > /app/startup.sh && \
    chmod +x /app/startup.sh

# Start the application with database initialization
CMD ["/app/startup.sh"]