from flask import Flask, jsonify, request
import pandas as pd
import joblib
from collections import deque
import json

app = Flask(__name__)

# Load the trained model
rf_model = joblib.load("simplified_random_forest_model_realtime.pkl")
ddos_threshold = 100
window_size = 60  # 1-minute window in seconds

# Sliding window for real-time processing
log_window = deque()

# Map numerical labels to string labels
label_map = {0: "normal", 1: "Denial of Service"}

# Function to process and extract features in real-time
def process_and_extract_features_real_time(logs, generate_labels=False, ddos_threshold=100):
    """
    Process logs in real-time using a sliding window to dynamically calculate counts.
    """
    global log_window

    try:
        # Add new logs to the sliding window
        for log in logs:
            # Ensure 'src_ip' exists and is valid
            if 'src_ip' not in log or pd.isna(log['src_ip']) or not isinstance(log['src_ip'], str):
                continue  # Skip logs without a valid 'src_ip'
            
            log['timestamp'] = pd.to_datetime(log['timestamp'])  # Ensure 'timestamp' is a datetime object
            log_window.append(log)

        # Remove logs older than the window size
        if log_window:
            current_time = max([log['timestamp'] for log in log_window])  # Get the latest timestamp
            while log_window and (current_time - log_window[0]['timestamp']).total_seconds() > window_size:
                log_window.popleft()

        # Count requests for each 'src_ip' in the sliding window
        counts = {}
        for log in log_window:
            if log['type'] == 'request':  # Only count 'request' logs
                counts[log['src_ip']] = counts.get(log['src_ip'], 0) + 1

        # Prepare the processed logs with dynamic counts
        processed_logs = []
        for log in logs:
            if 'src_ip' in log and isinstance(log['src_ip'], str):
                src_ip = log['src_ip']
                count = counts.get(src_ip, 0)  # Get the dynamic count for the 'src_ip'
                processed_logs.append({
                    "timestamp": log['timestamp'],
                    "src_ip": src_ip,
                    "count": count
                })

        # Convert processed logs to a DataFrame
        processed_logs_df = pd.DataFrame(processed_logs)

        # Optionally generate labels
        if generate_labels:
            processed_logs_df['label'] = processed_logs_df['count'].apply(lambda x: 1 if x >= ddos_threshold else 0)
            return processed_logs_df[['count']].values, processed_logs_df['label'].values, processed_logs_df

        # Return only the features
        return processed_logs_df[['count']].values, processed_logs_df

    except Exception as e:
        raise ValueError(f"Error in processing real-time logs: {e}")


@app.route('/test', methods=['GET'])
def predict():
    try:
        # Get the 'log' query parameter
        log_param = request.args.get('log')
        if not log_param:
            return jsonify({"error": "Missing 'log' query parameter"}), 400

        # Parse the JSON string from the 'log' parameter
        try:
            logs = json.loads(log_param)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format in 'log' query parameter"}), 400

        # Handle the case where the input is a single JSON object (not a list)
        if isinstance(logs, dict):
            logs = [logs]  # Wrap the single log into a list

        # Process logs and extract features
        features, processed_logs = process_and_extract_features_real_time(logs, generate_labels=False)

        if processed_logs.empty:
            return jsonify({"error": "No valid logs to process"}), 400

        # Predict using the loaded model
        predictions = rf_model.predict(features)
        processed_logs['predicted_label'] = predictions

        # Map numerical predictions to string labels
        processed_logs['predicted_label'] = processed_logs['predicted_label'].map(label_map)

        # Prepare the response data
        response_data = [
            {
                "log": {
                    "timestamp": log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    "src_ip": log['src_ip']
                },
                "count": int(log['count']),
                "predicted_label": log['predicted_label']
            }
            for _, log in processed_logs.iterrows()
        ]

        # Return the response as JSON
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8082)
