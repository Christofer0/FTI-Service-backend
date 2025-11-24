FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 2224

# Gunicorn WSGI server
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:2224", "main:create_app()"]
