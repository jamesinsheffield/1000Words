from flask import Flask
import os

app = Flask(__name__)
assert "APP_SETTINGS" in os.environ, "APP_SETTINGS environment variable not set"
app.config.from_object(os.environ['APP_SETTINGS'])

@app.route("/")
def hello():
    return "<h1>Hello World!</h1>"

if __name__ == "__main__":
    app.run()
