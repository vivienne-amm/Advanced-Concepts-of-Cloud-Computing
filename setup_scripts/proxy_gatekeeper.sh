sudo apt-get update -y
sudo apt-get install python3-venv nginx dos2unix -y

cd /home/ubuntu
# add project directory and vockey.pem using scp like this:
# scp -r -i <PATH_TO_VOCKEY.PEM_ON_LOCAL_MACHINE> <PATH_TO_LOG8415_TP3> ubuntu@<INSTANCE_DNS>:/home/ubuntu
# scp -r -i <PATH_TO_VOCKEY.PEM_ON_LOCAL_MACHINE> <PATH_TO_VOCKEY.PEM_ON_LOCAL_MACHINE> ubuntu@<INSTANCE_DNS>:/home/ubuntu

#scp -r -i /Users/vivi/Downloads/vockey.pem . ubuntu@ec2-44-222-68-148.compute-1.amazonaws.com:/home/ubuntu
#scp -r -i /Users/vivi/Downloads/vockey.pem /Users/vivi/Downloads/vockey.pem ubuntu@ec2-44-222-68-148.compute-1.amazonaws.com:/home/ubuntu

chmod 400 vockey.pem

# setup python virtual environment
python3.6 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
