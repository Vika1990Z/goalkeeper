FROM python:3.6-buster
LABEL maintainer="vika1990z <v.zubyenko@gmail.com>"
COPY . /goalkeeper_app
WORKDIR /goalkeeper_app
RUN apt update
RUN apt install -y python3-pip
RUN pip3 install openstacksdk
RUN apt install -y  nmap
RUN pip3 install python-nmap
CMD python ./goalkeeper_latest.py