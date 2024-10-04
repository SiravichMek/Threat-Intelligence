from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL connection setup
def get_db_connection():
    connection = mysql.connector.connect(
        host="db",  # refers to the MySQL container's service name in docker-compose
        user="root",
        password="password",
        database="myapp_db"
    )
    return connection

@app.route('/', methods=['GET'])
def home():
    return render_template('login.html')

@app.route('/error')
def error_route():
    raise Exception("This is a test error!")

# Endpoint to display comments
@app.route('/comments_page', methods=['GET'])
def comments_page():
    return render_template('comment_form.html') 


@app.route('/comments', methods=['POST'])
def submit_comment():
    username = request.form['username']
    comment = request.form['comment']
    return f"""
        <h1>Comments</h1>
        <p><strong>{username}</strong>: {comment}</p>
        <a href="/">Back</a>
    """

@app.route('/profile', methods=['GET'])
def profile():
    # Insecure Direct Object Reference
    user_id = request.args.get('user_id')
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # No access control checks
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  
    user = cursor.fetchone()

    connection.close()

    if user:
        return render_template('profile.html', user=user)
    else:
        return "User not found", 404

@app.route('/vulnerable_login', methods=['POST'])
def vulnerable_login():
    username = request.form['username']
    password = request.form['password']

    # Vulnerable to SQL Injection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Unsanitized input leading to SQL Injection vulnerability
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'")
    user = cursor.fetchone()

    connection.close()

    if user:
        return redirect(url_for('profile', user_id=user['id']))  # Redirect to profile page
    else:
        return "Invalid credentials"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
