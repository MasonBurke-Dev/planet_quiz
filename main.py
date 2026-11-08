"""Launch the Planet Quiz web application."""

from ui import app
#Comment

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
