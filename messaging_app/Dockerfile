# Use a base Python image
FROM python:3.10

# Set environment variable to ensure Python output is not buffered
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the default Django port (8000)
EXPOSE 8000

# Command to run the Django app (you may need to adjust for your specific app)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
