# Data lakehouse

### How-to-run will be uploaded later

# First run:
0. Install external dependencies:
- Install JDK 23: https://download.oracle.com/java/23/latest/jdk-23.0.1_linux-aarch64_bin.tar.gz
- Install Hadoop 3.4.0: https://dlcdn.apache.org/hadoop/common/hadoop-3.4.0/hadoop-3.4.0.tar.gz

Extract downloaded files to `/services/airflow/dependencies` and extract them
 
1. Change the variable IS_RESUME in ./services/metastore/docker-compose.yml to False

2. Grant all permissions for HDFS
```
sudo mkdir -p ./services/hadoop/data
sudo chmod  777 ./services/hadoop/data/*
```

1. Create docker network
`docker network create default_net`

1. Docker up
`bash start_all_service.sh`