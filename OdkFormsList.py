import configparser
import requests
from PyQt5.QtCore import QSettings

# ODK VARIABLES
odk = configparser.ConfigParser()
odk.read('OdkAuth.ini')

url_odk = odk['Odk Credentials']['url']
username_odk = odk['Odk Credentials']['username']
password_odk = odk['Odk Credentials']['password']
last_project_used_odk = odk['Projects ODK']['last used']

def getFormList():
    """Retrieves list of all forms using user entered credentials
    Returns
    ------
    forms - dictionary
        contains all forms in user's account
    x - HTTP response
        authentication response
    """

    user = username_odk
    password = password_odk
    c_url = url_odk
    data = {'email': user, 'password': password}
    if not c_url:
        print("Enter url in OdkAuth.ini file")
        return None, None
    headers = {"Content-Type": "application/json"}
    projects = {}
    forms = {}
    project_name = last_project_used_odk
    try:
        x = requests.post(c_url + "v1/sessions", json=data, headers=headers)
        token = x.json()["token"]
        usertoken = token
        projects_response = requests.get(c_url + "v1/projects/", headers={"Authorization": "Bearer " + token})
        for p in projects_response.json():
            if p["name"] == project_name:
                project_id = p["id"]
        form_response = requests.get(c_url + "v1/projects/" + str(project_id) + "/forms/",
                                     headers={"Authorization": "Bearer " + token})
        for form in form_response.json():
            forms[form["name"]] = form["enketoOnceId"]
        return forms
    except:
        print("Invalid url, username, project name or password")
        return None, None

list_of_forms = list(getFormList().items())

for list in list_of_forms:
    # print(list)
    odk['Projects ODK'][list[0]] = list[1]
    with open('OdkAuth.ini', 'w') as configfile:
        odk.write(configfile)
