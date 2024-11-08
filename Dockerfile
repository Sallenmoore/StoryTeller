FROM python:3.12

# NOTE: RUN ON HOST
# RUN echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf && sysctl -p

RUN apt-get clean
RUN apt-get update
RUN apt-get install --no-install-recommends -y build-essential curl git nodejs npm
RUN curl https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian10-x86_64-100.9.4.deb --output mongodb-database-tools.deb; apt install ./mongodb-database-tools.deb
# Install the vendor applications/configurations
COPY ./vendor/gunicorn.conf.py /var/gunicorn.conf.py
RUN npm install -g sass

# install dependencies
RUN pip install --no-cache-dir --upgrade pip wheel
COPY ./requirements.txt /var/tmp/requirements.txt
RUN pip install -r /var/tmp/requirements.txt