FROM apache/superset

USER root

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev
    
RUN pip install clickhouse-connect
RUN pip install pyhive thrift sasl

USER superset
