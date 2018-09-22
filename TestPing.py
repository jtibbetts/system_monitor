import unittest
import os
import json
from datetime import datetime, timedelta
from dateutil.parser import parse

import ping_openchannel
from SystemControlModule import SystemControl
from SystemControlModule import TestSystemControl

import config

URL = "https://localhost:8000/apis/users/me"
NOTIFY_FILENAME = "localhost.json"

NOTIFY_BEGIN_OF_EPOCH = 'notify_begin_of_epoch'
NOTIFY_TODAY = 'notify_today'
NOTIFY_YESTERDAY = 'notify_yesterday'

no_restart_on_bounce=True = True

def clear_notify_cache():
    if is_notify_cache():
        os.remove(os.path.join(config.CLOSET_DIR, NOTIFY_FILENAME))

def is_notify_cache():
    return os.path.exists(os.path.join(config.CLOSET_DIR, NOTIFY_FILENAME))

def replace_cache(test_filename, notify_date_type=NOTIFY_TODAY):
    with open(os.path.join(config.CLOSET_DIR, test_filename + ".json")) as infile:
        msg_str = infile.read()
        msg_obj = json.loads(msg_str)
    notified_at = parse(msg_obj['notified_at'])
    if notify_date_type == NOTIFY_BEGIN_OF_EPOCH:
        new_notified_at = datetime(1970, 3, 1)
    elif notify_date_type == NOTIFY_YESTERDAY:
        new_notified_at = notified_at - timedelta(days=1)
    else:
        new_notified_at = datetime.now() - timedelta(minutes=5)
    msg_obj['notified_at'] = new_notified_at.isoformat()
    with open(os.path.join(config.CLOSET_DIR, NOTIFY_FILENAME),  'w') as outfile:
        msg_str = json.dumps(msg_obj)
        outfile.write(msg_str)


class TestPing(unittest.TestCase):

    def test_up_and_still_up(self):
        print "test_up_and_still_up"
        clear_notify_cache()
        sctl = TestSystemControl(system_status=SystemControl.SYSTEM_UP)
        sm = ping_openchannel.process(URL, 0, False, sctl)
        self.assertTrue(sctl.is_system_up())
        self.assertFalse(sm.is_current_state_emailed)
        self.assertEqual("System status: up", sm.subject)
        self.assertEquals("", sm.get_message_content())
        self.assertFalse(is_notify_cache())

    def test_up_and_then_down_and_restarted(self):
        print "test_up_and_then_down_and_restarted"
        clear_notify_cache()
        sctl = TestSystemControl(system_status=SystemControl.SYSTEM_DOWN)
        sm = ping_openchannel.process(URL, 0, False, sctl)
        self.assertTrue(sctl.is_system_up())
        self.assertTrue(sm.is_current_state_emailed)
        self.assertEqual("System status: up", sm.subject)
        self.assertTrue("Localhost is not responding...attempting restart" in sm.get_message_content())
        self.assertTrue("Localhost has been successfully restarted" in sm.get_message_content())
        self.assertFalse(is_notify_cache())

    def test_up_and_then_down_and_no_restart(self):
        print "test_up_and_then_down_and_no_restart"
        clear_notify_cache()
        sctl = TestSystemControl(system_status=SystemControl.SYSTEM_DOWN, no_restart_on_bounce=True)
        sm = ping_openchannel.process(URL, 0, False, sctl)
        self.assertFalse(sctl.is_system_up())
        self.assertTrue(sm.is_current_state_emailed)
        self.assertEqual("System status: down", sm.subject)
        self.assertTrue("Localhost is not responding...attempting restart" in sm.get_message_content())
        self.assertTrue("Localhost could not be restarted" in sm.get_message_content())
        self.assertTrue(is_notify_cache())

    def test_down_then_back_up(self):
        print "test_down_then_back_up"
        replace_cache("test_could_not_be_restarted")
        sctl = TestSystemControl(system_status=SystemControl.SYSTEM_UP)
        sm = ping_openchannel.process(URL, 0, False, sctl)
        self.assertTrue(sctl.is_system_up())
        self.assertTrue(sm.is_current_state_emailed)
        self.assertEqual("System status: up", sm.subject)
        self.assertTrue("Localhost is back up" in sm.get_message_content())
        self.assertFalse(is_notify_cache())

    def test_down_then_back_up_begin_of_epoch(self):
        print "test_down_then_back_up_begin_of_epoch"
        replace_cache("test_could_not_be_restarted", NOTIFY_BEGIN_OF_EPOCH)
        sctl = TestSystemControl(system_status=SystemControl.SYSTEM_UP)
        sm = ping_openchannel.process(URL, 0, False, sctl)
        self.assertTrue(sctl.is_system_up())
        self.assertEqual("System status: up", sm.subject)
        self.assertTrue(sm.is_current_state_emailed)
        self.assertTrue("Localhost is back up" in sm.get_message_content())
        self.assertFalse(is_notify_cache())

    def test_down_then_back_up(self):
        print "test_down_then_back_up"
        replace_cache("test_could_not_be_restarted", NOTIFY_YESTERDAY)
        sctl = TestSystemControl(system_status=SystemControl.SYSTEM_UP)
        sm = ping_openchannel.process(URL, 0, False, sctl)
        self.assertTrue(sctl.is_system_up())
        self.assertTrue(sm.is_current_state_emailed)
        self.assertEqual("System status: up", sm.subject)
        self.assertTrue("Localhost is back up" in sm.get_message_content())
        self.assertFalse(is_notify_cache())

    def test_down_then_down_then_back_up(self):
        print "test_down_then_down_then_back_up"
        replace_cache("test_could_not_be_restarted", NOTIFY_TODAY)
        sctl = TestSystemControl(system_status=SystemControl.SYSTEM_DOWN)
        sm = ping_openchannel.process(URL, 0, False, sctl)
        self.assertTrue(sctl.is_system_up())
        self.assertTrue(sm.is_current_state_emailed)
        self.assertEqual("System status: up", sm.subject)
        self.assertTrue("Localhost is not responding...attempting restart" in sm.get_message_content())
        self.assertTrue("Localhost has been successfully restarted" in sm.get_message_content())
        self.assertFalse(is_notify_cache())

    def test_down_then_down_then_still_down(self):
        print "test_down_then_down_then_still_down"
        replace_cache("test_could_not_be_restarted", NOTIFY_TODAY)
        sctl = TestSystemControl(system_status=SystemControl.SYSTEM_DOWN, no_restart_on_bounce=True)
        sm = ping_openchannel.process(URL, 0, False, sctl)
        self.assertFalse(sctl.is_system_up())
        self.assertFalse(sm.is_current_state_emailed)
        self.assertEqual("System status: down", sm.subject)
        self.assertTrue("Localhost is not responding...attempting restart" in sm.get_message_content())
        self.assertTrue("Localhost could not be restarted" in sm.get_message_content())
        self.assertTrue(is_notify_cache())


if __name__ == '__main__':
    unittest.main()
