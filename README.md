
# Goalkeeper

**Goalkeeper** - a service that helps you to correctly and safely store data on ventus cloud resources. 

## What is the Goalkeeper and what is it for

This project was designed to protect customers from their carelessness or negligence in relation to the security of their data, from possible attacks of their databases by third parties,
when they are not sufficiently protected.

This aplication was implemented as *Python script* running in a *Kubernetis cluster* using a *cronjob* that runs it once a day on a schedule.  

Application logic is as follows:

* we set the list of ports which status we want to monitor on all our servers on Prod or Stage    
* according to the schedule of cronjob, once a day using nmap-module we scan all servers by the indicated ports, and if some of them are open, we send a notification by mail to the client who owns this server    
* logs of application execution are printed in the console, and results of scan are sent to a telegram channel.  

## Code explanation

Let's take a closer look at the code that launches the Goalkeeper. It consists of the following sections: 

1. Block of importing the necessary libraries
2. Block of defining variables  
3. Series of functions:  
        * `def logInsert(logStr)` - function of log settings  
        * `def ip_range()` - function that defines the list of servers for scanning  
        * `def find_projectID_Openstack(ip)` - function that finds the project ID in Openstack of a server that contains an open dangerous port  
        * `def find_projectNAME_Openstack(projectID_Openstack)` - function that finds the project Name in Openstack of that server by it's ID   
        * `def find_email_fleio(projectID_Openstack)` - function that finds the mail adress of the client who owns that server with open dangerous port  
        * `def sendmail_report(to_adr, code)` - function that sends a scan report to the found email   
        * `def scanning()` - the main function of nmap scanning of all hosts on selected ports, which scans and uses all of the above functions for sending a scan report.  
        

The first block is responsible for importing the necessary libraries, among which you can find the following:
        - openstack  
        - nmap  
        - smtplib  
        - requests  
        - json  
        - and others  

Next we need to define a series of variables that will be revealed in the secrets of the cluster. Depending on which variables are set, the service will analyze either Stage or Prod. In addition, the first variable (*environment*) is responsible for whether service reports will be sent to customers or only to our personal mailing address.

Then we set the connection to the Openstack and use it to get a list of all servers. When the list of servers is received, we connect to the Fleio API to get a list of all floating ip's. We execute these commands outside the function in order to speed up the application, since this data will be used repeatedly in subsequent functions.  

After these steps, we run function `ips`, which collects our servers into a one array for scanning, and run the main function `scanning`, which defines the main logic of the script:  
* using nmap-module we scan all our servers by the list of selected ports, which we were difined as dangereous  
* if one of that ports are open we run function `find_projectID_Openstack` and than by it's ID we find the remaining necessary details of the project, in order to ultimately find the mail address and send a report of scanning to the client  
* if the address of client is not found, the letter will be sent to our own address  
* also if the project number or other necessary information is not found, it will be marked as "NOT FOUND" and the report sent to our own address  
* the code also has a section responsible for sending notifications to the telegram channel   

## Run Goalkeeper on VM

1. Create VM with ubuntu-1804-bionic  
2. Install pip3   
    ` sudo apt-get update  `  
    ` sudo apt install python3-pip  `    
3. Install OpenstackSDK     
(https://docs.openstack.org/openstacksdk/latest/user/connection.html)  
    ` pip3 install openstacksdk    `  
4. Install nmap and nmap module for python3.6:  
    ` sudo apt-get install nmap  `  
    ` pip3 install python-nmap  `  
5. Set environment variables for Prod or Stage  
6. Run Python script - goalkeeper_latest.py    
    ` python3.6 goalkeeper_latest.py  `  


## Run Goalkeeper on Kubernetes Cluster

1. Create docker image from our goalkeeper_latest.py:
    - install docker
    ```
    apt install docker.io
    ```

    - create and go to the working directory 
    ```
    mkdir GOALKEEPER
    cd GOALKEEPER
    ```

    - create file with the code ('goalkeeper_latest.py') and Dockerfile, with the following contents:  
    ```
    FROM python:3.6-buster  
    LABEL maintainer=<your name and mail adress>  
    COPY . /goalkeeper_app  
    WORKDIR /goalkeeper_app  
    RUN apt update  
    RUN apt install -y python3-pip  
    RUN pip3 install openstacksdk  
    RUN apt install -y  nmap  
    RUN pip3 install python-nmap  
    CMD python ./goalkeeper_latest.py  
    ```
    - build the container
    ```
    docker build -t goalkeeper_app .
    ```

    - tag the version of our container in our docker hub
    ```
    docker tag goalkeeper_app vika1990z/goalkeeper_app:1.0.0
    ```

    - login in our docker hub
    ```
    docker login
    ```

    - push the container into our docker hub
    ```
    docker push vika1990z/goalkeeper_app:1.0.0
    ```
    - now you can run and check if the container works without errors
    ```
    docker run --env <Environment Variables> <id of container>
    ```
2. Create kubernetes cluster with next parameters:
    - Master count: 1    
    - Node count: 1  
    - Docker volume size (GB): 60  
    - Node flavor: VC-4  
    - Master node flavor: VC-4  

3. Get access to your kubernetes cluster:
    ```
    ssh core@<master's IP>
    ```
4. Create yaml file with kubernetes secrets, where will the encrypted values of my environment variables be stored, and apply it:
    ```
    vi mysecrets.yaml
    kubectl apply -f mysecrets.yaml
    kubectl get secrets mysecrets -o yaml
    ```

5. Create yaml file with kubernetes cronjob, where select the schedule how to start the application:
    ```
    vi cronjob-goalkeeper.yaml
    kubectl apply -f cronjob-goalkeeper.yaml
    kubectl get cronjobs
    ```
6. Check whether the pods are created on the basis of this cronjob:
    ```
    kubectl get pods
    kubectl describe pod <it's name>
    ```
7. Take a look at the logs of this pod 
    ```
    kubectl logs -f <pod's name>
    ```
8. If you need to remove the cronjob, and then remove all the pods, run the following command:
    ```
    kubectl delete -f cronjob_goalkeeper.yaml
    ```

    

