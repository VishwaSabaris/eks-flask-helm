from flask import Flask, request, jsonify, Response
import mysql.connector
import os
import json
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "flask_requests_total",
    "Total number of requests received by Flask app",
    ["method", "endpoint"]
)


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )


@app.route("/")
def home():
    REQUEST_COUNT.labels(method="GET", endpoint="/").inc()
    return "Flask App running on EKS and connected to RDS MySQL!"


@app.route("/init-db")
def init_db():
    REQUEST_COUNT.labels(method="GET", endpoint="/init-db").inc()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "message": "Students table created successfully"
    })


@app.route("/students", methods=["POST"])
def add_student():
    REQUEST_COUNT.labels(method="POST", endpoint="/students").inc()

    data = request.get_json()

    if not data or "name" not in data:
        return jsonify({"error": "Name is required"}), 400

    name = data["name"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO students (name) VALUES (%s)", (name,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Student added successfully",
        "name": name
    })


@app.route("/students", methods=["GET"])
def get_students():
    REQUEST_COUNT.labels(method="GET", endpoint="/students").inc()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "source": "rds-mysql",
        "data": students
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
