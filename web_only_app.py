from flask import Flask, render_template, send_from_directory
import time

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'desktop_drone_secret!'

@app.route('/')
def index():
    return render_template("index.html", version="v2.63-Desktop-TCP-WebOnly")

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/health')
def health_check():
    print("HEALTH CHECK ENDPOINT HIT")
    return "OK", 200

if __name__ == '__main__':
    print("Starting web-only WebGCS server on http://0.0.0.0:5000")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Exception during app.run: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("app.run block finished")
