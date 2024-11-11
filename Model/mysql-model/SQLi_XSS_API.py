from flask import Flask, request, jsonify
import joblib
import re
import pandas as pd
from sklearn.metrics import accuracy_score

def initial_filter(log):
    # Basic rule-based approach
    if ("SELECT" in log or "INSERT" in log) and ("<script>" in log or "<" in log):
        return "XSS"  # If it contains both SQL and XSS patterns, return XSS
    elif "SELECT" in log or "INSERT" in log:  # SQL-like keywords
        return "SQLi"
    elif "<script>" in log or "<" in log:  # XSS-like patterns
        return "XSS"
    return "Unknown"

# Define a combined tokenizer for both SQLi and XSS with operator flexibility
def custom_tokenizer(payload):
    tokens = []
    current_token = ''

    # Define SQLi and XSS patterns
    sqli_patterns = [
        r"\b1\s*=\s*1\b",           
        r"\bOR\s+1\s*=\s*1\b",      
        r"\bOR\s+'.*?'\s*=\s*'.*?'",  
        r"\bUNION\s+SELECT\b",        
        r"\b--",                    
        r"\/\*.*?\*\/",             
        r"\bDROP\b\s+.*\bTABLE\b",  
    ]

    xss_patterns = [
        r'<script[^>]*?>.*?</script>', 
        r'javascript\s*:',              
        r'on\w+\s*=',                   
        r'<img[^>]*?on\w+\s*=\s*["\'].*?["\']',  
        r'<iframe[^>]*?>.*?</iframe>',  
        r'<svg[^>]*?>.*?</svg>',        
        r'<a[^>]*?href\s*=\s*["\']javascript:.*?["\']',  
        r'<object.*?>.*?</object>',     
        r'<embed.*?>.*?</embed>',       
        r'<form.*?>.*?</form>',         
        r'&#[xX]?[0-9a-fA-F]+;',        
        r'alert\s*\(.*?\)',             
    ]

    combined_sqli_xss_regex = '|'.join(sqli_patterns + xss_patterns)

    i = 0
    while i < len(payload):
        char = payload[i]
        match = re.match(combined_sqli_xss_regex, payload[i:])
        if match:
            if current_token:
                tokens.append(current_token)
                current_token = ''
            tokens.append(match.group(0))
            i += len(match.group(0))
            continue

        if char in ['\'', '\"', ';', '--', '=', '<', '>']:
            if current_token:
                tokens.append(current_token)
                current_token = ''
            tokens.append(char)
        elif char.isspace():
            if current_token:
                tokens.append(current_token)
                current_token = ''
        else:
            current_token += char

        i += 1

    if current_token:
        tokens.append(current_token)

    return tokens

def xss_tokenizer(payload):
    tokens = []
    current_token = ''
    
    # Define XSS patterns
    xss_patterns = [
        r'<script[^>]*?>.*?</script>',              # <script> tags
        r'javascript\s*:',                          # "javascript:" syntax
        r'on\w+\s*=',                               # Inline event handlers (e.g., "onclick=")
        r'<img[^>]*?on\w+\s*=\s*["\'].*?["\']',     # <img> tags with event handlers
        r'<iframe[^>]*?>.*?</iframe>',              # <iframe> tags
        r'<svg[^>]*?>.*?</svg>',                    # <svg> tags
        r'<a[^>]*?href\s*=\s*["\']javascript:.*?["\']', # <a> tags with "javascript:" in href
        r'<object.*?>.*?</object>',                 # <object> tags
        r'<embed.*?>.*?</embed>',                   # <embed> tags
        r'<form.*?>.*?</form>',                     # <form> tags
        r'&#[xX]?[0-9a-fA-F]+;',                    # HTML entity encoding
        r'alert\s*\(.*?\)',                         # "alert()" function
        r'<.*?alert\(.+?\);.*?>',                   # "<...alert();...>" syntax
    ]

    # Combine XSS patterns into one regex
    combined_xss_regex = '|'.join(xss_patterns)
    
    # Iterate over each character in payload to create tokens
    i = 0
    while i < len(payload):
        # Check for matches against XSS patterns
        match = re.match(combined_xss_regex, payload[i:])
        if match:
            # If a match is found, add any current token, then add the match
            if current_token:
                tokens.append(current_token)
                current_token = ''
            tokens.append(match.group(0))
            i += len(match.group(0))  # Move past the matched pattern
            continue
        
        # Accumulate regular characters until a special character or match
        char = payload[i]
        if char in ['\'', '\"', ';', '=', '<', '>']:
            # If there's a current token, add it before adding the special character
            if current_token:
                tokens.append(current_token)
                current_token = ''
            tokens.append(char)
        elif char.isspace():
            # If space is encountered, add any current token and reset
            if current_token:
                tokens.append(current_token)
                current_token = ''
        else:
            # Otherwise, add the character to the current token
            current_token += char

        i += 1
    
    # Append the final token if there's any
    if current_token:
        tokens.append(current_token)
    
    return tokens

# Define a whitelist of safe patterns
whitelist_patterns = [
    r"^SELECT \* FROM users WHERE id\s*=\s*\d+$",
]
# Check if a query matches any pattern in the whitelist
def is_whitelisted(query):
    for pattern in whitelist_patterns:
        if re.fullmatch(pattern, query):
            return True
    return False

# Initialize the Flask app
app = Flask(__name__)

# Load the saved models, vectorizers, and tokenizers
sqli_model = joblib.load('gradient_boosting_model.pkl')
xss_model = joblib.load('logistic_regression_xss.pkl')
sqli_vectorizer = joblib.load('tfidf_vectorizer.pkl')
xss_vectorizer = joblib.load('tfidf_vectorizer_xss.pkl')

@app.route('/predict', methods=['GET'])
def predict():
    """
    Endpoint to make predictions on SQL queries.
    Accepts 'queries' as a comma-separated list of SQL queries in the URL.
    """
    queries_param = request.args.get('queries')
    if not queries_param:
        return jsonify({'error': 'No queries provided.'}), 400

    # Split the queries parameter by commas and strip whitespace
    queries = [q.strip() for q in queries_param.split(',') if q.strip()]

    # Preprocess and predict
    results = []
    for query in queries:
        if is_whitelisted(query):
            prediction_label = "Normal"  # Bypass model prediction if query is whitelisted
        else:
            # Apply initial filter function to classify query type
            model_type = initial_filter(query)

            if model_type == "SQLi":
                query_tfidf = sqli_vectorizer.transform([query])
                pred = sqli_model.predict(query_tfidf)[0]
                if pred == 1:
                    prediction_label = "SQL Injection"
                else:
                    prediction_label = "Normal"
            elif model_type == "XSS":
                query_tfidf = xss_vectorizer.transform([query])
                pred = xss_model.predict(query_tfidf)[0]
                if pred == 2:
                    prediction_label = "Cross-Site Scripting"
                else:
                    prediction_label = "Normal"
            else:
                prediction_label = "Normal"
        
        results.append({
            "log": query,
            "predicted_label": prediction_label
        })

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8081)
