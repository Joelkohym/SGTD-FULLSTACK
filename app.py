from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
    g,
)
from flask.helpers import make_response
from flask_mysqldb import MySQL
from sqlalchemy import create_engine, text
import re
import requests
import json
import threading

# import pygsheets
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import leafmap.foliumap as leafmap
import folium
import random
import time
import pytz
import os
from db_Vessel_map import get_map_data, display_map
from db_Vessel_data_pull import delete_all_rows_vessel_location, PULL_GET_VCP_VDA_MPA
from db_table_pull import (
    delete_all_rows_table_view,
    PULL_pilotage_service,
    PULL_vessel_due_to_arrive,
    validate_imo,
)
from db_table_view_request import (
    get_data_from_MPA_Vessel_Arrival_Declaration,
    get_data_from_vessel_due_to_arrive_and_depart,
    merge_arrivedepart_declaration_df,
)
from database import (
    get_user_detail,
    new_registration,
    validate_login,
    receive_details,
    new_vessel_movement,
    new_vessel_current_position,
    new_pilotage_service,
    new_vessel_due_to_arrive,
)

from flask_swagger_ui import get_swaggerui_blueprint
import logging
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta

app = Flask(__name__)
app.config['MYSQL_HOST'] = os.environ['MYSQL_HOST']
app.config['MYSQL_USER'] = os.environ['MYSQL_USER']
app.config['MYSQL_PASSWORD'] = os.environ['MYSQL_PASSWORD']
app.config['MYSQL_DB'] = os.environ['MYSQL_DB']
app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
# JWT token expiration is set to 1 hour
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)

app.secret_key = os.urandom(24)
CORS(app)
mysql = MySQL(app)

db_connection_string = os.environ['DB_CONNECTION_STRING']
engine = create_engine(db_connection_string,
                       connect_args={"ssl": {
                           "ssl_ca": "/etc/ssl/cert.pem"
                       }})


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        msg = ""
        try:
            email = request.form["email"]
            password = request.form["password"]
            login_data = validate_login(email, password)
            print(f"Login data = {login_data}")
            print(f"Length of Login data = {len(login_data)}")
            # print(f"Validate_login value returned = {validate_login(email, password)}")
            if len(login_data) == 5:
                # id = login_data[0]
                print(f"login_data[0] == {login_data[0]}")
                # API_KEY = login_data[1]
                # pID = login_data[2]
                # pitstop = login_data[3]
                # gSheet = login_data[4]

                # session["loggedin"] = True
                # session["id"] = id
                # session["email"] = email
                # session["participant_id"] = pID
                # session["pitstop_url"] = pitstop
                # session["api_key"] = API_KEY
                # session["gc"] = gSheet
                # session["IMO_NOTFOUND"] = []
                # session["IMO_FOUND"] = []

                user = {"id": login_data[0],"username": email}
                access_token = create_access_token(identity=user)

                msg = f"Login success for {email}, please enter Vessel IMO number(s)"
                print(f"Login success for {email}, redirect")
                return jsonify(access_token=access_token, msg= msg), 200
                # return render_template('vessel_request.html', msg=msg, email=email)
            else:
                msg = "Invalid credentials, please try again.."
                print("Invalid credentials, please try again..")
                return msg, 401
        except Exception as e:
            msg = "Log in failed, please contact admin."
            print("Log in failed, please contact admin.")
            return msg, 403
        # if request.data['username'] and request.data['password'] in db:
        #   user_data = load_data_from_db()
    if request.method == "GET":
        print("Request method == GET")
        msg = "GET Request to display Login page"
        return msg, 200


@app.route("/table_view", methods=["GET"])
@jwt_required()
def table_view():
    header = get_jwt_identity()
    user = get_user_detail(header["id"], header["username"])
    if user:
        msg = "Rendering Table View"
        return msg, 200
    else:
        msg = "Error while getting to table view, redirecting to login"
        print("No authorisation, redirecting to login")
        return msg, 401


@app.route("/api/table_pull", methods=["GET", "POST"])
@jwt_required()
def table_pull():
    header = get_jwt_identity()
    user = get_user_detail(header["id"], header["username"])
    if user:
        if request.method == "POST":
            # session["IMO_NOTFOUND"] = []
            # session["TABLE_IMO_NOTFOUND"] = []
            # Clear all rows in vessel_movement_UCE and vessel_current_position_UCE table
            print(f'Session gc = {user["gc"]}')
            delete_all_rows_table_view(user["gc"])
            user_vessel_imo = request.form["imo"]
            try:
                # Split vessel_imo list into invdivual records
                input_list = [int(x) for x in user_vessel_imo.split(",")]
                print(f"Pilotage service input_list from html = {input_list}")

                # ========================              START PULL pilotage_service by vessel imo                   ===========================
                # url_pilotage_service = (
                #     f"{session['pitstop_url']}/api/v1/data/pull/pilotage_service"
                # )
                # PULL_pilotage_service(
                #     url_pilotage_service,
                #     input_list,
                #     session["participant_id"],
                #     session["api_key"],
                # )
                # ========================          END PULL pilotage_service                         ===========================

                # ========================          START PULL vessel_due_to_arrive by date            ===========================
                url_vessel_due_to_arrive = (
                    f"{user['pitstop_url']}/api/v1/data/pull/vessel_due_to_arrive"
                )
                print("Start PULL_vessel_due_to_arrive thread...")
                print(datetime.now())
                threading.Thread(
                    target=PULL_vessel_due_to_arrive,
                    args=(
                        url_vessel_due_to_arrive,
                        user["participant_id"],
                        user["api_key"],
                    ),
                ).start()
                print("End PULL_vessel_due_to_arrive thread...")
                print(datetime.now())
                # PULL_vessel_due_to_arrive(
                #     url_vessel_due_to_arrive,
                #     session["participant_id"],
                #     session["api_key"],
                # )
                # ========================    END PULL vessel_due_to_arrive         ===========================

                return redirect(url_for("table_view_request", imo=user_vessel_imo)), 303
            except:
                msg = "Invalid IMO. Please ensure at IMO is valid."
                return msg, 400
        else:
            print("TABLE_PULL Method <> POST")
            msg = "Wrong method, only POST Method allowed"
            return msg, 405
    else:
        print("TABLE_PULL session['email'] is not valid")
        msg = "TABLE_PULL session['email'] is not valid"
        return msg, 401


@app.route("/table_view_request/<imo>", methods=["GET", "POST"])
@jwt_required()
def table_view_request(imo):
    header = get_jwt_identity()
    user = get_user_detail(header["id"], header["username"])
    if user:
        try:
            imo_list = imo.split(",")
            print(f"IMO ==== {imo}")
            print(f"IMO list ==== {imo_list}")

            # ======================== START GET MPA Vessel Arrival Declaration by IMO Number =============
            Declaration_df = get_data_from_MPA_Vessel_Arrival_Declaration(imo_list)
            # ======================== END GET MPA Vessel Arrival Declaration by IMO Number =============
            # ======================== START GET MPA Vessel Due to Arrive and Depart by next 99 hours  =============
            MPA_arrive_depart_df = get_data_from_vessel_due_to_arrive_and_depart()
            # ======================== END GET MPA Vessel Due to Arrive and Depart by next 99 hours =============
            # Filter the DataFrame based on imoNumbers
            filtered_df_before = MPA_arrive_depart_df[
                MPA_arrive_depart_df["vesselParticulars.imoNumber"].isin(imo_list)
            ]
            print(f"filtered_df_before = {filtered_df_before}")
            if len(filtered_df_before) == 0:
                msg = "IMO cannot be found in system, please try another IMO.. Display Table View."
                return msg, 404
            merged_filtered_df = merge_arrivedepart_declaration_df(
                filtered_df_before, Declaration_df
            )
            # if len(merged_filtered_df) == 0:
            #     msg = "IMO Numbers cannot be found in merged filtered data frame, dislay table_view.html"
            #     return msg, 404
            # # change purpose from Y,Y,N,N,N... to #1 indicator – Loading / Unloading Cargo #2 indicator – Loading / Unloading Passengers #3 indicator – Taking Bunker  #4 indicator – Taking Ship Supplies #5 indicator – Changing Crew #6 indicator – Shipyard Repair #7 indicator – Offshore Support #8 indicator – Not Used #9 indicator – Other Afloat Activities
            # else:
            print(f"merged_filtered_df = {merged_filtered_df}")
            result = merged_filtered_df.to_json(orient="table")
            print(f"Result 200 == {result}")
            return result, 200
        except Exception as e:
            print(f"Error: {e}")
            msg = "Something went wrong with the data, please ensure IMO Number is valid. Display table_view.html"
            return msg, 406
    else:
        msg = "/table_view_request/<imo> session['email'] is not valid"
        return msg, 401


# Make function for logout session
@app.route("/logout")
def logout():
    # session.pop("loggedin", None)
    # session.pop("id", None)
    # session.pop("email", None)
    # session.pop("participant_id", None)
    # session.pop("pitstop_url", None)
    # session.pop("api_key", None)
    # session.pop("gc", None)
    # session.pop("IMO_FOUND", None)
    # session.pop("IMO_NOT_FOUND", None)
    msg = "Logged out Successfully"
    return msg, 200


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    print(f"request.form = {request.form}")
    if (
        request.method == "POST"
        and "email" in request.form
        and "password" in request.form
    ):
        data = request.form
        print(data)
        r_status = new_registration(data)
        if r_status == 1:
            msg = "You have successfully registered!, please send Admin gsheet credentials file. Display Login page."
            return msg, 200
        else:
            msg = "Your email exists in database! Please reach out to Admin if you need assistance."
            return msg, 409
    elif request.method == "POST":
        msg = "Please fill out the form!"
        return msg, 406
    if request.method == "GET":
        msg = "GET Request to display Register page."
        return msg, 200
    # return render_template("register.html")


# https://sgtd-api.onrender.com/api/vessel_current_position_db/receive/test@sgtradex.com
# ==========================================       Vessel data PULL         ============================================
@app.route("/api/vessel", methods=["POST"])
@jwt_required()
def Vessel_data_pull():
    header = get_jwt_identity()
    user = get_user_detail(header["id"], header["username"])
    if user:
        if request.method == "POST":
            imo_notfound = []
            # Clear all rows in vessel_movement_UCE and vessel_current_position_UCE table
            delete_all_rows_vessel_location(user["gc"])
            user_vessel_imo = request.form["vessel_imo"]
            # Split vessel_imo list into invdivual records
            try:
                input_list = [int(x) for x in user_vessel_imo.split(",")]
                print(f"user_vessel_imo from html = {user_vessel_imo}")
                print(f"input_list from html = {input_list}")
                # Loop through input IMO list
                tic = time.perf_counter()
                # ============= GET 2 API's from MPA: VCP + VDA ===================
                # ============= PULL 2 API's from SGTD: VCP + VDA =================
                PULL_GET_VCP_VDA_MPA(
                    input_list,
                    user["pitstop_url"],
                    user["gc"],
                    user["participant_id"],
                    user["api_key"],
                    imo_notfound,
                )
                toc = time.perf_counter()
                print(
                    f"PULL duration for vessel map query {len(input_list)} in {toc - tic:0.4f} seconds"
                )
                msg = "PULL vessel map query success, redirect to vessel_map"
                return redirect(url_for("Vessel_map", imo_notfound=imo_notfound)), 303
            except Exception as e:
                print(f"Error: {e}")
                msg = "Invalid IMO. Please ensure IMO is valid."
                return msg, 406
        msg = "Wrong method, only POST Method allowed, redirect to login page"
        return msg, 403
    msg = "/api/vessel session['email'] is not valid, redirect login page"
    return msg, 401


@app.route("/vessel_request/<msg>", methods=["GET", "POST"])
@jwt_required()
def vessel_request(msg):
    header = get_jwt_identity()
    user = get_user_detail(header["id"], header["username"])
    if  user:
        msg = "Display Vessel Request Page"
        return msg, 200
    else:
        msg = "/vessel_request/<msg> session['email'] is not valid, redirect login page"
        return msg, 401


# 9490820 / 9929297
# ====================================####################MAP DB##############################========================================
@app.route("/api/vessel_map/<imo_notfound>", methods=["GET", "POST"])
@jwt_required()
def Vessel_map(imo_notfound):
    header = get_jwt_identity()
    user = get_user_detail(header["id"], header["username"])
    if user:
        print(f"VESSEL MAP PRINTING IMO_NOTFOUND = {imo_notfound}")
        DB_queried_data = get_map_data(user["gc"])
        df1 = pd.DataFrame(DB_queried_data[0])
        print(f"df1 VESSEL MAP = {df1.to_string(index=False, header=True)}")

        display_data = display_map(df1)
        if display_data[0] == 1:
            return df1

        else:
            return df1
    print("session['email']' doesn't exists, redirect to login")
    msg = "/api/vessel_map session['email'] is not valid, redirect login page"
    return msg, 401


####################################  START UPLOAD UCC #############################################
@app.route("/UCC_upload")
@jwt_required()
def UCC_upload():
    header = get_jwt_identity()
    user = get_user_detail(header["id"], header["username"])
    if user:
        email = user["email"]
        return render_template("UCC_upload.html", email=email)
    else:
        msg = "/api/vessel_map session['email'] is not valid, redirect login page"
        return msg, 401


@app.route("/api/triangular_upload", methods=["POST"])
@jwt_required()
def triangular_upload():
    header = get_jwt_identity()
    user = get_user_detail(header["id"], header["username"])
    if user:
        if request.method == "POST":
            # Get the list of files from webpage
            files = request.files.getlist("files[]")  # Use "files[]" as the key

            # Iterate for each file in the files list and save them
            for file in files:
                if file and file.filename.endswith(".csv"):  # Check if it's a CSV file
                    print(file.filename)

                    file.save(file.filename)
                else:
                    return (
                        "<h1>Invalid file format. Please upload only CSV files.</h1>",
                        415,
                    )
            return "<h1>Files Uploaded Successfully.!</h1>"
    else:
        msg = "/api/vessel_map session['email'] is not valid, redirect login page"
        return msg, 401


####################################  END UPLOAD UCC  ###############################################

##########################################################RECEIVE in MySQL DB#############################################################################################


# https://sgtd-api.onrender.com/api/vessel_due_to_arrive_db/receive/test@sgtradex.com
@app.route("/api/vessel_due_to_arrive_db/receive/<email_url>", methods=["POST"])
def RECEIVE_Vessel_due_to_arrive(email_url):
    email = email_url
    receive_details_data = receive_details(email)
    # print(f"Vessel_current_position_receive:   Receive_details from database.py {receive_details(email)}")
    API_KEY = receive_details_data[1]
    participant_id = receive_details_data[2]
    pitstop_url = receive_details_data[3]
    gsheet_cred_path = receive_details_data[4]

    data = request.data  # Get the raw data from the request body

    print(f"Vessel_due_to_arrive = {data}")

    data_str = data.decode("utf-8")  # Decode data as a UTF-8 string
    # Convert the JSON string to a Python dictionary
    data_dict = json.loads(data_str)
    row_data_vessel_due_to_arrive = data_dict["payload"]
    print(f"row_data_vessel_due_to_arrive = {row_data_vessel_due_to_arrive}")
    # ====================== Store VDA into DB =============================
    result = new_vessel_due_to_arrive(
        row_data_vessel_due_to_arrive, email, gsheet_cred_path
    )
    if result == 1:
        # Append the data as a new row
        return f"vessel_due_to_arrive Data saved to Google Sheets.{row_data_vessel_due_to_arrive}"
    else:
        return f"Email doesn't exists, unable to add data"


@app.route("/api/pilotage_service_db/receive/<email_url>", methods=["POST"])
def RECEIVE_Pilotage_service(email_url):
    email = email_url
    receive_details_data = receive_details(email)
    # print(f"Vessel_current_position_receive:   Receive_details from database.py {receive_details(email)}")
    API_KEY = receive_details_data[1]
    participant_id = receive_details_data[2]
    pitstop_url = receive_details_data[3]
    gsheet_cred_path = receive_details_data[4]

    data = request.data  # Get the raw data from the request body

    print(f"Pilotage service = {data}")

    data_str = data.decode("utf-8")  # Decode data as a UTF-8 string
    # Convert the JSON string to a Python dictionary
    data_dict = json.loads(data_str)
    row_data_pilotage_service = data_dict["payload"][-1]
    print(f"row_data_Pilotage service = {row_data_pilotage_service}")
    # ====================== Store VDA into DB =============================
    result = new_pilotage_service(data, email, gsheet_cred_path)
    if result == 1:
        # Append the data as a new row
        return (
            f"pilotage_service Data saved to Google Sheets.{row_data_pilotage_service}"
        )
    else:
        return f"Email doesn't exists, unable to add data"


# https://sgtd-api.onrender.com/api/vessel_current_position_db/receive/test@sgtradex.com
@app.route("/api/vessel_current_position_db/receive/<email_url>", methods=["POST"])
def RECEIVE_Vessel_current_position(email_url):
    email = email_url
    receive_details_data = receive_details(email)
    # print(f"Vessel_current_position_receive:   Receive_details from database.py {receive_details(email)}")
    API_KEY = receive_details_data[1]
    participant_id = receive_details_data[2]
    pitstop_url = receive_details_data[3]
    gsheet_cred_path = receive_details_data[4]

    data = request.data  # Get the raw data from the request body

    print(f"Vessel_current_position = {data}")

    data_str = data.decode("utf-8")  # Decode data as a UTF-8 string
    # Convert the JSON string to a Python dictionary
    data_dict = json.loads(data_str)
    row_data_vessel_current_position = data_dict["payload"][-1]
    print(f"row_data_vessel_current_position = {row_data_vessel_current_position}")
    result = new_vessel_current_position(
        row_data_vessel_current_position, email, gsheet_cred_path
    )
    if result == 1:
        # Append the data as a new row
        return f"Vessel Current Location Data saved to Google Sheets.{row_data_vessel_current_position}"
    else:
        return f"Email doesn't exists, unable to add data"


# https://sgtd-api.onrender.com/api/vessel_movement_db/receive/test@sgtradex.com
@app.route("/api/vessel_movement_db/receive/<email_url>", methods=["POST"])
def RECEIVE_Vessel_movement(email_url):
    email = email_url
    receive_details_data = receive_details(email)
    # print(f"Vessel_movement_receive:  Receive_details from database.py {receive_details(email)}")
    API_KEY = receive_details_data[1]
    participant_id = receive_details_data[2]
    pitstop_url = receive_details_data[3]
    gsheet_cred_path = receive_details_data[4]

    data = request.data  # Get the raw data from the request body

    data_str = data.decode("utf-8")  # Decode data as a UTF-8 string
    # Convert the JSON string to a Python dictionary
    data_dict = json.loads(data_str)
    # Extract the last item from the "payload" array
    last_payload_item = data_dict["payload"][-1]
    print(last_payload_item)
    try:
        print(
            f"Length of vessel movement end date = {len(last_payload_item['vm_vessel_movement_end_dt'])}"
        )
        row_data_vessel_movement = {
            "vm_vessel_particulars.vessel_nm": last_payload_item[
                "vm_vessel_particulars"
            ][0]["vessel_nm"],
            "vm_vessel_particulars.vessel_imo_no": last_payload_item[
                "vm_vessel_particulars"
            ][0]["vessel_imo_no"],
            "vm_vessel_particulars.vessel_flag": last_payload_item[
                "vm_vessel_particulars"
            ][0]["vessel_flag"],
            "vm_vessel_particulars.vessel_call_sign": last_payload_item[
                "vm_vessel_particulars"
            ][0]["vessel_call_sign"],
            "vm_vessel_location_from": last_payload_item["vm_vessel_location_from"],
            "vm_vessel_location_to": last_payload_item["vm_vessel_location_to"],
            "vm_vessel_movement_height": last_payload_item["vm_vessel_movement_height"],
            "vm_vessel_movement_type": last_payload_item["vm_vessel_movement_type"],
            "vm_vessel_movement_start_dt": last_payload_item[
                "vm_vessel_movement_start_dt"
            ],
            "vm_vessel_movement_end_dt": last_payload_item["vm_vessel_movement_end_dt"],
            "vm_vessel_movement_status": last_payload_item["vm_vessel_movement_status"],
            "vm_vessel_movement_draft": last_payload_item["vm_vessel_movement_draft"],
        }
    except:
        print("================no movement end date, printing exception===============")
        row_data_vessel_movement = {
            "vm_vessel_particulars.vessel_nm": last_payload_item[
                "vm_vessel_particulars"
            ][0]["vessel_nm"],
            "vm_vessel_particulars.vessel_imo_no": last_payload_item[
                "vm_vessel_particulars"
            ][0]["vessel_imo_no"],
            "vm_vessel_particulars.vessel_flag": last_payload_item[
                "vm_vessel_particulars"
            ][0]["vessel_flag"],
            "vm_vessel_particulars.vessel_call_sign": last_payload_item[
                "vm_vessel_particulars"
            ][0]["vessel_call_sign"],
            "vm_vessel_location_from": last_payload_item["vm_vessel_location_from"],
            "vm_vessel_location_to": last_payload_item["vm_vessel_location_to"],
            "vm_vessel_movement_height": last_payload_item["vm_vessel_movement_height"],
            "vm_vessel_movement_type": last_payload_item["vm_vessel_movement_type"],
            "vm_vessel_movement_start_dt": last_payload_item[
                "vm_vessel_movement_start_dt"
            ],
            "vm_vessel_movement_end_dt": "",
            "vm_vessel_movement_status": last_payload_item["vm_vessel_movement_status"],
            "vm_vessel_movement_draft": last_payload_item["vm_vessel_movement_draft"],
        }
    # Append the data to the worksheet
    print(f"row_data_vessel_movement: {row_data_vessel_movement}")

    result = new_vessel_movement(row_data_vessel_movement, email, gsheet_cred_path)
    if result == 1:
        # Append the data as a new row
        return f"Vessel Current Location Data saved to Google Sheets.{row_data_vessel_movement}"
    else:
        return f"Email doesn't exists, unable to add data"


@app.route("/api/others/receive/<email_url>", methods=["POST"])
def RECEIVE_Others(email_url):
    email = email_url
    response_data = {"message": f"Received others from {email_url}"}
    return jsonify(response_data)


##########################################################MySQL DB#############################################################################################


# @app.before_request
# def before_request():
#     g.user = None
#     if "email" in session:
#         session["email"] = session["email"]


# ====================================####################MAP DB##############################========================================


# @app.after_request
# def after_request(response):
#     response.headers[
#         "Cache-Control"
#     ] = "no-cache, no-store, must-revalidate, public, max-age=0"
#     response.headers["Expires"] = 0
#     response.headers["Pragma"] = "no-cache"
#     return response


# Configure Swagger UI
SWAGGER_URL = "/swagger"
API_URL = "/swagger.json"
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "SGTD Vessel Query API Swagger"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.route("/swagger.json")
def swagger():
    with open("swagger.json", "r") as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
