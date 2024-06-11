FROM python:3.8-slim

# Set environment variables to avoid warnings
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Install pip and virtualenv
RUN pip install --upgrade pip virtualenv

RUN mkdir /usr/app
RUN mkdir /usr/app/Logs
COPY . /usr/app
WORKDIR /usr/app

# Create and activate a virtual environment
RUN virtualenv venv
ENV PATH="/usr/src/app/venv/bin:$PATH"

RUN apt-get -y update && apt-get -y upgrade \
build-essential \
libsqlite3-dev \
&& rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install vim telnet -y && apt autoremove -y
RUN pip install -r requirements.txt

# Copy the entire application directory into the container
COPY . .

# Make the directory where files will be uploaded
RUN mkdir -p usr/app/app/data
RUN mkdir -p usr/app/app/company_documents


EXPOSE 80
# COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["python", "app.py", "runserver","--dir=/usr/app"]

