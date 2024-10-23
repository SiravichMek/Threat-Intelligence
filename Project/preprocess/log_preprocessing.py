from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, regexp_extract, concat_ws
from pyspark.sql.types import StructType, StructField, StringType
import os

# Create Spark session
spark = SparkSession.builder \
    .appName("Log Preprocessing with Kafka") \
    .getOrCreate()

# Define the schema for the JSON input
json_schema = StructType([
    StructField("@timestamp", StringType(), True),
    StructField("message", StringType(), True),
    StructField("log", StructType([
        StructField("file", StructType([
            StructField("path", StringType(), True)
        ]), True)
    ]), True)
])

# Kafka consumer settings
# Nginx Topic
nginx_kafka_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "nginx-logs") \
    .load()

# MySQL Topic
mysql_kafka_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "mysql-logs") \
    .load()

# Firewall Topic
# firewall_kafka_df = spark.readStream.format("kafka") \
#     .option("kafka.bootstrap.servers", "localhost:9092") \
#     .option("subscribe", "firewall-logs") \
#     .load()

# Parse the JSON from Kafka for each topic
nginx_message_df = nginx_kafka_df.selectExpr("CAST(value AS STRING) AS message")
mysql_message_df = mysql_kafka_df.selectExpr("CAST(value AS STRING) AS message")
# firewall_message_df = firewall_kafka_df.select(from_json(col("value").cast("string"), json_schema).alias("data.message"))

# Regular expression to match the log format in the message
# Nginx pattern
log_nginx_pattern = r'(\d+\.\d+\.\d+\.\d+) - - \[([^\]]+)\] "(\S+) ([^"]+)" (\d{3}) (\d+) "([^"]*)" "([^"]+)"'

# MySQL pattern
log_mysql_pattern = r'(\S+T\S+Z)\s+(\d+)\s+(\S+)\s+(.*)'

# Firewall pattern (Update this based on the actual firewall log format)
# log_firewall_pattern = r'(\S+) - - \[(\S+ \+\d+)\] "(\S+) ([^"]+) HTTP/\d\.\d" (\d{3}) (\d+) "([^"]*)" "([^"]*)"'

# Process the logs using the updated patterns
# Nginx Columns
processed_nginx_logs_df = nginx_message_df.select(
    regexp_extract('message', log_nginx_pattern, 1).alias('ip'),
    regexp_extract('message', log_nginx_pattern, 2).alias('timestamp'),
    regexp_extract('message', log_nginx_pattern, 3).alias('method'),
    regexp_extract('message', log_nginx_pattern, 4).alias('path'),
    regexp_extract('message', log_nginx_pattern, 5).alias('status'),
    regexp_extract('message', log_nginx_pattern, 6).alias('size'),
    regexp_extract('message', log_nginx_pattern, 7).alias('referrer'),
    regexp_extract('message', log_nginx_pattern, 8).alias('user_agent')
)

# MySQL Columns
processed_mysql_logs_df = mysql_message_df.select(
    regexp_extract('message', log_mysql_pattern, 1).alias('timestamp'),
    regexp_extract('message', log_mysql_pattern, 2).alias('thread_id'),
    regexp_extract('message', log_mysql_pattern, 3).alias('command'),
    regexp_extract('message', log_mysql_pattern, 4).alias('query_or_message')
)

# Firewall Columns (Assume similar pattern to Nginx)
# processed_firewall_logs_df = firewall_message_df.select(
#     regexp_extract('message', log_firewall_pattern, 1).alias('ip'),
#     regexp_extract('message', log_firewall_pattern, 2).alias('timestamp'),
#     regexp_extract('message', log_firewall_pattern, 3).alias('method'),
#     regexp_extract('message', log_firewall_pattern, 4).alias('path'),
#     regexp_extract('message', log_firewall_pattern, 5).alias('status'),
#     regexp_extract('message', log_firewall_pattern, 6).alias('size'),
#     regexp_extract('message', log_firewall_pattern, 7).alias('referrer'),
#     regexp_extract('message', log_firewall_pattern, 8).alias('user_agent')
# )

# Format the output log entries
formatted_nginx_logs_df = processed_nginx_logs_df.select(
    concat_ws(" ", col('ip'), col('timestamp'), col('method'), col('path'), 
              col('status'), col('size'), col('referrer'), col('user_agent')).alias('log_entry')
)

filtered_mysql_logs_df = processed_mysql_logs_df.filter(col('command') == 'Query') \
    .select(
        concat_ws(" ", col('timestamp'),
                  col('query_or_message')).alias('log_entry')
    )

# formatted_firewall_logs_df = processed_firewall_logs_df.select(
#     concat_ws(" | ", col('ip'), col('timestamp'), col('method'), col('path'), 
#               col('status'), col('size'), col('referrer'), col('user_agent')).alias('log_entry')
# )

# Define paths for the single output files
output_nginx_path = "/home/mekky/Project/logs/preprocessed/nginx/output.log"
output_mysql_path = "/home/mekky/Project/logs/preprocessed/mysql/output.log"
# output_firewall_path = "/home/mekky/Project/logs/preprocessed/firewall/output.log"

# Custom function to write to a single file
def write_to_single_file(output_path):
    def write_logs(batch_df, epoch_id):
        logs = batch_df.rdd.map(lambda row: row['log_entry']).collect()
        with open(output_path, 'a') as f:
            for log in logs:
                f.write(log + '\n')
    return write_logs

# Use foreachBatch to write to a single file
nginx_query = formatted_nginx_logs_df.writeStream \
    .foreachBatch(write_to_single_file(output_nginx_path)) \
    .outputMode("append") \
    .option("checkpointLocation", "/home/mekky/Project/checkpoints/nginx") \
    .start()

mysql_query = filtered_mysql_logs_df.writeStream \
    .foreachBatch(write_to_single_file(output_mysql_path)) \
    .outputMode("append") \
    .option("checkpointLocation", "/home/mekky/Project/checkpoints/mysql") \
    .start()

# firewall_query = formatted_firewall_logs_df.writeStream \
#     .foreachBatch(write_to_single_file(output_firewall_path)) \
#     .outputMode("append") \
#     .option("checkpointLocation", "/home/mekky/Project/checkpoints/firewall") \
#     .start()

# Wait for the streams to terminate
nginx_query.awaitTermination()
mysql_query.awaitTermination()
# firewall_query.awaitTermination()
