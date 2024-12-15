import requests
import json

DEBEZIUM_SERVER_CONS = "http://debezium:8085/connectors"

def create_connection(file_config:str):
    print(f"🔗 Creating connection for {file_config} ...")
    with open(f"./configs/{file_config}.json") as f:
        connector_config = json.load(f)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.post(DEBEZIUM_SERVER_CONS, json=connector_config, headers=headers)
    if response.status_code == 201:
        print("✅ Connector created successfully!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    print("-"*100)

if __name__ == "__main__":
    create_connection("postgres")
