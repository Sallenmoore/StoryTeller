FROM python:3.12

# NOTE: RUN ON HOST
# RUN echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf && sysctl -p
WORKDIR /var/app
RUN apt-get clean && apt-get update && \
    apt-get install --no-install-recommends -y \
    build-essential \
    curl \
    git \
    nodejs \
    npm \
    ffmpeg && \
    # Install MongoDB Tools
    curl https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian10-x86_64-100.9.4.deb --output mongodb-database-tools.deb && \
    apt install ./mongodb-database-tools.deb && \
    rm mongodb-database-tools.deb && \
    rm -rf /var/lib/apt/lists/*

#    Ensure './vendor/package.json' exists in your project root.
COPY ./vendor/package.json /var/app/package.json
RUN npm install -g npm@latest && npm cache clean --force && \
    npm install -g sass && \
    npm install

# Install the vendor applications/configurations
COPY ./vendor/gunicorn.conf.py /var/gunicorn.conf.py

# install dependencies
RUN pip install --no-cache-dir --upgrade pip wheel
COPY ./requirements.txt /var/tmp/requirements.txt
RUN pip install -r /var/tmp/requirements.txt