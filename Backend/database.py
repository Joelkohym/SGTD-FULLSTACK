from sqlalchemy import create_engine, text
import pandas as pd
import os
import json
from datetime import datetime

# db_connection_string = os.environ['DB_CONNECTION_STRING']
# db_connection_string = "mysql+pymysql://2j104pgpfhay9dokc46k:pscale_pw_fiA5JrG88BcLgKuQmmK9WZHjaOlzf2BkRisjOD6FDn6@aws.connect.psdb.cloud/sgtd?charset=utf8mb4"
db_connection_string = "mysql+pymysql://8c5qff8fhgi0sz6adth2:pscale_pw_k1WZMRjpR4X9iVfFadNWQM6o2o2lscav9ydrcM5Qfdp@aws.connect.psdb.cloud/sgtd?charset=utf8mb4"
engine = create_engine(
    db_connection_string, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
)


def load_data_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("select * from userDB"))
        result_all = result.all()
        print(f"result = {result_all}")
        user_data = []
        for row in result_all:
            user_data.append(dict(row._mapping))
        print(f"result_dicts = {user_data}")
    return user_data


def load_user_from_db(email, password):
    with engine.connect() as conn:
        email = email
        password = password
        result = conn.execute(
            text("select * from userDB WHERE email = :email and password = :password")
        )
        result_all = result.all()
        if len(result_all) == 0:
            return None
        else:
            return dict(result[0])


# def new_registration(email, password, api_key, participant_id, on_behalf_id, gsheet_cred_path, company):
def new_registration(data):
    print(f"printing data from new_registration: {data}")
    print(f"data['email'] == {data['email']}")
    print(f"data['api_key'] == {data['api_key']}")
    print(f"data['participant_id'] == {data['participant_id']}")
    email = data["email"]
    password = data["password"]
    with engine.connect() as conn:
        query = text("select * from userDB WHERE email = :email")
        values = {"email": email}
        result = conn.execute(query, values)
        result_all = result.all()
        print(result_all)
        print(f"length of result all = {len(result_all)}")
        if len(result_all) == 0:
            query = text(
                "INSERT INTO userDB (email, password, api_key, participant_id, pitstop_url, gsheet_cred_path) VALUES (:email,:password, :api_key, :participant_id, :pitstop_url, :gsheet_cred_path)"
            )
            values = {
                "email": data["email"],
                "password": data["password"],
                "api_key": data["api_key"],
                "participant_id": data["participant_id"],
                "pitstop_url": data["pitstop_url"],
                "gsheet_cred_path": data["gsheet_cred_path"],
            }
            print(query)
            result = conn.execute(query, values)
            print("execute success")
            return 1
        else:
            print("User exists, please try again")
            return 0
        # conn.execute(query, email = data['email'],password =data['password'],api_key = data['api_key'],participant_id = data['participant_id'],on_behalf_id_ = data['on_behalf_id_'],gsheet_cred_path = data['gsheet_cred_path'], company_ = data['company_'])


def validate_login(email, password):
    print(f"printing data from validate_login: email = {email}, password = {password}")

    with engine.connect() as conn:
        query = text(
            "SELECT * FROM userDB WHERE email = :email AND password = :password"
        )
        values = {"email": email, "password": password}
        check_login = conn.execute(query, values)
        login_entry = check_login.all()[0]
        print(f"check_login == {login_entry}")
        print(f"check_login TYPE == {type(login_entry)}")
        print(f"check_login_API == {login_entry[3]}")
        result_login = len(login_entry)
        print(login_entry[3], login_entry[4], login_entry[5])
        print(f"result_login == {result_login}")
        if result_login > 1:
            print("Login success")
            return (
                login_entry[0],
                login_entry[3],
                login_entry[4],
                login_entry[5],
                login_entry[6],
            )
        else:
            print("Error in Login")
            return 0


def receive_details(email):
    with engine.connect() as conn:
        query = text("SELECT * FROM userDB WHERE email = :email")
        values = {"email": email}
        receive_db = conn.execute(query, values)
        receive_data = receive_db.all()[0]
        # print(f"receive_data == {receive_data}, return api ={receive_data[3]}, return pID = {receive_data[4]}, return pitstop = {receive_data[5]}")
    return (
        receive_data[0],
        receive_data[3],
        receive_data[4],
        receive_data[5],
        receive_data[6],
    )


#######################################################        START RECEIVED DATA FROM API     #######################################################
def new_vessel_current_position(data, email, gsheet_cred_path):
    engine_vcp = create_engine(
        gsheet_cred_path, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )
    with engine_vcp.connect() as conn:
        query_vcp = text(
            """
    INSERT INTO vessel_current_position_UCE (vessel_nm,vessel_imo_no,vessel_call_sign,vessel_flag,vessel_length,vessel_depth,vessel_type,vessel_grosstonnage,vessel_nettonnage,vessel_deadweight,vessel_mmsi_number,vessel_year_built,vessel_latitude,vessel_longitude,vessel_latitude_degrees,vessel_longitude_degrees,vessel_speed,vessel_course,vessel_heading,vessel_time_stamp
    ) VALUES (:vessel_nm,:vessel_imo_no,:vessel_call_sign,:vessel_flag,:vessel_length,:vessel_depth,:vessel_type,:vessel_grosstonnage,:vessel_nettonnage,:vessel_deadweight,:vessel_mmsi_number,:vessel_year_built,:vessel_latitude,:vessel_longitude,:vessel_latitude_degrees,:vessel_longitude_degrees,:vessel_speed,:vessel_course,:vessel_heading,:vessel_time_stamp
    )
"""
        )

        values_vcp = {
            "vessel_nm": data["vessel_particulars"][0]["vessel_nm"],
            "vessel_imo_no": data["vessel_particulars"][0]["vessel_imo_no"],
            "vessel_call_sign": data["vessel_particulars"][0]["vessel_call_sign"],
            "vessel_flag": data["vessel_particulars"][0]["vessel_flag"],
            "vessel_length": data["vessel_length"],
            "vessel_depth": data["vessel_depth"],
            "vessel_type": data["vessel_type"],
            "vessel_grosstonnage": data["vessel_grosstonnage"],
            "vessel_nettonnage": data["vessel_nettonnage"],
            "vessel_deadweight": data["vessel_deadweight"],
            "vessel_mmsi_number": data["vessel_mmsi_number"],
            "vessel_year_built": data["vessel_year_built"],
            "vessel_latitude": data["vessel_latitude"],
            "vessel_longitude": data["vessel_longitude"],
            "vessel_latitude_degrees": data["vessel_latitude_degrees"],
            "vessel_longitude_degrees": data["vessel_longitude_degrees"],
            "vessel_speed": data["vessel_speed"],
            "vessel_course": data["vessel_course"],
            "vessel_heading": data["vessel_heading"],
            "vessel_time_stamp": data["vessel_time_stamp"],
        }

        result = conn.execute(query_vcp, values_vcp)
    print("New vessel_current_position execute success")
    return 1


def new_vessel_movement(data, email, gsheet_cred_path):
    engine_vm = create_engine(
        gsheet_cred_path, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )
    with engine_vm.connect() as conn:
        query_vm = text(
            "INSERT INTO vessel_movement_UCE (    vessel_nm,vessel_imo_no,vessel_flag,vessel_call_sign,vessel_location_from,vessel_location_to,vessel_movement_height,vessel_movement_type,vessel_movement_start_dt,vessel_movement_end_dt,vessel_movement_status,vessel_movement_draft) VALUES (:vessel_nm,:vessel_imo_no,:vessel_flag,:vessel_call_sign,:vessel_location_from,:vessel_location_to,:vessel_movement_height,:vessel_movement_type,:vessel_movement_start_dt,:vessel_movement_end_dt,:vessel_movement_status,:vessel_movement_draft)"
        )

        values_vm = {
            "vessel_nm": data["vm_vessel_particulars.vessel_nm"],
            "vessel_imo_no": data["vm_vessel_particulars.vessel_imo_no"],
            "vessel_flag": data["vm_vessel_particulars.vessel_flag"],
            "vessel_call_sign": data["vm_vessel_particulars.vessel_call_sign"],
            "vessel_location_from": data["vm_vessel_location_from"],
            "vessel_location_to": data["vm_vessel_location_to"],
            "vessel_movement_height": data["vm_vessel_movement_height"],
            "vessel_movement_type": data["vm_vessel_movement_type"],
            "vessel_movement_start_dt": data["vm_vessel_movement_start_dt"],
            "vessel_movement_end_dt": data["vm_vessel_movement_end_dt"],
            "vessel_movement_status": data["vm_vessel_movement_status"],
            "vessel_movement_draft": data["vm_vessel_movement_draft"],
        }

        result = conn.execute(query_vm, values_vm)
    print("New vessel_current_position execute success")
    return 1


def new_pilotage_service(data, email, gsheet_cred_path):
    engine_pilot = create_engine(
        gsheet_cred_path, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )
    with engine_pilot.connect() as conn:
        query_pilot = text(
            "INSERT INTO pilotage_service_UCE (     pilotage_cst_dt_time,pilotage_arrival_dt_time,pilotage_onboard_dt_time,pilotage_start_dt_time,pilotage_end_dt_time,pilotage_nm,pilotage_imo,pilotage_loc_to_code,pilotage_loc_from_code) VALUES (:pilotage_cst_dt_time, :pilotage_arrival_dt_time, :pilotage_onboard_dt_time, :pilotage_start_dt_time, :pilotage_end_dt_time, :pilotage_nm, :pilotage_imo, :pilotage_loc_to_code, :pilotage_loc_from_code)"
        )

        values_pilot = {
            "pilotage_cst_dt_time": data["pilotage_cst_dt_time"],
            "pilotage_arrival_dt_time": data["pilotage_arrival_dt_time"],
            "pilotage_onboard_dt_time": data["pilotage_onboard_dt_time"],
            "pilotage_start_dt_time": data["pilotage_start_dt_time"],
            "pilotage_end_dt_time": data["pilotage_end_dt_time"],
            "pilotage_nm": data["pilotage_nm"],
            "pilotage_imo": data["pilotage_imo"],
            "pilotage_loc_to_code": data["pilotage_loc_to_code"],
            "pilotage_loc_from_code": data["pilotage_loc_from_code"],
        }

        result = conn.execute(query_pilot, values_pilot)
    print("New pilotage_service execute success")
    return 1


def new_vessel_due_to_arrive(data, email, gsheet_cred_path):
    engine_VDA = create_engine(
        gsheet_cred_path, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )

    # Clean up entire VDA data array - can be 300+ into proper columns before storing in SQL DB
    # Insert each JSON object into the table
    values = []
    # insert_query = """
    #     INSERT INTO vessel_due_to_arrive_UCE (vessel_name, call_sign, imo_number, flag, due_to_arrive_dt, location_from, location_to)
    #     VALUES (%s, %s, %s, %s, %s, %s, %s)
    #     """
    #    INSERT INTO vessel_due_to_arrive_UCE (vessel_name, call_sign, imo_number, flag, due_to_arrive_dt, location_from, location_to) VALUES (:vessel_name, :call_sign, :imo_number, :flag, :due_to_arrive_dt, :location_from, :location_to)
    query_VDA = text(
        "INSERT INTO vessel_due_to_arrive_UCE (vessel_name, call_sign, imo_number, flag, due_to_arrive_dt, location_from, location_to) VALUES (:vessel_name, :call_sign, :imo_number, :flag, :due_to_arrive_dt, :location_from, :location_to)"
    )

    for item in data:
        vessel_particulars = item["vda_vessel_particulars"]
        vessel_name = vessel_particulars[0]["vessel_nm"]
        call_sign = vessel_particulars[0]["vessel_call_sign"]
        imo_number = vessel_particulars[0]["vessel_imo_no"]
        flag = vessel_particulars[0]["vessel_flag"]
        due_to_arrive_dt = item["vda_vessel_due_to_arrive_dt"]
        due_to_arrive_dt = datetime.fromisoformat(
            due_to_arrive_dt.replace("Z", "+00:00")
        ).strftime("%Y-%m-%d %H:%M:%S")
        location_from = item["vda_vessel_location_from"]
        location_to = item["vda_vessel_location_to"]

        # values = (vessel_name, call_sign, imo_number, flag, due_to_arrive_dt, location_from, location_to)
        # values.append((vessel_name, call_sign, imo_number, flag, due_to_arrive_dt, location_from, location_to))
        values.append(
            {
                "vessel_name": vessel_name,
                "call_sign": call_sign,
                "imo_number": imo_number,
                "flag": flag,
                "due_to_arrive_dt": due_to_arrive_dt,
                "location_from": location_from,
                "location_to": location_to,
            }
        )

    with engine_VDA.connect() as conn:
        result = conn.execute(query_VDA, values)
        conn.commit()
        # result = conn.executemany(insert_query, values)
        # result = conn.execute(query_pilot, values_pilot)

    print("New new_vessel_due_to_arrive execute success")
    return 1


#######################################################        END RECEIVED DATA FROM API     #######################################################


# Merge database data for MAP
def get_map_data(db_creds):
    print("Start of get_map_data......")
    engine = create_engine(
        db_creds, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )
    with engine.connect() as conn:
        # Select vessel_movement_UCE
        # query = text("select * from vessel_movement_UCE")
        # result_VM = conn.execute(query)
        # result_all_VM = result_VM.fetchall()
        # column_names_VM = result_VM.keys()
        # print(result_all_VM)
        # print(f"length of result_all_VM = {len(result_all_VM)}")
        # df1 = pd.DataFrame(result_all_VM, columns=column_names_VM)

        # Select MPA_vessel_data
        query = text("select * from MPA_vessel_data")
        result_VCP = conn.execute(query)
        result_all_VCP = result_VCP.fetchall()
        column_names_VCP = result_VCP.keys()
        print(result_all_VCP)
        print(f"length of result_all_VCP = {len(result_all_VCP)}")
        df2 = pd.DataFrame(result_all_VCP, columns=column_names_VCP)
        # sorting by first name
        df2.drop_duplicates(subset="imoNumber", keep="last", inplace=True)

        # Select MPA_arrivaldeclaration
        query = text("select * from MPA_arrivaldeclaration")
        result_ETA = conn.execute(query)
        result_all_ETA = result_ETA.fetchall()
        column_names_ETA = result_ETA.keys()
        print(result_all_ETA)
        print(f"length of result_all_ETA = {len(result_all_ETA)}")
        df3 = pd.DataFrame(result_all_ETA, columns=column_names_ETA)
        df3.drop(columns=["call_sign", "flag", "vessel_name"], inplace=True)
        df3.drop_duplicates(subset="imo_number", keep="last", inplace=True)
        new_df = pd.merge(
            df2, df3, left_on=df2["imoNumber"], right_on=df3["imo_number"], how="inner"
        )
        if "key_0" in new_df.columns:
            new_df.drop(columns=["key_0"], inplace=True)
        new_df.drop(columns=["id_x", "id_y", "imo_number"], inplace=True)
        # print(f"Final Result all vm = {[df1, new_df]}")
        # return [df1, new_df]
        print(f"Final Result all vm = {[new_df]}")
        return [new_df]


def delete_all_rows_vessel_location(db_creds):
    print(
        "Start of delete_all_rows_vessel_location 3 tables: vessel_movement_UCE, vessel_current_position_UCE, MPA_vessel_data......"
    )
    engine = create_engine(
        db_creds, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )
    with engine.connect() as conn:
        # query_VM = text("DELETE FROM vessel_movement_UCE where id > 0")
        # result_VM = conn.execute(query_VM)
        # print("Deleted vessel_movement_UCE where id > 0")
        query_VCP = text("DELETE FROM vessel_current_position_UCE where id > 0")
        result_VCP = conn.execute(query_VCP)
        print("Deleted vessel_current_position_UCE where id > 0")
        query_MPA = text("DELETE FROM MPA_vessel_data WHERE id > 0")
        result_MPA = conn.execute(query_MPA)
        print("Deleted MPA_vessel_data where id > 0")


# Store data into MPA_vessel_data from GET
def MPA_GET(api_response, gsheet_cred_path):
    data_list = json.loads(api_response)
    print(f"API response = {(data_list)}")
    print(f"API response[0] = {data_list[0]}")
    vessel_data = data_list[0]["vesselParticulars"]
    print(f"vessel_data = {vessel_data}")
    print(f"vessel_data['vesselName'] = {vessel_data['vesselName']}")
    print(f"vessel_data['callSign'] = {vessel_data['callSign']}")
    latitude = data_list[0]["latitude"]
    print(f"latitude = {data_list[0]['latitude']}")
    longitude = data_list[0]["longitude"]
    latitude_degrees = data_list[0]["latitudeDegrees"]
    longitude_degrees = data_list[0]["longitudeDegrees"]
    speed = data_list[0]["speed"]
    course = data_list[0]["course"]
    heading = data_list[0]["heading"]
    timestamp = data_list[0]["timeStamp"]

    query = text(
        "INSERT INTO MPA_vessel_data (vesselName, callSign, imoNumber, flag, vesselLength, vesselBreadth, vesselDepth, vesselType, grossTonnage, netTonnage, deadweight, mmsiNumber, yearBuilt, latitude, longitude, latitudeDegrees, longitudeDegrees, speed, course, heading, timeStamp) VALUES (:vesselName, :callSign, :imoNumber, :flag, :vesselLength, :vesselBreadth, :vesselDepth, :vesselType, :grossTonnage, :netTonnage, :deadweight, :mmsiNumber, :yearBuilt, :latitude, :longitude, :latitudeDegrees, :longitudeDegrees, :speed, :course, :heading, :timeStamp)"
    )
    values = {
        "vesselName": vessel_data["vesselName"],
        "callSign": vessel_data["callSign"],
        "imoNumber": vessel_data["imoNumber"],
        "flag": vessel_data["flag"],
        "vesselLength": vessel_data["vesselLength"],
        "vesselBreadth": vessel_data["vesselBreadth"],
        "vesselDepth": vessel_data["vesselDepth"],
        "vesselType": vessel_data["vesselType"],
        "grossTonnage": vessel_data["grossTonnage"],
        "netTonnage": vessel_data["netTonnage"],
        "deadweight": vessel_data["deadweight"],
        "mmsiNumber": vessel_data["mmsiNumber"],
        "yearBuilt": vessel_data["yearBuilt"],
        "latitude": latitude,
        "longitude": longitude,
        "latitudeDegrees": latitude_degrees,
        "longitudeDegrees": longitude_degrees,
        "speed": speed,
        "course": course,
        "heading": heading,
        "timeStamp": timestamp,
    }

    engine_MPA_GET = create_engine(
        gsheet_cred_path, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )
    with engine_MPA_GET.connect() as conn:
        MPA_Data = conn.execute(query, values)
    return MPA_Data


def MPA_GET_arrivaldeclaration(api_response, gsheet_cred_path):
    data_list = json.loads(api_response)
    print(f"API response = {(data_list)}")
    print(f"API response[0] = {data_list[0]}")

    # Initialize variables to keep track of the latest record and time
    latest_record = None
    latest_time = None
    # Iterate through the list of records
    for record in data_list:
        reported_arrival_time = record.get("reportedArrivalTime")

        # Check if reported_arrival_time is not None and greater than the latest_time
        if reported_arrival_time and (
            latest_time is None or reported_arrival_time > latest_time
        ):
            latest_record = record
            latest_time = reported_arrival_time

        # Print the latest record
    if latest_record:
        print(json.dumps(latest_record, indent=4))
    else:
        print("No records with reported arrival times found.")

    # Your JSON data
    vessel_data = latest_record

    # Create a SQL query with placeholders for the values
    query = text(
        """
      INSERT INTO MPA_arrivaldeclaration (
          vessel_name, call_sign, imo_number, flag, 
          location, grid, purpose, agent, reported_arrival_time
      ) VALUES (
          :vessel_name, :call_sign, :imo_number, :flag, 
          :location, :grid, :purpose, :agent, :reported_arrival_time
      )
  """
    )

    # Prepare the values
    values = {
        "vessel_name": vessel_data["vesselParticulars"]["vesselName"],
        "call_sign": vessel_data["vesselParticulars"]["callSign"],
        "imo_number": vessel_data["vesselParticulars"]["imoNumber"],
        "flag": vessel_data["vesselParticulars"]["flag"],
        "location": vessel_data["location"],
        "grid": vessel_data["grid"],
        "purpose": vessel_data["purpose"],
        "agent": vessel_data["agent"],
        "reported_arrival_time": vessel_data["reportedArrivalTime"],
    }

    engine_MPA_arrivaldeclaration = create_engine(
        gsheet_cred_path, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )
    with engine_MPA_arrivaldeclaration.connect() as conn:
        MPA_arrivaldeclaration = conn.execute(query, values)
    return MPA_arrivaldeclaration
