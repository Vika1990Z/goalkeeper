
from datetime import datetime  
from time import gmtime, strftime

import json
import os

import requests
import argparse

import nmap
import openstack
from openstack import connection

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Hello Today! The GOALKEEPER starts!\n') 



openstack_region_name=os.environ['OS_OPENSTACK_REGION_NAME']
openstack_auth_url=os.environ['OS_OPENSTACK_URL']
openstack_username=os.environ['OS_OPENSTACK_USERNAME']
openstack_password=os.environ['OS_OPENSTACK_PASSWORD']
openstack_user_domain_id=os.environ['OS_OPENSTACK_USER_DOMAIN_ID']
openstack_project_id=os.environ['OS_OPENSTACK_PROJECT_ID']
fleio_token = os.environ['OS_FLEIO_TOKEN']
fleio_auth_url = os.environ['OS_FLEIO_URL']
mail_from_adr=os.environ['OS_MAIL_FROM_ADR']
mail_password=os.environ['OS_MAIL_PASSWORD']

own_adress = 'v.zubyenko@gmail.com'

# logging function:
def logInsert(logStr):                                                                               
    with open('2logging_goalkeeper.log', 'a', encoding='utf-8') as f_obj:
        string = str(datetime.now())[0:19] + ': ' + logStr + '\n'
        f_obj.write(string)
#logInsert(f'Hello Today,\nThe GOALKEEPER starts!\n') 


# function collecting all our IP addresses into one array:
def ip_range():
    ip = []
    for i in range(1, 128):
        ip_i = str(f"188.40.161.{i}")
        ip.append(ip_i)
    for y in range(33, 64):    
        ip_y = str(f"46.4.240.{y}")
        ip.append(ip_y)
    ip_str = ' '.join(ip)
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: All IP_addresses is assembled and represented in a variable "ips"')
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: ips = 188.40.161.1 - 188.40.161.127; 46.4.240.33 - 46.4.240.63')
    return (ip_str)

ips = ip_range()

conn = connection.Connection(
    region_name=openstack_region_name,
    identity_api_version=3,
    compute_api_version=2,
    auth=dict(
        auth_url=openstack_auth_url,
        username=openstack_username,
        password=openstack_password,
        user_domain_id=openstack_user_domain_id,
        project_id=openstack_project_id)
    )

print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Succesfully connect with openstackSDK')  
servers = conn.list_servers(detailed=False, all_projects=True, bare=False, filters=None)
print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: List_of_servers was found with openstackSDK') 
floatingIPs = conn.list_floating_ips(filters=None)
print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: List_of_floating_IPs was found with openstackSDK\n')


def find_projectID_Openstack(ip):
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Start finding Project details in Openstack for IP: {ip}')
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Looking for IP: {ip} in list_of_servers in Openstack')  
    servers_str = json.dumps(servers, indent=2)
    servers_json = json.loads(servers_str)
    output_byIP_json = [x for x in servers_json if x['public_v4'] == ip]
    if output_byIP_json == []:
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: IP: {ip} was NOT_FOUND in list_of_servers in Openstack')
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Looking for IP: {ip} in list_of_floating_IPs in Openstack')        
        floatingIPs_str = json.dumps(floatingIPs, indent=2)
        floatingIPs_json = json.loads(floatingIPs_str)
        output_byfloatingIPs_json = [x for x in floatingIPs_json if x['floating_ip_address'] == ip]
        if output_byfloatingIPs_json == []:
            projectID_Openstack = "NOT_FOUND"
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: IP: {ip} was NOT_FOUND in list_of_floating_IPs ')
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_ID in Openstack: {projectID_Openstack}')
        else:
            projectID_Openstack = output_byfloatingIPs_json[0]['project_id']
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project details in Openstack for IP: {ip} was FOUND among floatingIPs')
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_ID in Openstack: {projectID_Openstack}')            
    else:
        projectID_Openstack = output_byIP_json[0]['project_id']
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project details in Openstack for IP: {ip} was FOUND among servers') 
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_ID in Openstack: {projectID_Openstack}')     
    return projectID_Openstack


def find_email_fleio(projectID_Openstack):
    

    if projectID_Openstack == "NOT_FOUND":
        projectNAME_Openstack = 'NOT_FOUND'
        found_email = "NOT_FOUND"
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project details in Openstack was NOT_FOUND because IP_NOT_FOUND not in servers_list not in list_of_flostingIPs')
        return found_email    
    else:
        project = conn.get_project(projectID_Openstack, filters=None, domain_id=None)
        project_str = json.dumps(project, indent=2)
        project_json = json.loads(project_str)
        projectNAME_Openstack = project_json['name']
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_NAME was FOUND in Openstack')
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_NAME in Openstack: {projectNAME_Openstack}')
        projectNAME_Openstack_formatted = projectNAME_Openstack.split(' - ')
        if len(projectNAME_Openstack_formatted) < 2:
            project_Fleio = 'NOT_FOUND'
            projectNAME_Fleio = 'NOT_FOUND'
            projectID_Fleio = 'NOT_FOUND'
            found_email = "NOT_FOUND"
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project details in Fleio was NOT_FOUND because Project was created not from Fleio')
            return found_email  
        else:
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project details in Fleio was FOUND and formatted')
            projectNAME_Fleio = projectNAME_Openstack_formatted[0]
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_NAME in Fleio: {projectNAME_Fleio}')
            projectID_Fleio = projectNAME_Openstack_formatted[-1]
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_ID in Fleio: {projectID_Fleio}')


            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Start finding EMAIL_ADDR in Fleio')
            found_email = False
            pages = []
            myToken = fleio_token
            myUrl = str(f"{fleio_auth_url}/clients/{projectID_Fleio}")
            head = {'Authorization': 'token {}'.format(myToken)}
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Authorization in Fleio is succesfull')
            response = requests.get(myUrl, headers=head)
            response_status = response.status_code
            response_json = json.loads(response.text)
            data_from_page = json.dumps(response_json, indent=2)    
            found_email =  (response_json['email'])
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: EMAIL_ADDR was FOUND for ProjectNAME: {projectNAME_Fleio}')
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: EMAIL_ADDR: {found_email}') 
            return found_email     

# function of sending a scan report to the found email address of the project owner in Fleio:
def sendmail_report(to_adr, code):
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Start formulating a report')
    from_adr = mail_from_adr
    password = mail_password
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Abuse Message"
    msg['From'] = from_adr
    msg['To'] = to_adr

    
    html = """\
    <html>
      <head></head>
      <body>
        <p>Dear User,</p>
        <p>We have received a security alert from our security guide.</p>
        <br>{code}<br>
        <p>Please investigate and solve the reported issue.</p>
        <p>It is not required that you reply to either us.</p>
        <p>If the issue has been fixed successfully, you should not receive any further notifications.</p>
        <p>In case of further questions, please contact support@ventus.ag.</p>
        <p>Additional information can be found at the link below.</p>
        <a href="https://ventuscloud.eu/docs/tutorials/Security_Guide">Security_Guide</a>
        <p>Kind regards,</p>
        <p>Your Ventus Cloud Team</p>
      </body>
    </html>
    """.format(code=code)
    part1=MIMEText(html, 'html')
    msg.attach(part1)

    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Login in to the mail from which reports will be sent is succesfull')
    server = smtplib.SMTP("smtp.office365.com:587")
    server.starttls()
    #server.set_debuglevel(True)                            # Включаем режим отладки, если не нужен - можно закомментировать
    server.login(from_adr, password)
    server.sendmail(from_adr, to_adr, msg.as_string())
    server.quit()


# The main function of nmap scanning of selected hosts on selected ports, which scans and uses all of the above functions for sending a scan report.
def scanning():
    danger_ports = '53,123,9200,389,5353,11211,6379,27017,1434,111,161,9306,9312,1900,10001,23,137,135,138,139,445,3306,5432,9042,9160,7000,7001,7199,8888,61620,61621'
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Start scanning according to the list of dangerous ports')
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: List of dangerous ports: {danger_ports}')
    nm = nmap.PortScanner()
    nm_scan_json = nm.scan(hosts=ips, arguments=f'-sS -sU -p {danger_ports}')
    nm_scan_str = json.dumps(nm_scan_json, indent=4)
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Scanning is COMLETED, all information is collected in a variable "nm_scan_str"')
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Analaze which IPaddress has open dangerous ports\n')
    for host in nm.all_hosts():
        output_host = f"{host} - State : {nm[host].state()}:"
        open_ports = []
        for proto in nm[host].all_protocols():
            lport = nm[host][proto].keys()
            for port in lport:
                if nm[host][proto][port]['state'] == 'open':
                    output_port = f"port : {port}  state : {nm[host][proto][port]['state']}  Protocol : {proto}"
                    open_ports.append(output_port)
                    open_ports_str = ';\n               '.join(open_ports)
        if open_ports != []:
            output = f"\n               {output_host}\n               {open_ports_str}"
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: The host {host} has the following open dangerous ports: {output}')
        

            projectID_Openstack = find_projectID_Openstack(host)
            found_email = find_email_fleio(projectID_Openstack)

            to_adr = found_email
            code = output

            if to_adr == False or to_adr == 'NOT_FOUND':
                own_adress = 'v.zubyenko@gmail.com'
                sendmail_report(own_adress, code)
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: As EMAIL_ADDR was NOT_FOUND a report was sent to OWN_adress')
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Report sent successfully to {own_adress}\n')
            else:
                sendmail_report(to_adr, code)
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Report was sent to owner of this host {host} on email {to_adr}')
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Report sent successfully to {to_adr}\n')

        else:
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: The host {host} has NO OPEN dangerous ports.\n')

scanning()    
