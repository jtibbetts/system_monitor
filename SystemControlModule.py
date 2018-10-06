
import sys
import requests
import json
import subprocess


def read_json(url):
    result = None
    error = None
    try:
        request = requests.get(url)
    except Exception as exc:
        result = None
        error = "Connection error: " + str(exc)

    if not error:
        try:
            result = request.json()
        except Exception as exc:
            result = None
            error = "Read error: " + str(exc)

    return (result, error)

def ssh(host, command):
    ssh = subprocess.Popen(["ssh", "%s" % host, command],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        if error:
            print >> sys.stderr, "ERROR: %s" % error
    else:
        print result


class SystemControl:
    SYSTEM_UP = 'up'
    SYSTEM_DOWN = 'down'

    def __init__(self, config_dict):
        pass

    def is_system_up(self):
        pass

    def system_restart(self):
        if self.is_system_up():
            self.system_down()
        self.system_up()

    def system_up(self):
        pass

    def system_down(self):
        pass

class OpenChannelControl(SystemControl):
    def __init__(self, **config_dict):
        self.base_url = config_dict['base_url']
        self.url = self.base_url + "/api/users/me"

    def is_system_up(self):
        result = True
        (result, error) = read_json(self.url)
        if result:
            if 'oc_session' in result.keys():
                pass
            else:
                error = "No oc_session key is present in result set"

        if error:
            print error

        return (error == None, error)

    def system_restart(self):
        ssh("root@ford.kinexis.com", "service nginx restart")
        ssh("kinexis@ford.kinexis.com", "pm2 restart all")

class NdarControl(SystemControl):
    def __init__(self, **config_dict):
        self.base_url = config_dict['base_url']
        self.url = self.base_url + "/site/BeachChalet/SanFrancisco/CA/"

    def is_system_up(self):
        result = True
        (result, error) = read_json(self.url)
        if result:
            if 'username' in result.keys():
                pass
            else:
                error = "No oc_session key is present in result set"

        if error:
            print error

        return (error == None, error)

    def system_restart(self):
        ssh("root@ford.kinexis.com", "service nginx restart")

class NdarCredentialControl(SystemControl):
    def __init__(self, **config_dict):
        self.base_url = config_dict['base_url']
        self.url = self.base_url + "/test_credentials"

    def is_system_up(self):
        result = True
        (result, error) = read_json(self.url)
        try:
            if result:
                if result['results']['status'] == 'OK':
                    error = None
                else:
                    error = result['results']['error_message']
        except:
            error = 'Indeterminate access error'

        if error:
            print error

        return (error == None, error)

    def system_restart(self):
        pass

class TestSystemControl(SystemControl):

    def __init__(self, **config_dict):
        self.system_status = config_dict['system_status']
        if 'no_restart_on_bounce' in config_dict:
            self.no_restart_on_bounce = config_dict['no_restart_on_bounce']
        else:
            self.no_restart_on_bounce = False

    def is_system_up(self):
        return (self.system_status == SystemControl.SYSTEM_UP, "")

    def system_up(self):
        self.system_status = SystemControl.SYSTEM_UP

    def system_down(self):
        self.system_status = SystemControl.SYSTEM_DOWN

    def system_restart(self):
        if self.is_system_up():
            self.system_down()
        if not self.no_restart_on_bounce:
            self.system_up()