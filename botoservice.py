import os
import time
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

SUBNET_ID = 'subnet-030172ef91484d431'

# globals + helpers
SECURITY_GROUP_GATEKEEPER_NAME = "security_group_gatekeeper"
SECURITY_GROUP_WORKERS_NAME = "security_group_workers"
SECURITY_GROUP_STANDALONE_NAME = "security_group_standalone"
SECURITY_GROUP_PROXY_NAME = "security_group_proxy"

regionName = 'us-east-1'
imageId = 'ami-0ee23bfc74a881de5'

# returns value of specified environment variable
def get_os_var(keyName):
    load_dotenv()
    return os.getenv(keyName)

def print_elapsed_time(startTime):
    elapsed_time = time.time() - startTime
    elapsed_time_formatted = "{:.2f}".format(elapsed_time)
    print(f"Elapsed time: {elapsed_time_formatted} seconds")

# Creates an orchestrator instance of specified type and assigns it to security group with provided id.
# Returns instance Id of the orchestrator.
def create_instance(ec2resource, instanceType, securityGroupId, privateIp, tagName):
    try:
        response = ec2resource.create_instances(
            ImageId=imageId,  # taken from https://cloud-images.ubuntu.com/locator/ec2/, map to multiple
            MinCount=1,
            MaxCount=1,
            InstanceType=instanceType,
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
def init_vpc(ec2client):
    response = ec2client.describe_vpcs()
    if not response['Vpcs']:
        raise Exception('No existing VPC!')

    return response['Vpcs'][0]['VpcId']


def create_security_group(client, name, description, vpcId, ingress_rules):
    response = client.create_security_group(
        GroupName=name,
        Description=description,
        VpcId=vpcId
    )
    group_id = response['GroupId']

    for rule in ingress_rules:
        client.authorize_security_group_ingress(GroupId=group_id, IpPermissions=[rule])

    return group_id


def create_security_group_proxy(client, vpcId):
    rules = [
        {'IpProtocol': 'tcp', 'FromPort': 3306, 'ToPort': 3306, 'IpRanges': [{'CidrIp': '172.31.1.0/28'}]},  # proxy IP
        {'IpProtocol': 'tcp', 'FromPort': 5001, 'ToPort': 5001, 'IpRanges': [{'CidrIp': '172.31.1.0/28'}]},  # gatekeeper port
        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}, # ssh rule
    ]

    return create_security_group(client, SECURITY_GROUP_PROXY_NAME, 'Proxy Security Group', vpcId, rules)

def create_security_group_gatekeeper(client, vpcId):
    rules = [
        {'IpProtocol': 'tcp', 'FromPort': 5001, 'ToPort': 5001, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}, # ssh rule
    ]

    return create_security_group(client, SECURITY_GROUP_GATEKEEPER_NAME, 'The gatekeeper security group', vpcId, rules)

def create_security_group_workers(client, vpcId):
    rules = [
        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': '-1', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '172.31.0.0/20'}]}
    ]

    return create_security_group(client, SECURITY_GROUP_WORKERS_NAME, 'Cluster Security Group', vpcId, rules)

def create_security_group_standalone(client, vpcId):
    rules = [
        {'IpProtocol': '-1', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
    ]

    return create_security_group(client, SECURITY_GROUP_STANDALONE_NAME, 'Security group', vpcId, rules)


def get_security_group_by_name(client, group_name):
    response = client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [group_name]}])
    group_id = ""
    if response['SecurityGroups']:
        group = response['SecurityGroups'][0]
        group_id = group['GroupId']

    # return id of security group or ""
    return group_id

def get_ec2_resource():
    return boto3.resource(
        'ec2',
        region_name=regionName,
        aws_access_key_id=get_os_var('aws_access_key_id'),
        aws_secret_access_key=get_os_var('aws_secret_access_key'),
        aws_session_token=get_os_var('aws_session_token')
    )

def get_boto3_client(clientType):
    return boto3.client(
        clientType,
        region_name=regionName,
        aws_access_key_id=get_os_var('aws_access_key_id'),
        aws_secret_access_key=get_os_var('aws_secret_access_key'),
        aws_session_token=get_os_var('aws_session_token')
    )

def get_ec2_client():
    return get_boto3_client('ec2')

def get_elbv2_client():
    return get_boto3_client('elbv2')

def get_cloudwatch_client():
    return get_boto3_client('cloudwatch')

def init_architecture():
    ec2_client = get_ec2_client()
    ec2_resource = get_ec2_resource()
    print('Resources initiated!')

    vpcId = init_vpc(ec2_client)
    print('VPC check done!')

    security_groups_info = [
        {"name": SECURITY_GROUP_GATEKEEPER_NAME, "create_func": create_security_group_gatekeeper},
        {"name": SECURITY_GROUP_WORKERS_NAME, "create_func": create_security_group_workers},
        {"name": SECURITY_GROUP_PROXY_NAME, "create_func": create_security_group_proxy},
        {"name": SECURITY_GROUP_STANDALONE_NAME, "create_func": create_security_group_standalone},
    ]

    security_group_ids = {}

    for sg_info in security_groups_info:
        sg_id = get_security_group_by_name(ec2_client, sg_info["name"])
        if not sg_id:
            sg_id = sg_info["create_func"](ec2_client, vpcId)
        security_group_ids[sg_info["name"]] = sg_id
        print(f"{sg_info['name']} Security Group ID: {sg_id}")

    # create instances
    create_instance(ec2_resource, 't2.micro', security_group_ids["security_group_workers"], "172.31.1.2", "worker")
    create_instance(ec2_resource, 't2.micro', security_group_ids["security_group_workers"], "172.31.1.3", "worker")
    create_instance(ec2_resource, 't2.micro', security_group_ids["security_group_workers"], "172.31.1.4", "worker")
    create_instance(ec2_resource, 't2.micro', security_group_ids["security_group_workers"], "172.31.1.1", "manager")
    create_instance(ec2_resource, 't2.micro', security_group_ids["security_group_standalone"], "172.31.1.5", "standalone")
    create_instance(ec2_resource, 't2.large', security_group_ids["security_group_proxy"], "172.31.1.10", "proxy")
    create_instance(ec2_resource, 't2.large', security_group_ids["security_group_gatekeeper"], "172.31.1.11", "gatekeeper")

def shut_down_instances(ec2):
    instances_response = ec2.describe_instances()
    instances = instances_response['Reservations']
    for reservation in instances:
        for instance in reservation['Instances']:
            print(f"Terminating instance ID: {instance['InstanceId']}")
            ec2.terminate_instances(InstanceIds=[instance['InstanceId']])
            print(f"------------------------")

# Deletes user security group
# All machines in this security groups must be down before the deleting starts
def delete_security_group(ec2Client):
    print("Deleting security groups")
    response = ec2Client.describe_security_groups()
    groups = response["SecurityGroups"]
    group_tuple = map(lambda g: g["GroupName"], groups)
    for group in group_tuple:
        if group != "default":
            response = ec2Client.delete_security_group(
                GroupName=group,
            )

def tear_down_architecture(shutSecurityGroup=True):
    ec2_client = get_ec2_client()
    print('Resources initiated!')
    shut_down_instances(ec2_client)
    print('Instances terminated!')
    # Shut also the security group if the shutSecurityGroup is true
    if shutSecurityGroup:
        print('Sleeping for 60 seconds to be able to delete target and security groups!')
        time.sleep(60)
        delete_security_group(ec2_client)
        print('Security group deleted!')