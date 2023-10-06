from sqlalchemy import create_engine, text
import pandas as pd
import os
import json
import requests

# db_connection_string = os.environ['DB_CONNECTION_STRING']
# db_connection_string = "mysql+pymysql://2j104pgpfhay9dokc46k:pscale_pw_fiA5JrG88BcLgKuQmmK9WZHjaOlzf2BkRisjOD6FDn6@aws.connect.psdb.cloud/sgtd?charset=utf8mb4"
db_connection_string = "mysql+pymysql://8c5qff8fhgi0sz6adth2:pscale_pw_k1WZMRjpR4X9iVfFadNWQM6o2o2lscav9ydrcM5Qfdp@aws.connect.psdb.cloud/sgtd?charset=utf8mb4"
engine = create_engine(
    db_connection_string, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
)


def get_table_data(db_creds):
    print("Start of get_table_data......")
    engine = create_engine(
        db_creds, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )
    with engine.connect() as conn:
        query = text("select * from MPA_vessel_data")
        result_VCP = conn.execute(query)
        result_all_VCP = result_VCP.fetchall()
        column_names_VCP = result_VCP.keys()
        # print(result_all_VCP)
        print(f"length of result_all_VCP = {len(result_all_VCP)}")
        df2 = pd.DataFrame(result_all_VCP, columns=column_names_VCP)
        # sorting by first name
        df2.drop_duplicates(subset="imoNumber", keep="last", inplace=True)

        query = text("select * from MPA_arrivaldeclaration")
        result_ETA = conn.execute(query)
        result_all_ETA = result_ETA.fetchall()
        column_names_ETA = result_ETA.keys()
        # print(result_all_ETA)
        print(f"length of result_all_ETA = {len(result_all_ETA)}")
        df3 = pd.DataFrame(result_all_ETA, columns=column_names_ETA)
        df3.drop_duplicates(subset="imo_number", keep="last", inplace=True)
        # print(f"df3 = {df3}")
        # print(f"df2= {df2}")
        df3.drop(columns=["call_sign", "flag", "vessel_name"], inplace=True)
        #   df3.rename(columns={'key_0': 'renamed_key_0'}, inplace=True)
        # if 'key_0' in df2.columns:
        #   df2.drop(columns=['key_0'], inplace=True)
        new_df = pd.merge(
            df2, df3, left_on=df2["imoNumber"], right_on=df3["imo_number"], how="inner"
        )
        new_df.drop(
            columns=[
                "id_x",
                "id_y",
                "imo_number",
                "time_queried",
                "timeStamp",
                "latitude",
                "longitude",
                "deadweight",
                "vesselDepth",
                "heading",
            ],
            inplace=True,
        )
        if "key_0" in new_df.columns:
            new_df.drop(columns=["key_0"], inplace=True)
        print(f"new_df= {new_df}")
        print(f"Final Result all vm = {[new_df]}")
        return [new_df]


def delete_all_rows_table_view(db_creds):
    print("Start of delete_all_rows_table_view 2 tables: MPA_arrivaldeclaration......")
    engine = create_engine(
        db_creds, connect_args={"ssl": {"ssl_ca": "/etc/ssl/cert.pem"}}
    )
    with engine.connect() as conn:
        query_VM = text("DELETE FROM MPA_arrivaldeclaration where id > 0")
        result_VM = conn.execute(query_VM)
        print("Deleted vessel_movement_UCE where id > 0")
        query_VCP = text("DELETE FROM MPA_vessel_data where id > 0")
        result_VCP = conn.execute(query_VCP)
        print("Deleted MPA_vessel_data where id > 0")
        query_VDA = text("DELETE FROM vessel_due_to_arrive_UCE where id > 0")
        result_VDA = conn.execute(query_VDA)
        print("Deleted vessel_due_to_arrive_UCE; where id > 0")
        query_PS = text("DELETE FROM pilotage_service_UCE where id > 0")
        result_PS = conn.execute(query_PS)
        print("Deleted pilotage_service_UCE where id > 0")


# get VDA from MPA API
def get_data_from_vessel_due_to_arrive_and_depart(
    url_arrive, url_depart, gsheet_cred_path
):
    API_KEY_MPA = "QgCv2UvINPRfFqbbH3yVHRVVyO8Iv5CG"
    r_GET_arrive = requests.get(url_arrive, headers={"Apikey": API_KEY_MPA})
    # Check the response
    if r_GET_arrive.status_code == 200:
        print("vessel_due_to_arrive Data retrieved successfully!")
        # query and values
        dueToArrive_Data = json.loads(r_GET_arrive.text)
        # print(f"dueToArrive_Data = {dueToArrive_Data}")
        arrive_df = pd.json_normalize(dueToArrive_Data)
        print(f"arrive_df = {arrive_df}")
        print(arrive_df.iloc[200:206])
        # write in mysql
    else:
        print("Failed to get vessel_due_to_arrive data")

    r_GET_depart = requests.get(url_depart, headers={"Apikey": API_KEY_MPA})
    # Check the response
    if r_GET_depart.status_code == 200:
        print("vessel_due_to_depart Data retrieved successfully!")
        # query and values
        dueToDepart_Data = json.loads(r_GET_depart.text)
        # print(f"dueToDepart_Data = {dueToDepart_Data}")
        depart_df = pd.json_normalize(dueToDepart_Data)
        # print(f"depart_df = {depart_df}")
        # write in mysql
    else:
        print("Failed to get vessel_due_to_depart data")

    merged_df = arrive_df.merge(depart_df, on="vesselParticulars.imoNumber", how="left")
    merged_df.drop(
        columns=[
            "vesselParticulars.vesselName_y",
            "vesselParticulars.vesselName_y",
            "vesselParticulars.flag_y",
            "vesselParticulars.callSign_y",
        ],
        inplace=True,
    )
    # change purpose from Y,Y,N,N,N... to #1 indicator – Loading / Unloading Cargo #2 indicator – Loading / Unloading Passengers #3 indicator – Taking Bunker  #4 indicator – Taking Ship Supplies #5 indicator – Changing Crew #6 indicator – Shipyard Repair #7 indicator – Offshore Support #8 indicator – Not Used #9 indicator – Other Afloat Activities
    print(merged_df)
    return merged_df


def get_data_from_MPA_Vessel_Arrival_Declaration(input_list):
    Declaration_df = pd.DataFrame()
    print("Start of get_data_from_MPA_Vessel_Arrival_Declaration.............")
    print(f"input_list = {input_list}")
    for vessel_imo in input_list:
        print(f"vessel_imo = {vessel_imo}")
        url_MPA_arrivaldeclaration = f"https://sg-mdh-api.mpa.gov.sg/v1/vessel/arrivaldeclaration/imonumber/{vessel_imo}"
        API_KEY_MPA = "QgCv2UvINPRfFqbbH3yVHRVVyO8Iv5CG"
        r_GET_arrivaldeclaration = requests.get(
            url_MPA_arrivaldeclaration, headers={"Apikey": API_KEY_MPA}
        )
        if r_GET_arrivaldeclaration.status_code == 200:
            print("Config Data retrieved successfully!")
            # print(r_GET_arrivaldeclaration.text)
            data_list = json.loads(r_GET_arrivaldeclaration.text)
            # print(f"API response = {(data_list)}")
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
                Declaration_df = Declaration_df.append(
                    pd.json_normalize(latest_record), ignore_index=True
                )
                print(
                    f"Declaration_df get_data_from_MPA_Vessel_Arrival_Declaration == {Declaration_df}"
                )

            else:
                print("No records with reported arrival times found.")
    return Declaration_df
    # ======================== END GET MPA Vessel Arrival Declaration by IMO Number =============
