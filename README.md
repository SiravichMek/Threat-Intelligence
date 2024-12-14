
# Threat Intelligence System Setup

This README provides comprehensive steps to set up the Threat Intelligence System, covering log ingestion, preprocessing, machine learning model deployment, and visualization using the ELK Stack and MITRE ATT&CK framework mapping.

## Prerequisites
- Apache Spark installed on the cluster
- ELK Stack installed
- Kafka for distributed log processing
- Machine learning models for NGINX, MySQL, and network logs
- Linux (Ubuntu 64-bit) for hosting the sample web server
- Windows 10 for log monitoring and visualization
---

## Step 1: Set Up Log Collection (On Linux VM)
1. Create the necessary Kafka topics.
```bash
./kafka-topics.sh --create --topic [topic_name] --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```
2. Adjust the Configuration for FileBeat by Edit filebeat.yml to specify the log paths for NGINX and database logs.

3. Tcpdump Configuration to capture network traffic and save the acquisition result into a “.log” file. 
```bash
sudo tcpdump -i [network card name] icmp and dst [destination IP] -tttt > [path to save capturing file]

```
---

## Step 2: Set Up Log Preprocessing (On Linux VM)
1. Navigate to the Spark log preprocessing script directory.
2. Adjust the Kafka topics to relate with existing Topics and the output paths which will be used to place outputs.
3. Execute the Spark Streaming process using the following command:
   ```bash
   spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0 spark/log_preprocessing.py
   ```

---

## Step 3: Deploy Logstash Pipeline (On Linux VM)
1. Go to the Logstash configuration directory:
   ```bash
   cd logstash/config
   ```
2. Edit the `transfer.conf` file to specify:
   - **Input sources**: Output paths for processed logs
   - **Output destinations**: IP addresses of devices hosting the ELK Stack
3. Deploy the Logstash pipeline using the following command:
   ```bash
   sudo service logstash start
   ```

---

## Step 4: Deploy Machine Learning Models (On Window Device)

### NGINX Model
1. Navigate to the NGINX model directory:
   ```bash
   cd model/nginx-model
   ```
2. Run the `ml_api.ipynb` notebook to deploy the model.

### MySQL Model
1. Navigate to the MySQL model directory:
   ```bash
   cd model/mysql-model
   ```
2. Execute the SQL injection detection API script:
   ```bash
   python SQLi_XSS_API.py
   ```

### Network Model
1. Navigate to the network model directory:
   ```bash
   cd model/network-model
   ```
2. Run the network anomaly detection API:
   ```bash
   python new_api_get.py
   ```

---

## Step 5: Setup Receiving Pipeline on ELK Hosted Device (On Window Device)

### Configure Receiving Logstash
1. Copy the Logstash configuration file:
   ```bash
   cp /logstash/pipeline_log_processing.conf /logstash/config
   ```
2. Edit `pipeline_log_processing.conf` to:
   - Specify **input sources**: Ports listening to incoming Logstash pipelines
   - Specify **output destinations**: Elasticsearch
3. Start Logstash with the updated configuration:
   ```bash
   sudo service logstash start
   ```

---

## Step 6: Setup Elasticsearch and Kibana (On Window Device)

### Start Elasticsearch
1. Activate Elasticsearch by running:
   ```bash
   elasticsearch.bat
   ```

### Start Kibana
1. Activate Kibana by running:
   ```bash
   kibana.bat
   ```
2. Access Kibana via the web GUI at:
   ```
   http://localhost:5601
   ```

---

## Step 7: Configure MITRE ATT&CK Framework Mapping (On Window Device)
1. In Kibana, navigate to **Dev Tools** from the menu panel.
2. Use the JSON configuration file located at `/elasticsearch/mitre_mapping_pipeline.json` to map the MITRE ATT&CK framework.

---

## Final Steps
By following the steps above, the Threat Intelligence System will be fully installed and operational. It will:
- Process logs from various sources
- Detect threats using machine learning models
- Map detected anomalies to the MITRE ATT&CK framework
- Visualize insights in real time using Kibana

### Access the Kibana Dashboard
Monitor and analyze the threat intelligence system via the Kibana interface for real-time insights and incident management.
