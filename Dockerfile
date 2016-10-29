FROM ubuntu:14.04
MAINTAINER Tarun Bhardwaj <tarun.bhardwaj@fulfil.io>

RUN apt-get update && apt-get install -y \
    curl \
    python \
    git \
 && rm -rf /var/lib/apt/lists/*
RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python

ADD . /opt/shop/

# Install python deps
WORKDIR /opt/shop/

# Install module
RUN pip install -r requirements.txt

# clean up all shit to make image size small
RUN apt-get -y autoremove

ENTRYPOINT ["gunicorn"]
CMD ["shop.app:create_app()", "-b", "0.0.0.0:5000", "-w",  "3", "--access-logfile", "-", "--error-logfile", "-"]
