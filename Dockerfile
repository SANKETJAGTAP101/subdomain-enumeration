FROM python:3.9-slim-buster

WORKDIR /app

# Copy subfinder binary - corrected path and ensure executable
COPY subfinder /app/subfinder
RUN chmod +x /app/subfinder

# Copy your web application code
COPY . /app/
RUN chmod +x /app/script1.sh

# No need to copy requirements.txt again, it's already in /app
# Install dependencies
RUN pip install -r requirements.txt


# Set environment variables (if needed)
ENV PORT 5000
ENV DEBUG_PRINT "true"

CMD ["python3", "app.py"]
