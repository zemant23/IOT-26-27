from flask import Flask, jsonify, request, render_template
from projects import PROJECTS
from hardware import get_sensor

app = Flask(__name__)
sensor = get_sensor()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/projects")
def projects():
    return jsonify(PROJECTS)

@app.route("/api/ultrasonic")
def ultrasonic():
    since = float(request.args.get("since", 0))
    return jsonify(value=sensor.value, running=sensor.running, display=sensor.display_on,
                   mode=sensor.mode, text=sensor.text, lcd_error=sensor.lcd_error,
                   history=[h for h in sensor.history if h[0] > since])

@app.route("/api/ultrasonic/control", methods=["POST"])
def control():
    d = request.get_json(force=True)
    if "running" in d: sensor.running = bool(d["running"])
    if "display" in d: sensor.display_on = bool(d["display"])
    return jsonify(running=sensor.running, display=sensor.display_on)

@app.route("/api/ultrasonic/lcd", methods=["POST"])
def lcd():
    d = request.get_json(force=True)
    if d.get("mode") == "text":
        sensor.set_text(d.get("line1", ""), d.get("line2", ""))
    else:
        sensor.mode = "distance"
    return jsonify(mode=sensor.mode, text=sensor.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
