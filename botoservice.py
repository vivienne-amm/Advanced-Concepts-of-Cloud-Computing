import os
import time
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# globals + helpers
security_group_orchestrator_name = "security_group_orchestrator"
security_group_workers_name = "security_group_workers"
regionName = 'us-east-1'
imageId = 'ami-0fe0238291c8e3f07'
setupScriptPath = 'instance_flask_setup.sh' # TODO If the script got renamed

def getOsVar(keyName):
    load_dotenv()
    return os.getenv(keyName)

def getAwsAccessKeyId():
    return getOsVar('aws_access_key_id')

def getAwsSecretAccessKey():
    return getOsVar('aws_secret_access_key')

def getAwsSessionToken():
    return getOsVar('aws_session_token')

def setupContainersConfig(containerConfigTemplate, workerIps):
    for i in range(1, 5):
        containerConfigTemplate = containerConfigTemplate.replace(f"__WORKER{str(i)}_IP__", workerIps[i - 1])
    return containerConfigTemplate

def loadOrchestratorScript(scriptPath):
    user_data_script_template = open(scriptPath, 'r').read()
    #orchestrator_flask_source_code = open(appCodePath, 'r').read()
    #container_config_template = open(containerConfigPath, 'r').read()
    #container_config = setupContainersConfig(container_config_template, workerIps)
    #user_data_script_template = user_data_script_template.replace("__CONTAINER_CONFIG__", container_config)
    #return user_data_script_template.replace("__APP_CODE__", orchestrator_flask_source_code)
    return user_data_script_template

def loadWorkerScript(scriptPath, containerCodePath, dockerfilePath, dockerRequirementsPath):
    worker_script_template = open(scriptPath, 'r').read()
    worker_container_flask_source_code = open(containerCodePath, 'r').read()
    worker_container_dockerfile = open(dockerfilePath, 'r').read()
    worker_container_requirements = open(dockerRequirementsPath, 'r').read()
    worker_script_template = worker_script_template.replace("__APP_CODE__", worker_container_flask_source_code)
    worker_script_template = worker_script_template.replace("__CONTAINER_DOCKER_FILE__", worker_container_dockerfile)
    worker_script_template = worker_script_template.replace("__APP_CODE_REQ__", worker_container_requirements)
    return worker_script_template


# Fetches an instance by given ID and retrieves its DNS.
def getInstanceDns(ec2client, instanceId):
    response = ec2client.describe_instances(InstanceIds=[instanceId])
    return response['Reservations'][0]['Instances'][0]['PublicDnsName']


# Creates an orchestrator instance of specified type and assigns it to security group with provided id.
# Returns instance Id of the orchestrator.
def createInstance(ec2resource, instanceType, securityGroupId):
    try:
        script = loadOrchestratorScript(
            'setup.sh'
        )
        response = ec2resource.create_instances(
            ImageId=imageId,  # taken from https://cloud-images.ubuntu.com/locator/ec2/, map to multiple
            MinCount=1,
            MaxCount=1,
            InstanceType=instanceType,
            #UserData=script,
            SecurityGroupIds=[securityGroupId],
            KeyName='vockey'
        )
        print(f"Instance created successfully, 1 instance of type {instanceType}.")
        return response[0].id
    except ClientError as e:
        print(f"Creation of type {instanceType} failed!")
        print(e)

# Creates [count] workers.
# Returns list of worker ids.
def createWorkers(ec2resource, count, instanceType, securityGroupId):
    try:
        script = loadWorkerScript(
            'to_deploy/worker_setup_static.sh',
            'to_deploy/worker.py',
            'to_deploy/Dockerfile_worker',
            'to_deploy/worker_requirements.txt'
        )
        instances = ec2resource.create_instances(
            ImageId=imageId,  # taken from https://cloud-images.ubuntu.com/locator/ec2/, map to multiple
            MinCount=count,
            MaxCount=count,
            InstanceType=instanceType,
            UserData=script,
            SecurityGroupIds=[securityGroupId],
            KeyName='vockey'
        )
        print(f"Workers created successfully, {count} instances of type {instanceType}.")
        ips = []
        for instance in instances:
            instance.wait_until_running()
            instance.load()
            ips.append(instance.public_ip_address)
        return ips
    except ClientError as e:
        print(f"Creation of type {instanceType} failed!")
        print(e)
        raise e

# inits VPC + returns its Id
def initVPC(ec2client):
    response = ec2client.describe_vpcs()
    if not response['Vpcs']:
        raise Exception('No existing VPC!')
    return response['Vpcs'][0]['VpcId']


def createSecurityGroupWorker(client, vpcId):
    response = client.create_security_group(
        GroupName=security_group_workers_name,
        Description='Allow http requests on 5000 and 5001 ports',
        VpcId=vpcId
    )
    group_id = response['GroupId']

    http_rule1 = {
        'IpProtocol': 'tcp',
        'FromPort': 5001,
        'ToPort': 5001,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }

    http_rule2 = {
        'IpProtocol': 'tcp',
        'FromPort': 5002,
        'ToPort': 5002,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }
    ssh_rule = {
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }

    client.authorize_security_group_ingress(
        GroupId=group_id,
        IpPermissions=[http_rule1, http_rule2, ssh_rule]
    )

    client.authorize_security_group_egress(
        GroupId=group_id,
        IpPermissions=[http_rule1, http_rule2]
    )

    return group_id

def createSecurityGroupOrchestrator(client, vpcId):
    response = client.create_security_group(
        GroupName=security_group_orchestrator_name,
        Description='Allow http requests from any ip',
        VpcId=vpcId
    )
    group_id = response['GroupId']

    http_rule = {
        'IpProtocol': 'tcp',
        'FromPort': 80,
        'ToPort': 80,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }

    ssh_rule = {
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }

    client.authorize_security_group_ingress(
        GroupId=group_id,
        IpPermissions=[http_rule, ssh_rule]
    )

    client.authorize_security_group_egress(
        GroupId=group_id,
        IpPermissions=[http_rule]
    )

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

    securityGroupId = createSecurityGroupOrchestrator(ec2Client, vpcId)
    #securityGroupWorkerId = createSecurityGroupWorker(ec2Client, vpcId)
    print('Security group created!')

    InstanceId = createInstance(ec2Resource, 't2.micro', securityGroupId)

    print('Instances initiated!')

    print('Sleeping for 80 for instances to get into running state!')
    # Running state is required to obtain orchestrator DNS
    time.sleep(80)
    InstanceDns = getInstanceDns(ec2Client, InstanceId)
    print('Architecture built!')
    return InstanceDns


def deleteSubnets(vpcId):
    ec2Client = getEc2Client()
    subnets = ec2Client.describe_subnets(
        Filters=[{'Name': 'vpc-id', 'Values': [vpcId]}]
    )
    key = 'Subnets'
    if key in subnets:
        for subnet in subnets[key]:
            subnetId = subnet['SubnetId']
            ec2Client.delete_subnet(
                SubnetId=subnetId
            )

def deleteInternetGateway(vpcId):
    ec2Client = getEc2Client()
    igs = ec2Client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpcId]}])
    key = 'InternetGateways'
    if key in igs:
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

def tearDownArchitecture():
    ec2Client = getEc2Client()
    print('Resources initiated!')

    shutDownInstances(ec2Client)
    print('Instances terminated!')

    # Just for be sure that all machines in that security group are deleted
    print('Sleeping for 60 seconds to be able to delete target and security groups!')
    time.sleep(60)
    deleteSecurityGroup(ec2Client)
    print('Security group deleted!')
