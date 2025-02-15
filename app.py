from flask import Flask, request, render_template, jsonify
import subprocess
import re
import os
from prometheus_client import make_wsgi_app, Counter, Gauge, Histogram
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)

DEBUG_PRINT = os.environ.get("DEBUG_PRINT", "true").lower() == "true"

# Prometheus metrics (Define these BEFORE the middleware)
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status_code'])
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'HTTP request latency', ['method', 'endpoint'])
SUBDOMAIN_ENUMERATION_COUNT = Counter('subdomain_enumeration_total', 'Total subdomain enumerations')
ALIVE_SUBDOMAINS_COUNT = Gauge('alive_subdomains_count', 'Number of alive subdomains')
DEAD_SUBDOMAINS_COUNT = Gauge('dead_subdomains_count', 'Number of dead subdomains')

# Correctly integrate Prometheus middleware (Do this ONLY ONCE)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})

def debug_print(message):
    if DEBUG_PRINT:
        print(message)

@app.route("/", methods=["GET"])
def index():
    results = None
    error = None
    domain = None

    debug_print("Request received")

    if "domain" in request.args:
        domain = request.args.get("domain")
        debug_print(f"Domain received: {domain}")

        if not domain:
            error = "Please enter a domain."
        elif "." not in domain:
            error = "Invalid domain format."
        else:
            try:
                debug_print("About to call run_subfinder_locally")
                results = run_subfinder_locally(domain)
                debug_print(f"Results from run_subfinder_locally: {results}")

                # Update Prometheus metrics
                if results and results.get("prometheus_data"):
                    SUBDOMAIN_ENUMERATION_COUNT.inc()
                    alive_count = sum(1 for sub in results["prometheus_data"] if sub.get("status") == "Alive")
                    dead_count = sum(1 for sub in results["prometheus_data"] if sub.get("status") == "Dead")
                    ALIVE_SUBDOMAINS_COUNT.set(alive_count)
                    DEAD_SUBDOMAINS_COUNT.set(dead_count)

                best_type = request.accept_mimetypes.best_match(['application/json', 'text/html'])

                if best_type == 'application/json':
                    return jsonify(results), 200
                elif best_type == 'text/html':
                    return render_template("index.html", results=results, error=error, domain=domain), 200
                else:
                    return render_template("index.html", results=results, error=error, domain=domain), 200

            except Exception as e:
                error = f"An error occurred: {str(e)}"
                debug_print(f"Error: {error}")
                best_type = request.accept_mimetypes.best_match(['application/json', 'text/html'])
                if best_type == 'application/json':
                    return jsonify({"error": error}), 500
                else:
                    return render_template("index.html", error=error, domain=domain), 500

    debug_print("Returning initial HTML")
    return render_template("index.html", results=results, error=error, domain=domain)


def run_subfinder_locally(domain):
    try:
        command = ["./script1.sh", domain]
        debug_print(f"Running command: {command}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if stderr:
            debug_print(f"Subprocess stderr: {stderr}")

        ansi_escape = re.compile(r'\x1b\[[0-9;]*[mG]')
        cleaned_stdout = ansi_escape.sub('', stdout)

        subdomains_data = []
        prometheus_data = []

        for line in cleaned_stdout.splitlines():
            if "," in line:  # Comma-separated line (Prometheus)
                parts = line.split(",")
                if len(parts) == 3:  # Check if it has 3 parts
                    subdomain = parts[0].strip()
                    status = parts[1].strip()
                    ip = parts[2].strip()
                    prometheus_data.append({"subdomain": subdomain, "status": status, "ip": ip})
            else:  # Original line (Web app)
                parts = line.split("|")  # Split by pipe
                if len(parts) == 3:
                    subdomain = parts[0].strip()
                    status = parts[1].strip()
                    ip = parts[2].strip()
                    subdomains_data.append({"subdomain": subdomain, "status": status, "ip": ip})

        return {"subdomains": subdomains_data, "prometheus_data": prometheus_data}
    except subprocess.CalledProcessError as e:
        debug_print(f"CalledProcessError: {e}")
        return {"error": str(e)}
    except FileNotFoundError:
        debug_print("FileNotFoundError: script1.sh not found")
        return {"error": "script1.sh not found. Make sure it's in the same directory as app.py"}
    except Exception as e:
        debug_print(f"Exception in run_subfinder_locally: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
