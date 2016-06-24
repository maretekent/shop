FROM ubuntu:14.04
MAINTAINER Tarun Bhardwaj <tarun.bhardwaj@fulfil.io>

RUN apt-get -y update

# Add node js repo to ppa
RUN apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:chris-lea/node.js
RUN apt-get -y update
RUN apt-get install -y curl python nodejs git-core

RUN npm install -g bower
RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python

ADD . /opt/shop/

# Install python deps
WORKDIR /opt/shop/

# Install module
RUN pip install -r requirements/dev.txt
RUN bower install --allow-root
ENTRYPOINT ["gunicorn"]
CMD ["shop.app:create_app()", "-b", "0.0.0.0:5000", "-w",  "3", "--access-logfile", "-", "--error-logfile", "-"]
