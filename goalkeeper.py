from datetime import datetime  
import json

import requests
import argparse

import nmap
import openstack
from openstack import connection

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



# функция обеспечивающая ведение логов:
def logInsert(logStr):                                                                               
    with open('logging_goalkeeper.log', 'a', encoding='utf-8') as f_obj:
        string = str(datetime.now())[0:19] + ': ' + logStr + '\n'
        f_obj.write(string)

logInsert(f'\n\nHello Today,\nThe GOALKEEPER starts!\n')            


# функция собирающая все наши IPадреса в один массив:
def ip_range():
    ip = []
    for i in range(1, 128):
        ip_i = str(f"188.40.161.{i}")
        ip.append(ip_i)
    for y in range(33, 64):
        ip_y = str(f"46.4.240.{y}")
        ip.append(ip_y)
    ip_str = ' '.join(ip)
    logInsert(f'An array of all IPaddresses is assembled and represented in a variable "ips"')
    return (ip_str)


# функция обеспечивающая подключение к Openstack:
def connection_with_openstack():
    conn = connection.Connection(
        region_name='RegionOne',
        identity_api_version=3,
        compute_api_version=2,
        auth=dict(
            auth_url='https://cloud.vstack.ga:5000/v3',
            username='admin',
            password='5e0f98157fb42d26d',
            user_domain_id='default',
            project_id='9ee58a52925d4b9fbe78e77737afb5d7')
        )
    logInsert(f'Succesfully connect with openstackSDK')    
    return conn    



# функция поиска имени проэкта во Fleio по его ID в Openstack, которому пренадлежит указанный IPадрес: 
def find_project_name(ip):
    logInsert(f'Function "find_project_name({ip})" starts')
    # блок поиска ID проэкта в Openstack
    conn = connection_with_openstack()
    servers = conn.list_servers(detailed=False, all_projects=True, bare=False, filters=None)
    logInsert(f'List of servers was found with openstackSDK')
    servers_str = json.dumps(servers, indent=2)
    servers_json = json.loads(servers_str)
    output_byIP_json = [x for x in servers_json if x['public_v4'] == ip]
    if output_byIP_json == []:
        logInsert(f'Target IP {ip} was not found in list of servers ')
        floatingIPs = conn.list_floating_ips(filters=None)
        logInsert(f'List of floating IPs was found because target IP was not in list of servers')
        floatingIPs_str = json.dumps(floatingIPs, indent=2)
        floatingIPs_json = json.loads(floatingIPs_str)
        output_byfloatingIPs_json = [x for x in floatingIPs_json if x['floating_ip_address'] == ip]
        if output_byfloatingIPs_json == []:
            found_projectID_openstack = "Ip Not Found"
            logInsert(f'Target IP {ip} was not found in list of floating IPs ')
        else:
            found_projectID_openstack = output_byfloatingIPs_json[0]['project_id']
            logInsert(f'ProjectID in openstack of target ip: {ip} was found among floatingIPs and it is next : {found_projectID_openstack}')
    else:
        found_projectID_openstack = output_byIP_json[0]['project_id']
        logInsert(f'ProjectID in openstack of host: {ip} was found among servers and it is next : {found_projectID_openstack}') 
    projectID = found_projectID_openstack
    # блок поиска имени проэкта во Fleio
    if projectID == "Ip Not Found":
        projectNAME_Fleio = 'Project name not found'
        logInsert(f'Project name not found because Ip {ip} Not Found not in servers_list not in list_of_flostingIPs')
        logInsert(f'Function "find_project_name({ip})" completed, but project NAME not found in openstack')
    else:
        conn = connection_with_openstack()
        projects = conn.identity.projects()
        lst = list(projects)
        logInsert(f'Project list in openstack was found')
        projects_str = json.dumps(lst, indent=2)
        projects_json = json.loads(projects_str)
        output_byID_json = [x for x in projects_json if x['id'] == projectID]
        found_projectNAME = output_byID_json[0]['name']
        logInsert(f'Project NAME was found and it is next : {found_projectNAME}')
        find_projectNAME_Fleio = found_projectNAME.split(' - ')
        projectNAME_Fleio = find_projectNAME_Fleio[0]
        logInsert(f'Project NAME formatted for Fleio: {projectNAME_Fleio}')
        logInsert(f'Function "find_project_name({ip})" completed successfully - project NAME in openstack for Fleio is: {projectNAME_Fleio}')
    return projectNAME_Fleio



# функция поиска почтового адресса проэкта во Fleio, которому пренадлежит указанный IPадрес:
def find_email_fleio(ip):
    logInsert(f'Function "find_email_fleio({ip})" starts')
    logInsert(f'Firstly, needs to define project NAME')
    project_name = find_project_name(ip) 
    if project_name == 'Project name not found':
        found_email = "Email not found"
        logInsert (f'Email not found because Project name of target ip {ip} not defined even in openstack')
        logInsert (f'Function "find_email_fleio({ip})" completed but email was not found')
    else:
        found_email = False
        pages = []
        for i in range (1, 100):    
            myToken = '96a76c696d504c65d41b1cdf623786e7421ea072'
            myUrl = str(f"https://sportal.ventuscloud.eu/backend/staffapi/clients?page={i}")
            head = {'Authorization': 'token {}'.format(myToken)}
            logInsert (f'Authorization in Fleio is succesfull')
            response = requests.get(myUrl, headers=head)
            response_status = response.status_code
            response_json = json.loads(response.text)
            data_from_page = json.dumps(response_json, indent=2)    
            if response_status == 200:
                response_json_objects = response_json['objects']
                pages.append(response_json_objects)
                i += 1
                logInsert (f'Page {i-1} - response_status_code  = {response_status} so information about clients in FLEIO from page {i-1} was got')
            else:
                logInsert (f'Pagging was ended, all information is collected in a variable "pages"')
                break
        logInsert (f'Start browsing every page and analyzing each object on page')
        for page in pages:
            for objects in page:
                if objects['name'] == project_name:
                    found_email =  (objects['email'])
                    logInsert (f'Found email for project {project_name} is {found_email}')
                    break 
        logInsert(f'Function "find_email_fleio({ip})" completed successfully - found email is {found_email}')                
    return found_email     



# функция отправки отчета сканирования на найденный почтовый адресс, владельца проэкта во Fleio:
def sendmail_report(to_adr, code):
    logInsert(f'Function "sendmail_report(to_adr, code)" starts')
    from_adr ='support@ventus.ag'
    password  = "9nkvZ4V6jD36qR"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Abuse Message"
    msg['From'] = from_adr
    msg['To'] = to_adr

    logInsert(f'Start to form the body of the report, which will contain the scan results')
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
        <a href="https://vika1990z.github.io/docs/docs/tutorials/Security_Guide">Security_Guide</a>
        <p>Kind regards,</p>
        <p>Your Ventus Cloud Team</p>
      </body>
    </html>
    """.format(code=code)
    part1=MIMEText(html, 'html')
    msg.attach(part1)
    logInsert(f'Log in to the mail from which reports will be sent (now it is {from_adr})')
    server = smtplib.SMTP("smtp.office365.com:587")
    server.starttls()
    #server.set_debuglevel(True)                            # Включаем режим отладки, если не нужен - можно закомментировать
    server.login(from_adr, password)
    server.sendmail(from_adr, to_adr, msg.as_string())
    server.quit()



# основная функция nmap сканирования выбранных хостов по выбранным портам, которая сканирует и использует все вышеперчисленные функции, чтоб в конечном итоге отправить отчет сканирования
def scanning():
    logInsert(f'Function "scanning()" starts')
    ips = ip_range()
    nm = nmap.PortScanner()
    logInsert(f'Start scanning each IPaddress according to the list of dangerous ports')
    nm_scan_json = nm.scan(hosts=ips, arguments='-sS -sU -p 53,123,9200,389,5353,11211,6379,27017,1434,111,161,9306,9312,1900,10001,23,137,135,138,139,445,3306,5432,9042,9160,7000,7001,7199,8888,61620,61621')
    nm_scan_str = json.dumps(nm_scan_json, indent=4)
    logInsert(f'Scanning is completed, all information is collected in a variable "nm_scan_str"')
    logInsert(f'Start analazing which IPaddress has open dangerous ports')
    for host in nm.all_hosts():
        output_host = f"{host} - State : {nm[host].state()}:"
        open_ports = []
        for proto in nm[host].all_protocols():
            lport = nm[host][proto].keys()
            for port in lport:
                if nm[host][proto][port]['state'] == 'open':
                    output_port = f"port : {port}  state : {nm[host][proto][port]['state']}  Protocol : {proto}"
                    open_ports.append(output_port)
                    open_ports_str = ';\n'.join(open_ports)
        if open_ports != []:
            output = f"\n\n{output_host}\n{open_ports_str}\n"
            logInsert(f'Analyzing is comleted: the host {host} has the following open dangerous ports: {output}')
        
            logInsert(f'Start looking for contact details of {host} for sending a report')
            to_adr = find_email_fleio(host)
            code = output

            if to_adr == False or to_adr == 'Email not found':
                sendmail_report('v.zubyenko@gmail.com', code)
                logInsert(f'As contact details was not found a report was sent to my own adress')
                logInsert(f'Report sent successfully')
                logInsert(f'______________________________________________________________________________')
            else:
                sendmail_report(to_adr, code)
                logInsert(f'Report was sent to owner of this host {host}')
                logInsert(f'Report sent successfully')
                logInsert(f'______________________________________________________________________________')
            print (output)
            print (to_adr)

scanning()

logInsert(f'\n\nThat is all for today,\nThe GOALKEEPER completed!\n')          