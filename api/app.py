from flask import Flask
from flask import Flask, request, jsonify
from flask_cors import CORS
from app.services.auth_service import AuthService

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return {"status": "Backend Connected"}

if __name__ == "__main__":
    app.run(debug=True)