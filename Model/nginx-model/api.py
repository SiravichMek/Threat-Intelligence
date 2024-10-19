from flask import Flask, request, jsonify
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

# Initialize Flask app
app = Flask(__name__)

# Set up logging to a file
logging.basicConfig(filename='app.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s: %(message)s')

# Load the trained model and vectorizer
try:
    print("Loading model and vectorizer...")
    vectorizer = joblib.load('vectorizer.pkl')
    model = joblib.load('fine_tuned_ensemble_model.pkl')
except Exception as e:
    app.logger.error(f"Error loading model or vectorizer: {e}")
    raise e

# Helper function to parse individual log entry
def parse_log_entry(log):
    try:
        # Split the log entry into parts by whitespace
        parts = log.split(" ")

        # Ensure we have at least the required 6 elements
        if len(parts) < 6:
            raise ValueError("Log entry does not contain enough parts")

        ip = parts[2]
        method = parts[5]
        url = parts[6]
        status = parts[7]
        size = parts[8]
        referer = parts[9] if parts[9] != '-' else '-'

        # Create a structured log entry string for model input
        structured_log = f"{ip} {method} {url} {status} {size} {referer}"
        return structured_log

    except (IndexError, ValueError) as e:
        app.logger.error(f"Skipping malformed log entry: {log} - Error: {e}")
        return None

# Route to predict a single log entry (POST method)
# @app.route('/predict', methods=['POST'])
# def predict_log():
#     try:
#         data = request.json  # Get JSON data from request
#         log = data.get('log')  # Extract 'log' from JSON payload

#         if not log:
#             return jsonify({'error': 'No log entry provided'}), 400

#         # Parse the log and handle malformed cases
#         parsed_log = parse_log_entry(log)
#         if not parsed_log:
#             return jsonify({'error': 'Invalid log format'}), 400

#         # Transform the log using the vectorizer
#         X_test = vectorizer.transform([parsed_log])

#         # Predict the label using the model
#         prediction = model.predict(X_test)[0]

#         # Map numeric labels to human-readable labels
#         label_mapping = {0: 'normal', 1: 'suspicious status', 2: 'bypass'}
#         predicted_label = label_mapping.get(prediction, 'unknown')

#         # Format the output
#         result = {
#             'log': log,
#             'predicted_label': predicted_label
#         }

#         return jsonify(result)
#     except Exception as e:
#         app.logger.error(f"Error in /predict route: {e}")
#         return jsonify({'error': 'Internal Server Error'}), 500

# Route to test if API is running
@app.route('/', methods=['GET'])
def home():
    try:
        return "Threat Classification API is running!"
    except Exception as e:
        app.logger.error(f"Error in / route: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

# New GET method to predict log entry through query parameters
@app.route('/predict_get', methods=['GET'])
def predict_log_get():
    try:
        log = request.args.get('log')  # Get 'log' from query parameters

        if not log:
            return jsonify({'error': 'No log entry provided'}), 400

        # Parse the log and handle malformed cases
        parsed_log = parse_log_entry(log)
        if not parsed_log:
            return jsonify({'error': 'Invalid log format'}), 400

        # Transform the log using the vectorizer
        X_test = vectorizer.transform([parsed_log])

        # Predict the label using the model
        prediction = model.predict(X_test)[0]

        # Map numeric labels to human-readable labels
        label_mapping = {0: 'normal', 1: 'suspicious status', 2: 'bypass'}
        predicted_label = label_mapping.get(prediction, 'unknown')

        # Format the output
        result = {
            'log': log,
            'predicted_label': predicted_label
        }

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in /predict_get route: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


# Run the Flask app
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
