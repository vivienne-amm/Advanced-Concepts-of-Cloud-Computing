from botoservice import initArchitecture, tearDownArchitecture, checkUntilReady, printElapsedTime
from sys import argv
import time

from benchmarkservice import runWorkload, getOrchestratorUrl

# Initialize architecture
if argv[1] == 'UP':
    startTime = time.time()
    print('[MAIN] Initializing architecture!')
    orchestratorDns, standAloneDns = initArchitecture()
    orchestratorUrl = getOrchestratorUrl(orchestratorDns)
    standaloneUrl = getOrchestratorUrl(standAloneDns)

    #checkUntilReady(workerDnsArray)
    print('[MAIN] Architecture initialized, going to sleep for 60 seconds!')
    time.sleep(60)
    print("All workers ready")
    print(f'Standalone url: {standaloneUrl}')
    print(f'Orchestrator url: {orchestratorUrl}')
    printElapsedTime(startTime)
# Tear down architecture
elif argv[1] == 'DOWN':
    print('[MAIN] Tearing down architecture!')
    tearDownArchitecture()
    print('[MAIN] Finished!')

# Runs workload, taking user input for orchestrator URL & number of requests
elif argv[1] == 'RUN':
    orchestratorUrl = input("Enter URL of the orchestrator: ")
    try:
        num_requests = int(input("Enter the number of requests to send: "))
        runWorkload(num_requests, orchestratorUrl)
    except ValueError:
        print("Please enter a valid integer.")

# Does tearing down without deleting security groups to save time during debugging
elif argv[1] == 'DD':
    print('[MAIN] Tearing down architecture!')
    tearDownArchitecture(False)
    print('[MAIN] Finished!')
