
import os
import os.path
import sys
import time
from datetime import datetime
from slugify import slugify
from urlparse import urlparse

import config
from SysmonMessageModule import SysmonMessage

from SysmonMessageModule import domain_from_base_url

from SystemControlModule import SystemControl
from SystemControlModule import OpenChannelControl
from SystemControlModule import TestSystemControl

import create_and_send_text_email

TEST_MODE = True

RESTART_INTERVAL = 3

BEGINNING_OF_EPOCH = datetime(1970, 3, 1)


def notify(sm, is_system_up, error_message, is_mail_at_end):
    now = datetime.now()
    notified_at = sm.get_notified_at()
    start_now = start_of_day(now)
    start_notified_at = start_of_day(notified_at)
    # if it's just back up or it's down and notify is stale
    if is_system_up or start_notified_at < start_now:
        if is_mail_at_end:
            create_and_send_text_email.set_up_email_and_send(config.ADMIN_CONFIG_PATH, config.EMAIL_SENDER, config.EMAIL_TO,
                                                 sm.subject, sm.get_message_content())
        else:
            print "Email would be sent: \n" + sm.get_message_content()

        sm.is_current_state_emailed = True
        if sm.system_status == 'down':
            # update notification stamp and write it back out
            print "system down: updating notification file"
            sm.notified_at = now
            sm.write_notify_cache()
        else:
            print "system up: removing notification file"
            sm.delete_notify_cache()
    else:
        sm.is_current_state_emailed = False
        print "Recent notification made"

def start_of_day(ts):
    return datetime(ts.year, ts.month, ts.day)

def validate_openchannel(sctl, url):
    return sctl.is_system_up(url)

def process(base_url, restart_after, is_mail_at_end, sctl_obj_or_str):
    parse_result = urlparse(base_url)
    hostname = parse_result.hostname
    domain = domain_from_base_url(base_url)
    notify_cache_filename = slugify(hostname) + '.json'
    sm = SysmonMessage(config.CLOSET_DIR, notify_cache_filename, base_url)
    sm.read_notify_cache()

    if type(sctl_obj_or_str) is str:
        sysctl_cls_str = sctl_obj_or_str
        mod = __import__("SystemControlModule")
        sctl_cls = getattr(mod, sysctl_cls_str)
        sctl = sctl_cls(base_url=base_url)
    else:
        sysctl_cls_str = None
        sctl = sctl_obj_or_str

    system_status_at_startup = sm.system_status
    if sm.is_notify_cache_exists():
        result, error_msg = sm.read_notify_cache()
        if not result:
            print "Error reading file: " + error_msg
            os.remove(sm.notify_cache_path)
            sys.exit(0)

    restart_after = float(restart_after)
    status_log = []

    # ping OC and bounce if necessary
    (is_system_up, error_message) = sctl.is_system_up()
    if is_system_up:
        sm.set_system_status(SystemControl.SYSTEM_UP)
        if system_status_at_startup == SystemControl.SYSTEM_UP:
            # server still up...no comment necessary
            return sm
        print sm.server_label + " is up"
        sm.add_line_to_message_lines(sm.server_label + " is back up")
        if system_status_at_startup == "down":
            # NOTIFY that it's back up
            notify(sm, sctl.is_system_up, error_message, is_mail_at_end)
        if sm.is_notify_cache_exists():
            sm.delete_notify_cache()
            print "notify cache is removed"
        return sm
    else:
        sm.set_system_status(SystemControl.SYSTEM_DOWN)
        sm.add_line_to_message_lines(sm.server_label + " is not responding")
        if error_message != None and error_message != '':
            sm.add_line_to_message_lines(error_message)

    # give it a jiffy to rest
    time.sleep(restart_after)

    (is_system_up, error_message) = sctl.is_system_up()
    if is_system_up:
        sm.set_system_status(SystemControl.SYSTEM_UP)
        print sm.server_label + " is up"
        system_status = "restarted"
        sm.add_line_to_message_lines(sm.server_label + " has been successfully restarted")
    else:
        sm.set_system_status(SystemControl.SYSTEM_DOWN)
        print sm.server_label + " could not be restarted"
        system_status = 'down'
        sm.add_line_to_message_lines(sm.server_label + " could not be restarted")

    sm.write_notify_cache()
    notify(sm, is_system_up, error_message, is_mail_at_end)

    return sm

if __name__ == '__main__':
    try:
        import argparse

        argparser = argparse.ArgumentParser()
        argparser.add_argument("base_url", help="List of base URL")
        argparser.add_argument("--sysctl_cls", help="SystemControl class name", default="OpenChannelControl")
        argparser.add_argument("--restart_after", help="Attempt restart after seconds", default="4")
        args = argparser.parse_args()
    except ImportError:
        args = None

    process(args.base_url, args.restart_after, True, args.sysctl_cls)