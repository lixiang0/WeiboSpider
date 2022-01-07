FROM ubuntu:20.04
WORKDIR /code


RUN apt update --yes && apt upgrade --yes && apt-get clean && apt-get update --yes

RUN apt install -y tzdata
RUN echo "Asia/Shanghai" > /etc/timezone
RUN rm -f /etc/localtime

RUN dpkg-reconfigure -f noninteractive tzdata

RUN apt-get install -y locales
RUN locale-gen 'en_US.UTF-8'

ENV LANG en_US.UTF-8 
ENV LC_ALL en_US.UTF-8 
ENV LC_LANG en_US.UTF-8  


RUN  apt install build-essential libssl-dev libffi-dev python-dev python3-pip gcc --yes
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple
RUN pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
# COPY youran-0.1.3-py3-none-any.whl .
COPY . .
# RUN pip3 install youran-0.1.3-py3-none-any.whl
RUN pip3 install cython pika -i https://mirrors.aliyun.com/pypi/simple