from flask import Flask, render_template

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# Serve React app for root
@app.route("/")
def index():
    return render_template("index.html")

# Serve React app for /entrepreneured and ALL subpaths
@app.route("/entrepreneured")
@app.route("/entrepreneured/<path:path>")
def entrepreneured(path=None):
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)