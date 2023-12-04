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


# Will execute requests on [num_threads] threads simultaneously on the orchestrator with provided url.
def runWorkload(num_threads, orchestratorUrl):
    threads = []

    for _ in range(num_threads):
        thread = threading.Thread(target=do_requests, args=(orchestratorUrl,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
