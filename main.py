from botoservice import init_architecture, tear_down_architecture
from sys import argv
import time

# Initialize architecture
if argv[1] == 'UP':
    print('[MAIN] Initializing architecture!')
    init_architecture()
    print('[MAIN] Architecture initialized, going to sleep for 60 seconds!')
    time.sleep(60)
    print('[MAIN] Finished!')

# Tear down architecture
elif argv[1] == 'DOWN':
    print('[MAIN] Tearing down architecture!')
    tear_down_architecture()
    print('[MAIN] Finished!')