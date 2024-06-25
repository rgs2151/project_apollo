from flask import Flask, render_template, request
from flask_cors import CORS
from health_gpt import FileHistoryWithFAISS, DocumentKeyValuePairExtraction

# client = OpenAI(api_key=api_key)
app = Flask(__name__)
CORS(app)

import conversation as conv

FH = FileHistoryWithFAISS(10, history_location="./history")


# Route for the login page
@app.route("/")
def home():
    return render_template("login.html")

# Route for the app
@app.route("/app")
def application():
    return render_template("index.html")

# Route to save the uploaded file
@app.route("/upload", methods=["POST"])
def upload():
    if request.method == "POST":
        # Get the file from the request
        file = request.files["file"]
        
        DKVPE = DocumentKeyValuePairExtraction(file.read())

        # Save the file
        file.save("data/raw/" + file.filename)

        responses, stash = DKVPE.extract()
        
        FH.update(DKVPE.get_results(stash))

        # Return success
        return {"status": "success"}

@app.route("/speech", methods=["POST"])
def speech():
    if request.method == "POST":
        
        # Get the file from the request
        # new_prompt = request.json["prompt"]
        new_prompt = request.form["prompt"]
        
        # handle new prompt in the conversation

        to_user, flag_for_front = conv.ingest_user_input(new_prompt, FH)

        return {"status": "success", "response": to_user, "flag": flag_for_front}

@app.route("/auth", methods=["POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "alpha" and password == "alpha":
            return {"status": "success"}
        else:
            return {"status": "error"}

# Set the port
# Run the app
if __name__ == "__main__":
    # fuser -k 8000/tcp
    app.run(host="0.0.0.0", port=8000, debug=True)