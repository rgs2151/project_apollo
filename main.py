from flask import Flask, render_template, request, g
from flask_cors import CORS
from health_gpt import FileHistoryWithFAISS, DocumentKeyValuePairExtraction
from registry import APIRegistry, APIRegistryBaseParameter, API_MAPS
import requests
import numpy as np
# client = OpenAI(api_key=api_key)

MODE = "DEV"

API_REGISTER = APIRegistry(API_MAPS, base_params = APIRegistryBaseParameter(MODE).base_params)


app = Flask(__name__)
CORS(app)

import conversation as conv



@app.before_request
def authenticate():
    token = request.headers.get('Authorization', None)
    user_details = None
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        api = API_REGISTER.get_api("user-details")
        response = requests.get(api, headers=headers)
        # print(response.content)
        if response.status_code == 200 and not "error" in response.json():
            user_details = response.json()

    g.user_details = user_details


@app.route("/test", methods=["POST"])
def test():

    if not g.user_details: return {"error": "unauthorized"}
    user_id = g.user_details.get("user_details", {}).get("user", {}).get('id', None)
    if not user_id: return {"error": {"code": "Internal server error", "message": "something went wrong"}}

    FH = FileHistoryWithFAISS({
        "columns": ["parameter_label", "parameter_type", "parameter_value"],
        "indexes": ["parameter_label"]
    }, user_id, "./history", name="history")
    retrieved = FH.retrieve()
    
    print("user_id", g.user_details)
    print("retrieved", retrieved)

    return {"status": "success"}

# Route for the app
@app.route("/")
def application():
    return render_template("index.html")

# Route to save the uploaded file
@app.route("/upload", methods=["POST"])
def upload():

    if request.method == "POST":

        if not g.user_details: return {"error": "unauthorized"}
        user_id = g.user_details.get("user_details", {}).get("user", {}).get('id', None)
        if not user_id: return {"error": {"code": "Internal server error", "message": "something went wrong"}}

        # Get the file from the request
        file = request.files["file"]
        
        DKVPE = DocumentKeyValuePairExtraction(file.read())

        # Save the file
        file.save("data/raw/" + file.filename)

        responses, stash = DKVPE.extract()
        
        FH = FileHistoryWithFAISS({
            "columns": ["parameter_label", "parameter_type", "parameter_value"],
            "indexes": ["parameter_label"]
        }, user_id, history_location="./history", name="history")
        FH.update(DKVPE.get_results(stash))

        # Return success
        return {"status": "success"}

@app.route("/speech", methods=["POST"])
def speech():
    if request.method == "POST":

        if not g.user_details: return {"error": "unauthorized"}
        user_id = g.user_details.get("user_details", {}).get("user", {}).get('id', None)
        if not user_id: return {"error": {"code": "Internal server error", "message": "something went wrong"}}
        
        # Get the file from the request
        new_prompt = request.json["prompt"]
        # new_prompt = request.form["prompt"]
        
        # handle new prompt in the conversation

        FH = FileHistoryWithFAISS({
            "columns": ["parameter_label", "parameter_type", "parameter_value"],
            "indexes": ["parameter_label"]
        }, user_id, history_location="./history")
        to_user, flag_for_front = conv.ingest_user_input(new_prompt, FH)

        return {"status": "success", "response": to_user, "flag": flag_for_front}

@app.route("/data", methods=["GET"])
def data():
    # if not g.user_details: return {"error": "unauthorized"}
    # user_id = g.user_details.get("user_details", {}).get("user", {}).get('id', None)
    # if not user_id: return {"error": {"code": "Internal server error", "message": "something went wrong"}}
    
    # FH = FileHistoryWithFAISS(user_id, history_location="./history")
    FH = FileHistoryWithFAISS(1, history_location="./history")
    retrieved = FH.retrieve().replace({np.nan: None})
    
    return {"status": "success", "data": retrieved.to_dict("records")}

@app.route("/goal", methods=["GET"])
def goal():

    if request.method == "GET":
        
        if not g.user_details: return {"error": "unauthorized"}
        user_id = g.user_details.get("user_details", {}).get("user", {}).get('id', None)
        if not user_id: return {"error": {"code": "Internal server error", "message": "something went wrong"}}

        FH = FileHistoryWithFAISS({
            "columns": ["goal", "reminder", "progress"],
            "indexes": ["goal"]
        }, user_id, history_location="./history", name="goal")

        data = FH.retrieve().replace({np.nan: None}).to_dict("records")

        return {"data": data}


@app.route("/auth", methods=["POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]


# Set the port
# Run the app
if __name__ == "__main__":
    # fuser -k 8000/tcp
    app.run(host="0.0.0.0", port=8000, debug=True)