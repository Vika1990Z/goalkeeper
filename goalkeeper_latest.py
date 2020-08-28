
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

environment = os.environ['ENV'] 

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

telegram_token=os.environ['OS_TELEGRAM_TOKEN']

my_chat_id=os.environ['OS_TELEGRAM_MY_CHAT_ID'] 
own_adress=os.environ['OWN_MAIL_ADDR']


print ()
print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Hello Today! The GOALKEEPER starts!\n') 
print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Target environment is {environment} in {fleio_auth_url}\n')

TELEGRAM_MESSAGE = f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Hello Today! The GOALKEEPER starts! Target environment is {environment} in {fleio_auth_url}'
requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage',
      dict(chat_id=my_chat_id, text=TELEGRAM_MESSAGE))


# logging function:
def logInsert(logStr):                                                                               
    with open('2logging_goalkeeper.log', 'a', encoding='utf-8') as f_obj:
        string = str(datetime.now())[0:19] + ': ' + logStr + '\n'
        f_obj.write(string)
#logInsert(f'Hello Today,\nThe GOALKEEPER starts!\n') 


# function collecting all our IP addresses into one array:
def ip_range():
    ip = []
    for i in range(1, 255):
        ip_i = str(f"185.91.80.{i}")
        ip.append(ip_i)
    for y in range(1, 255):    
        ip_y = str(f"185.91.81.{y}")
        ip.append(ip_y)
    for x in range(1, 255):    
        ip_x = str(f"185.91.82.{x}")
        ip.append(ip_x) 
    for n in range(1, 255):    
        ip_n = str(f"185.91.83.{n}")
        ip.append(ip_n)               
    ip_str = ' '.join(ip)
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: All IP_addresses is assembled and represented in a variable "ips"')
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: List of target ips is from Range: 185.91.80.1 – 185.91.83.254')
    return (ip_str)


# configure Connection to OpenStack
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

  
servers = conn.list_servers(detailed=False, all_projects=True, bare=False, filters=None)
print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Succesfully connect with openstackSDK')
print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: List_of_servers was found with openstackSDK') 

myToken = fleio_token
myUrl = str(f"{fleio_auth_url}/openstack/floatingips?page_size=10000")
head = {'Authorization': 'token {}'.format(myToken)}
response = requests.get(myUrl, headers=head)
response_status = response.status_code
if response_status == 200:
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Succesfully connect with Fleio API')
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: List_of_floating_IPs was found with Fleio API\n')
else:
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Page not found - problem with Authorization in Fleio')



ips = ip_range()



# function for finding project ID in Openstack by ip
def find_projectID_Openstack(ip):
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Start finding Project details in Openstack for IP: {ip}')
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Looking for IP: {ip} in list_of_servers in Openstack')  
    servers_str = json.dumps(servers, indent=2)
    servers_json = json.loads(servers_str)
    output_byIP_json = [x for x in servers_json if x['public_v4'] == ip]
    if output_byIP_json != []:
        projectID_Openstack = output_byIP_json[0]['project_id']
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project details in Openstack for IP: {ip} was FOUND among servers') 
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_ID in Openstack: {projectID_Openstack}')     
        return projectID_Openstack
    else:  
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: IP: {ip} was NOT_FOUND in list_of_servers in Openstack')
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Looking for IP: {ip} in list_of_floating_IPs in Fleio')        
        floatingIPs_json = json.loads(response.text)
        floatingIPs_str = json.dumps(floatingIPs_json, indent=2) 
        floatingIPs_json_objects = floatingIPs_json['objects'] 
        for objects in floatingIPs_json_objects:
            if objects["floating_ip_address"] == ip:
                projectID_Openstack = objects ["project"]
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project details in Fleio for IP: {ip} was FOUND among floatingIPs')
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_ID in Openstack: {projectID_Openstack}')
                return projectID_Openstack           
            else:
                projectID_Openstack = "NOT_FOUND"
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: IP: {ip} was NOT_FOUND in list_of_floating_IPs ')
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_ID in Openstack: {projectID_Openstack}')
                return projectID_Openstack



# function of finding Project Name in Openstack by it ID
def find_projectNAME_Openstack(projectID_Openstack):
    if projectID_Openstack == "NOT_FOUND":
        projectNAME_Openstack = 'NOT_FOUND'
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_NAME in Openstack: {projectNAME_Openstack}\n')
        return projectNAME_Openstack
    else:
        project = conn.get_project(projectID_Openstack, filters=None, domain_id=None)
        project_str = json.dumps(project, indent=2)
        project_json = json.loads(project_str)
        projectNAME_Openstack = project_json['name']
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_NAME in Openstack: {projectNAME_Openstack}\n')
        return projectNAME_Openstack        



# function of finding email address of the project owner in Fleio by its Project ID:
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
        print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Project_NAME for project_ID:{projectID_Openstack}  was FOUND in Openstack')
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
    msg['Subject'] = "Abuse Message from Ventus Cloud Security Guide"
    msg['From'] = from_adr
    msg['To'] = to_adr

    
    html = """\
    <html>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> 
      <head></head>
      <body>
        <p><b>Dear User,</b></p>
        <p><b>I'm your personal Ventus Cloud Security Advisor.</b></p>
        <p>While you're working in Ventus Cloud Portal, I monitor the security of your environment and inform you, if I found any security breaches.</p>
        <p></p>
        <p><u>Recently I've received a security alert about the next incident on your servers:</u></p>
        <p>{code}</p>
        <p></p>
        <p><i>These internet faced ports are well known and can be abused by DDoS, brute-force, exploits and other types of vulnerabilities. Furthermore, they allow potential attackers to gather information on the server or network for preparation of further attacks.</i></p>
        <p>We kindly ask you to take steps to mitigate potential risks and protect your deployments.</p>
        <p>We prepared <a href="https://ventuscloud.eu/docs/tutorials/Security_Guide">Security Guide</a> for you which describes how-to solve common issues.</p>
        <p>Also, we highly recommend you to configure <a href="https://ventuscloud.eu/docs/coretasks/security-groups">Security Groups</a>, this is our cloud-native firewall which is simple to use but very powerful.</p>
        <p>Until then, I will regularly remind you of this possible threat.</p>
        <p>And if you want to receive additional information or advice, please write to us <a href = "mailto: support@ventus.ag">support@ventus.ag</a> or create a <b>ticket</b> on our portal.</p>
        <p></p>
        <p><b>Kind regards,</b></p>
        <p><b>Your Ventus Cloud Security Advisor</b></p>
      </body>
    </html>
    """.format(code=code)
    part1=MIMEText(html, 'html')
    msg.attach(part1)

    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Login in to the mail from which reports will be sent is succesfull')
    server = smtplib.SMTP("smtp.office365.com:587")
    server.starttls()
    #server.set_debuglevel(True)                            
    server.login(from_adr, password)
    server.sendmail(from_adr, to_adr, msg.as_string())
    server.quit()


# The main function of nmap scanning of selected hosts on selected ports, which scans and uses all of the above functions for sending a scan report.
def scanning():
    danger_ports = '53,123,9200,389,5353,11211,6379,27017,1434,111,161,9306,9312,1900,10001,23,137,135,138,139,445,3306,5432,9042,9160,7000,7001,7199,8888,61620,61621'
    
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: List of dangerous ports: {danger_ports}\n')
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Start scanning according to the list of dangerous ports')

    nm = nmap.PortScanner()
    nm_scan_json = nm.scan(hosts=ips, arguments=f'-sS -sU -p {danger_ports}')
    nm_scan_str = json.dumps(nm_scan_json, indent=4)
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Scanning is COMLETED, all information is collected in a variable "nm_scan_str"')
    print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Analaze which IPaddress has open dangerous ports\n')
    
    host_open_ports_dict = {}
    host_projects_dict = {}

    host_open_ports_dict_console = {}
    host_projects_dict_console = {}

    for host in nm.all_hosts():
        output_host = f"<p style='color:#ff0000'>{host} - State : {nm[host].state()}:</p>"
        output_host_console = f"{host} - State : {nm[host].state()}:"
        
        open_ports_list = []
        open_ports_list_console = []
        for proto in nm[host].all_protocols():
            lport = nm[host][proto].keys()
            for port in lport:
                if nm[host][proto][port]['state'] == 'open':
                    output_port = f"<p>Port : {port}  State : {nm[host][proto][port]['state']}  Protocol : {proto};<p>"
                    open_ports_list.append(output_port)
                    open_ports_str = ' '.join(open_ports_list)

                    output_port_console = f"Port : {port}  State : {nm[host][proto][port]['state']}  Protocol : {proto};"
                    open_ports_list_console.append(output_port_console)
                    open_ports_str_console = '\n                     '.join(open_ports_list_console)
                  
        if open_ports_list != []:
            output = f"{output_host}\n{open_ports_str}"
            host_open_ports_dict[host]=output
            host_open_ports_dict.update({host : output}) 

            output_console = f"\n                     {output_host_console}\n                     {open_ports_str_console}"
            host_open_ports_dict_console[host]=output_console
            host_open_ports_dict_console.update({host : output_console}) 
            print(f'\n{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: The host {host} has the following open dangerous ports: {host_open_ports_dict_console[host]}')

            projectID_Openstack = find_projectID_Openstack(host)
            projectNAME_Openstack = find_projectNAME_Openstack(projectID_Openstack)
            host_projects_dict[host]=projectID_Openstack
            host_projects_dict.update({host : projectID_Openstack})
        else:
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: The host {host} has NO OPEN dangerous ports.\n')
    
    print ('_____________________________________________________________________________________________________ ')
    print(f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Start agrigating information conected with the same project')
    formatted_host_projects_dict = {}
    for pair in host_projects_dict.items():
        if pair[1] not in formatted_host_projects_dict.keys():
            formatted_host_projects_dict[pair[1]] = []
        formatted_host_projects_dict[pair[1]].append(pair[0])

    for pr in formatted_host_projects_dict.keys():
        full_inf_str = ''
        full_inf_str_console = ''
        for hs in formatted_host_projects_dict[pr]:
            inf_str = f'\n<br><b>{host_open_ports_dict[hs]}<b><br>'
            full_inf_str +=  inf_str
            
            inf_str_console = f'\n{host_open_ports_dict_console[hs]}'
            full_inf_str_console +=  inf_str_console
        print(f'\n{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Start looking for other project details for project: {pr}')
        found_email = find_email_fleio(pr)
        projectNAME_Openstack = find_projectNAME_Openstack(pr)
        all_found_inf_string = f'The project which has next details:\n\nID in OPENSTACK is: {pr} \nNAME in OPENSTACK is: {projectNAME_Openstack}\nEMAIL_ADDR: {found_email} \n\nhas the next problem on the folowing servers: {full_inf_str_console}'
        
        TELEGRAM_MESSAGE = f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: {all_found_inf_string}'
        requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage',
          dict(chat_id=my_chat_id, text=TELEGRAM_MESSAGE))

        if environment == 'DEV':
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: As target environment is DEV, all reports will be sent to our own adresses')
            to_adr = own_adress
            code = f'{full_inf_str}'
            sendmail_report(to_adr, code)
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Report sent successfully to {to_adr}\n')

        if environment == 'PROD':
            print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: As target environment is PROD, all reports will be sent to owner of this host')
            to_adr = found_email
            code = f'{full_inf_str}'

            if to_adr == False or to_adr == 'NOT_FOUND':
                sendmail_report(own_adress, code)
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: As EMAIL_ADDR was NOT_FOUND a report was sent to OWN_adress')
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Report sent successfully to {own_adress}\n')
            else:
                sendmail_report(to_adr, code)
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Report was sent to owner of this host {host} on email {to_adr}')
                print (f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())}: Report sent successfully to {to_adr}\n')

scanning()            
        

