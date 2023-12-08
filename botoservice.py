import os
import time
import boto3
import requests
from botocore.exceptions import ClientError
from dotenv import load_dotenv

SUBNET_ID = 'subnet-030172ef91484d431'

# globals + helpers
security_group_orchestrator_name = "security_group_orchestrator"
security_group_workers_name = "security_group_workers"
security_group_standalone_name = "security_group_standalone"
regionName = 'us-east-1'
#imageId = 'ami-0fe0238291c8e3f07'
imageId = 'ami-0ee23bfc74a881de5'
# returns value of specified environment variable
def getOsVar(keyName):
    load_dotenv()
    return os.getenv(keyName)


def getAwsAccessKeyId():
    return getOsVar('aws_access_key_id')


def getAwsSecretAccessKey():
    return getOsVar('aws_secret_access_key')


def getAwsSessionToken():
    return getOsVar('aws_session_token')

# generating URLs for the worker containers
def getWorkerIndexUrl(dns):
    return "http://" + dns + ":5001" + "/", "http://" + dns + ":5002" + "/"


def checkInstanceStatus(dns):
    # print("checking instance with dns: " + dns)
    container1, container2 = getWorkerIndexUrl(dns)
    try:
        # send HTTP GET requests to both containers
        response1 = requests.get(container1)
        response2 = requests.get(container2)

        # check if both return status 200 OK
        if response1.status_code == 200 and response2.status_code == 200:
            return True
    except requests.exceptions.RequestException as e:
        # print(f"Error: {e}")
        return False
    return False

def checkUntilReady(instance_dns):
    print("checking instances until ready")
    # loop until all instances are ready
    while True:
        print(str(len(instance_dns)) + " instances not ready")

        # iterate through each worker instance's DNS address
        for dns in instance_dns:
            isRunning = checkInstanceStatus(dns)
            if isRunning:
                url1, url2 = getWorkerIndexUrl(dns)
                print(url1 + " is ready")
                print(url2 + " is ready")
                instance_dns.remove(dns)

            # check if all instances are ready -> if true, exit the loop
            if len(instance_dns) == 0:
                return
        time.sleep(20)

def printElapsedTime(startTime):
    elapsed_time = time.time() - startTime
    elapsed_time_formatted = "{:.2f}".format(elapsed_time)
    print(f"Elapsed time: {elapsed_time_formatted} seconds")

def setupContainersConfig(containerConfigTemplate, workerIps):
    for i in range(1, 5):
        # replace placeholders with corresponding worker IP addresses
        containerConfigTemplate = containerConfigTemplate.replace(f"__WORKER{str(i)}_IP__", workerIps[i - 1])
    return containerConfigTemplate


def loadOrchestratorScript(scriptPath, appCodePath, containerConfigPath, requirementsPath, dockerfilePath, workerIps):
    # read content form files
    user_data_script_template = open(scriptPath, 'r').read()
    orchestrator_flask_source_code = open(appCodePath, 'r').read()
    container_config_template = open(containerConfigPath, 'r').read()
    orchestrator_dockerfile_source_code = open(dockerfilePath, 'r').read()
    orchestrator_requirements = open(requirementsPath, 'r').read()

    # replace placeholders with actual content
    container_config = setupContainersConfig(container_config_template, workerIps)
    user_data_script_template = user_data_script_template.replace("__CONTAINER_CONFIG__", container_config)
    user_data_script_template = user_data_script_template.replace("__APP_CODE__", orchestrator_flask_source_code)
    user_data_script_template = user_data_script_template.replace("__REQUIREMENTS__", orchestrator_requirements)

    return user_data_script_template.replace("__DOCKERFILE__", orchestrator_dockerfile_source_code)


def loadScript(scriptPath):
    script_template = open(scriptPath, 'r').read()
    return script_template


# Fetches an instance by given ID and retrieves its DNS.
def getInstanceDns(ec2client, instanceId):
    response = ec2client.describe_instances(InstanceIds=[instanceId])
    return response['Reservations'][0]['Instances'][0]['PublicDnsName']


# Creates an orchestrator instance of specified type and assigns it to security group with provided id.
# Returns instance Id of the orchestrator.
def createManager(ec2resource, instanceType, securityGroupId, workerIps, privateIp):
    try:
        script = loadScript(
            'manager_setup.sh',
        ) # create orchestrator instance
        response = ec2resource.create_instances(
            ImageId=imageId,  # taken from https://cloud-images.ubuntu.com/locator/ec2/, map to multiple
            MinCount=1,
            MaxCount=1,
            InstanceType=instanceType,
            UserData=script,
            SecurityGroupIds=[securityGroupId],
            SubnetId=SUBNET_ID,
            PrivateIpAddress=privateIp,
            KeyName='vockey',

        )
        # wait until orchestrator instance is running & loaded
        print(f"Orchestrator created successfully, 1 instance of type {instanceType}. Waiting till running state.")
        orchestratorInstance = response[0]
        orchestratorInstance.wait_until_running()

        orchestratorInstance.load()

        return orchestratorInstance.public_dns_name
    except ClientError as e:
        print(f"Creation of type {instanceType} failed!")
        print(e)


# Creates an orchestrator instance of specified type and assigns it to security group with provided id.
# Returns instance Id of the orchestrator.
def createInstance(ec2resource, instanceType, securityGroupId, privateIp, tagName, script):
    try:

        response = ec2resource.create_instances(
            ImageId=imageId,  # taken from https://cloud-images.ubuntu.com/locator/ec2/, map to multiple
            MinCount=1,
            MaxCount=1,
            InstanceType=instanceType,
            UserData=script,
            SecurityGroupIds=[securityGroupId],
            SubnetId=SUBNET_ID,
            KeyName='vockey',
            PrivateIpAddress=privateIp,
            TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': tagName
                    },
                ]
            },
            ]
        )

        # wait until orchestrator instance is running & loaded
        print(f"{tagName} Instance created successfully, 1 instance of type {instanceType}. Waiting till running state.")
        instance = response[0]
        instance.wait_until_running()
        instance.load()

        return instance.public_dns_name
    except ClientError as e:
        print(f"Creation of type {instanceType} failed!")
        print(e)

# inits VPC + returns its Id
def initVPC(ec2client):
    response = ec2client.describe_vpcs()
    if not response['Vpcs']:
        raise Exception('No existing VPC!')
    return response['Vpcs'][0]['VpcId']


def createSecurityGroupWorker(client, vpcId):
    # create new security group for workers
    response = client.create_security_group(
        GroupName=security_group_workers_name,
        Description='Allow http requests on 5001 and 5002 ports',
        VpcId=vpcId
    )
    group_id = response['GroupId']

    # ingress + egress rules
    allow_all_traffic_rule = {
         'IpProtocol': '-1',
         'FromPort': 0,
         'ToPort': 65535,
         'IpRanges': [{'CidrIp': '172.31.0.0/20'}]
    }
    ssh_rule = {
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }

    # Authorize ingress + egress rules for security group
    client.authorize_security_group_ingress(
        GroupId=group_id,
        IpPermissions=[allow_all_traffic_rule, ssh_rule]
    )

    # ID of created security group
    return group_id


def createSecurityGroupStandalone(client, vpcId):

    # create new security group for workers
    response = client.create_security_group(
        GroupName=security_group_standalone_name,
        Description='Security group',
        VpcId=vpcId
    )
    group_id = response['GroupId']

    client.authorize_security_group_ingress(
        CidrIp="0.0.0.0/0",
        IpProtocol='-1',
        FromPort=0,
        ToPort=65535,
        GroupName=security_group_standalone_name,
    )

    # ID of created security group
    return group_id


def get_security_group_by_name(client, group_name):
    response = client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [group_name]}])
    group_id = ""
    if response['SecurityGroups']:
        group = response['SecurityGroups'][0]
        group_id = group['GroupId']

    # return id of security group or ""
    return group_id

def get_manager_security_group(client):
    return get_security_group_by_name(client, security_group_orchestrator_name)


def get_worker_security_group(client):
    return get_security_group_by_name(client, security_group_workers_name)

def get_standalone_security_group(client):
    return get_security_group_by_name(client, security_group_standalone_name)


def createSecurityGroupManager(client, vpcId):
    response = client.create_security_group(
        GroupName=security_group_orchestrator_name,
        Description='Allow http requests from any ip',
        VpcId=vpcId
    )
    group_id = response['GroupId']

    # ingress + egress rules
    allow_all_traffic_rule = {
        'IpProtocol': '-1',
        'FromPort': 0,
        'ToPort': 65535,
        'IpRanges': [{'CidrIp': '172.31.0.0/20'}]
    }
    ssh_rule = {
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }

    # Authorize ingress + egress rules for security group
    client.authorize_security_group_ingress(
        GroupId=group_id,
        IpPermissions=[allow_all_traffic_rule, ssh_rule]
    )

    # return the ID of created security group
    return group_id


def getEc2Resource():
    return boto3.resource(
        'ec2',
        region_name=regionName,
        aws_access_key_id=getAwsAccessKeyId(),
        aws_secret_access_key=getAwsSecretAccessKey(),
        aws_session_token=getAwsSessionToken()
    )


def getBoto3Client(clientType):
    return boto3.client(
        clientType,
        region_name=regionName,
        aws_access_key_id=getAwsAccessKeyId(),
        aws_secret_access_key=getAwsSecretAccessKey(),
        aws_session_token=getAwsSessionToken()
    )

def getEc2Client():
    return getBoto3Client('ec2')


def getElbv2Client():
    return getBoto3Client('elbv2')


def getCloudwatchClient():
    return getBoto3Client('cloudwatch')

def initArchitecture():
    ec2Client = getEc2Client()
    ec2Resource = getEc2Resource()
    print('Resources initiated!')

    vpcId = initVPC(ec2Client)
    print('VPC check done!')

    # Retrieve or create orchestrator and worker security groups
    securityGroupManagerId = get_manager_security_group(ec2Client)
    securityGroupWorkerId = get_worker_security_group(ec2Client)
    securityGroupStandaloneId = get_standalone_security_group(ec2Client)
    if securityGroupManagerId == "":
        securityGroupManagerId = createSecurityGroupManager(ec2Client, vpcId)

    if securityGroupStandaloneId == "":
        securityGroupStandaloneId = createSecurityGroupStandalone(ec2Client, vpcId)

    if securityGroupWorkerId == "":
        securityGroupWorkerId = createSecurityGroupWorker(ec2Client, vpcId)

    print('Security group created!')

    script = loadScript(
        'worker_setup1.sh',
    )
    # create the worker and orchestrator instances
    worker1 = createInstance(ec2Resource, 't2.micro', securityGroupWorkerId, "172.31.1.2", "worker", script)
    worker2 = createInstance(ec2Resource, 't2.micro', securityGroupWorkerId, "172.31.1.3", "worker", script)
    worker3 = createInstance(ec2Resource, 't2.micro', securityGroupWorkerId, "172.31.1.4", "worker", script)

    script = loadScript(
        'manager_setup.sh',
    )
    orchestratorDns = createInstance(ec2Resource, 't2.micro', securityGroupManagerId, "172.31.1.1", "manager", script)

    script = loadScript(
        'standalone_setup.sh',
    )  # create orchestrator instance
    standAloneDns = createInstance(ec2Resource, 't2.micro', securityGroupStandaloneId, "172.31.1.5", "standalone", script)

    script = loadScript(
        'manager_setup.sh',
    )
    orchestratorDns = createInstance(ec2Resource, 't2.micro', securityGroupManagerId, "172.31.1.1", "manager", script)

    print('Instances initiated!')

    #return orchestratorDns, workersIps, workersInstanceIds
    return orchestratorDns, standAloneDns

def deleteInternetGateway(vpcId):
    ec2Client = getEc2Client()
    igs = ec2Client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpcId]}])
    key = 'InternetGateways'
    if key in igs:
        # detach + delete each internet gateway
        for ig in igs[key]:
            igId = ig['InternetGatewayId']
            ec2Client.detach_internet_gateway(
                InternetGatewayId=igId,
                VpcId=vpcId
            )
            ec2Client.delete_internet_gateway(
                InternetGatewayId=igId
            )


def shutDownInstances(ec2):
    instancesResponse = ec2.describe_instances()

    instances = instancesResponse['Reservations']
    for reservation in instances:
        for instance in reservation['Instances']:
            print(f"Terminating instance ID: {instance['InstanceId']}")
            ec2.terminate_instances(InstanceIds=[instance['InstanceId']])
            print(f"------------------------")


# Deletes user security group
# All machines in this security groups must be down before the deleting starts
def deleteSecurityGroup(ec2Client):
    print("Deleting security groups")
    response = ec2Client.describe_security_groups()
    groups = response["SecurityGroups"]
    groupTuple = map(lambda g: g["GroupName"], groups)
    for group in groupTuple:
        if group != "default":
            response = ec2Client.delete_security_group(
                GroupName=group,
            )


def tearDownArchitecture(shutSecurityGroup=True):
    ec2Client = getEc2Client()
    print('Resources initiated!')

    shutDownInstances(ec2Client)
    print('Instances terminated!')

    # Shut also the security group if the shutSecurityGroup is true
    if shutSecurityGroup:
        print('Sleeping for 60 seconds to be able to delete target and security groups!')
        time.sleep(60)
        deleteSecurityGroup(ec2Client)
        print('Security group deleted!')