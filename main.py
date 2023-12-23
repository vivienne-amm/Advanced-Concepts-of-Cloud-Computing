from botoservice import init_architecture, tear_down_architecture
from sys import argv
import time

# Initialize architecture
if argv[1] == 'UP':
    startTime = time.time()
    print('[MAIN] Initializing architecture!')
    init_architecture()

    print('[MAIN] Architecture initialized, going to sleep for 60 seconds!')
    time.sleep(60)
    print("All workers ready")

# Tear down architecture
elif argv[1] == 'DOWN':
    print('[MAIN] Tearing down architecture!')
    tear_down_architecture()
    print('[MAIN] Finished!')

# Does tearing down without deleting security groups to save time during debugging
elif argv[1] == 'DD':
    print('[MAIN] Tearing down architecture!')
    tear_down_architecture(False)
    print('[MAIN] Finished!')



