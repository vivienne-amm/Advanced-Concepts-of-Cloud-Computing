from botoservice import initArchitecture, tearDownArchitecture, checkUntilReady, printElapsedTime
from sys import argv
import time

from benchmarkservice import getOrchestratorUrl

# Initialize architecture
if argv[1] == 'UP':
    startTime = time.time()
    print('[MAIN] Initializing architecture!')
    orchestratorDns, standAloneDns = initArchitecture()
    orchestratorUrl = getOrchestratorUrl(orchestratorDns)
    standaloneUrl = getOrchestratorUrl(standAloneDns)

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

# Does tearing down without deleting security groups to save time during debugging
elif argv[1] == 'DD':
    print('[MAIN] Tearing down architecture!')
    tearDownArchitecture(False)
    print('[MAIN] Finished!')
