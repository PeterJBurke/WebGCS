import requests
import sys

# Use the standard port configured in app.py
WEB_SERVER_PORT = 5000
url = f'http://127.0.0.1:{WEB_SERVER_PORT}/'

print(f"Attempting to access web server at: {url}")
print("(Requires the 'python app.py' process to be running)")

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

    # Check for a key element from the HTML (e.g., the title)
    # Update this if you changed the title in index.html
    if "<title>Drone Control Interface</title>" in response.text:
        print("SUCCESS: Web server is running and responded with expected content.")
        sys.exit(0)
    else:
        print("FAILED: Web server responded, but the content seems incorrect.")
        print("  (Check if the correct index.html is being served)")
        # Optionally print some response text for debugging:
        # print("\nResponse Text (first 500 chars):\n", response.text[:500])
        sys.exit(1)

except requests.exceptions.ConnectionError:
    print(f"FAILED: Could not connect to the server at {url}.")
    print("  Is the 'python app.py' script running?")
    sys.exit(1)
except requests.exceptions.Timeout:
    print(f"FAILED: The request timed out.")
    print("  Is the 'python app.py' script running and responsive?")
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"FAILED: An error occurred while accessing the web server: {e}")
    sys.exit(1)
