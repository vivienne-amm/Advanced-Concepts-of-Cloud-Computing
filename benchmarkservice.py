import requests
import threading

multiplier = 100

# returns url of orchestrator instance
def getOrchestratorUrl(orchestratorDns):
    return "http://" + orchestratorDns

def do_requests(orchestratorUrl):
    url = f"{orchestratorUrl}/new_request"
    data = {}
    try:
        response = requests.post(url, json=data)
        print(f"Request sent. Response: {response.status_code} | {response.json()}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")
