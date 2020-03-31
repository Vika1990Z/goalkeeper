
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