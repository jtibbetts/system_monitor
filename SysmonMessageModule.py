
import os.path
import json
import time
from datetime import datetime
from slugify import slugify
from dateutil.parser import parse

BEGINNING_OF_EPOCH = datetime(1970, 3, 1)

def domain_from_base_url(base_url):
    zones = base_url.split("://")
    return zones[-1]

class SysmonMessage:
    def __init__(self, notify_cache_folder, notify_cache_filename, base_url):
        "construct base message from typical defaults"
        self.notify_cache_path = os.path.join(notify_cache_folder, notify_cache_filename)
        self.base_url = base_url
        self.domain = domain_from_base_url(base_url)
        self.created_at = datetime.utcnow()
        self.notified_at = BEGINNING_OF_EPOCH

        zones = notify_cache_filename.split('.')
        zones.pop()
        notify_cache_name = '.'.join(zones)

        self.domain_slug = slugify(notify_cache_name)
        zones = self.domain_slug.split('-')
        self.server_label = zones[0].capitalize()

        self.system_status = "up"
        self.notify_type = "scheduled"
        self.subject = "System status: " + self.system_status
        self.message_lines = []

        self.is_current_state_emailed = False

    def add_line_to_message_lines(self, line):
        tstring = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d--%H:%M:%S')
        self.message_lines.append(tstring + ": " + line)

    def delete_notify_cache(self):
        os.remove(self.notify_cache_path)

    def get_message_content(self):
        return '\n'.join(self.message_lines)

    def get_notified_at(self):
        if self.notified_at:
            return self.notified_at
        else:
            return BEGINNING_OF_EPOCH

    def is_notify_cache_exists(self):
        return os.path.exists(self.notify_cache_path)

    def read_notify_cache(self):
        result = True
        error_msg = ""
        try:
            with open(self.notify_cache_path) as infile:
                msg_str = infile.read()
                try:
                    msg_obj = json.loads(msg_str)
                    self.domain = msg_obj['domain']
                    self.server_label = msg_obj['server_label']
                    self.system_status = msg_obj['system_status']
                    self.notify_type = msg_obj["notify_type"]
                    self.notified_at = parse(msg_obj['notified_at'])
                    self.subject = msg_obj['subject']
                    message_text = msg_obj['msg_text']
                    self.message_lines = message_text.split('\n')
                    self.is_current_state_emailed = msg_obj['is_current_state_emailed']
                except Exception as exc:
                    # bad or empty json file
                    result = False
                    error_msg = "Invalid file contents"
        except Exception as exc:
            result = False
            error_msg = "No notify_cache exists"

        return (result, error_msg)

    def set_system_status(self, new_system_status):
        self.system_status = new_system_status
        self.subject = "System status: " + self.system_status

    def write_notify_cache(self):
        msg_obj = {}
        msg_obj['system_status'] = self.system_status
        msg_obj['domain'] = self.domain
        msg_obj['server_label'] = self.server_label
        msg_obj['notify_type'] = self.notify_type
        msg_obj['created_at'] = self.created_at.isoformat()
        msg_obj['notified_at'] = self.notified_at.isoformat()
        msg_obj['subject'] = "System status: " + self.system_status
        msg_obj['msg_text'] = self.get_message_content()
        msg_obj['is_current_state_emailed'] = self.is_current_state_emailed

        msg_str = json.dumps(msg_obj)
        with open(self.notify_cache_path, 'w') as outfile:
            outfile.write(msg_str)

