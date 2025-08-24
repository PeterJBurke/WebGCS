from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World! Flask test server is working."

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    print("Starting test Flask server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
