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
    StructField("message", StringType(), True)
])

# Kafka consumer settings
kafka_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "nginx-logs") \
    .load()

# Parse the JSON from Kafka
parsed_df = kafka_df.select(from_json(col("value").cast("string"), json_schema).alias("data"))

# Extract the 'message' field from the parsed JSON
message_df = parsed_df.select("data.message")

# Regular expression to match the log format in the message
log_pattern = r'(\S+) - - \[(\S+ \+\d+)\] "(\S+) ([^"]+) HTTP/\d\.\d" (\d{3}) (\d+) "([^"]*)" "([^"]*)"'

# Process the logs using the pattern
processed_logs_df = message_df.select(
    regexp_extract('message', log_pattern, 1).alias('ip'),
    regexp_extract('message', log_pattern, 2).alias('timestamp'),
    regexp_extract('message', log_pattern, 3).alias('method'),
    regexp_extract('message', log_pattern, 4).alias('path'),
    regexp_extract('message', log_pattern, 5).alias('status'),
    regexp_extract('message', log_pattern, 6).alias('size'),
    regexp_extract('message', log_pattern, 7).alias('referrer'),
    regexp_extract('message', log_pattern, 8).alias('user_agent')
)

# Format the output log entries
formatted_logs_df = processed_logs_df.select(
    concat_ws(" | ", col('ip'), col('timestamp'), col('method'), col('path'), 
              col('status'), col('size'), col('referrer'), col('user_agent')).alias('log_entry')
)

# Define the path for the single output file
output_path = "/home/mekky/Project/logs/preprocessed/nginx/output.log"

# Custom function to write to a single file
def write_to_single_file(df, epoch_id):
    # Convert DataFrame to RDD and collect as a list of strings
    logs = df.rdd.map(lambda row: row['log_entry']).collect()
    
    # Append to the file
    with open(output_path, 'a') as f:
        for log in logs:
            f.write(log + '\n')

# Use foreachBatch to write to a single file
query = formatted_logs_df.writeStream \
    .foreachBatch(write_to_single_file) \
    .outputMode("append") \
    .option("checkpointLocation", "/home/mekky/Project/checkpoints/nginx") \
    .start()

# For debugging: Write to console to verify the output
debug_query = formatted_logs_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# Wait for the stream to terminate
query.awaitTermination()