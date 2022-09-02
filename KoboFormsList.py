import configparser

import requests
from PyQt5.QtCore import QSettings

kobo = configparser.ConfigParser()
kobo.read('ini/KoboAuth.ini')

url_kobo = kobo['Kobo Credentials']['url']
username_kobo = kobo['Kobo Credentials']['username']
password_kobo = kobo['Kobo Credentials']['password']


def getproxiesConf():
    """
    This function is used to configure all the proxy settings.
    :return:
    """
    s = QSettings()  # getting proxy from qgis options settings
    proxyEnabled = s.value("proxy/proxyEnabled", "")
    proxyType = s.value("proxy/proxyType", "")
    proxyHost = s.value("proxy/proxyHost", "")
    proxyPort = s.value("proxy/proxyPort", "")
    proxyUser = s.value("proxy/proxyUser", "")
    proxyPassword = s.value("proxy/proxyPassword", "")
    if proxyEnabled == "true" and proxyType == 'HttpProxy':  # test if there are proxy settings
        proxyDict = {
            "http": "http://%s:%s@%s:%s" % (proxyUser, proxyPassword, proxyHost, proxyPort),
            "https": "http://%s:%s@%s:%s" % (proxyUser, proxyPassword, proxyHost, proxyPort)
        }
        return proxyDict
    else:
        return None

def getFormList():
    """
    This function will return the dictionary of all the forms present in the kobotoolbox in json format

    :return:
    dictionary containing name of the form as key and id as value
    Example: ({'test': 'aDHQqdStRmoRUwSZJb5P35', 'iirs_buildings': 'aumGeYCKpLmoK6jkcDgcUv'}, <Response [200]>)
    """

    user = username_kobo
    password = password_kobo
    turl = url_kobo
    proxies = getproxiesConf()

    if turl:
        url = turl + 'api/v2/assets'
    else:
        # print("Enter correct url.")
        return None, None

    para = {'format': 'json'}
    keyDict = {}
    questions = []

    try:
        response = requests.get(url, proxies=proxies, auth=(user, password), params=para)
        forms = response.json()
        for form in forms['results']:
            if form['asset_type'] == 'survey' and form['deployment__active'] == True:
                keyDict[form['name']] = form['uid']
        return keyDict
    except:
        # self.iface.messageBar().pushCritical(self.tag, self.tr("Invalid url username or password"))
        # print("Invalid username or password")
        return None, None

list_of_forms = list(getFormList().items())

for list in list_of_forms:
    # print(list)
    kobo['Forms List'][list[0]] = list[1]
    kobo['Forms List']['last used'] = ""
    with open('ini/KoboAuth.ini', 'w') as configfile:
        kobo.write(configfile)

