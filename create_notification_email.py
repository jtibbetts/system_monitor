import os
import sys
import json
import httplib2
import select

from dateutil.parser import parse
from datetime import datetime

import config

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery
import mimetypes
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase

from apiclient import discovery

from oauth2client.service_account import ServiceAccountCredentials

CONFIG_DIR = os.path.expanduser('~/.credentials/OpenChannel/')
ADMIN_CONFIG_PATH = CONFIG_DIR + 'OpenChannel-SrvAcct.json';
SUBJECT = 'john.tibbetts@kinexis.com'

try:
    import argparse
    argparser = argparse.ArgumentParser()
    args = argparser.parse_args()
except ImportError:
    args = None

def get_credentials(config_path, scopes):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        config_path,
        scopes)

    return credentials

def create_message(sender, to, subject, message_text):
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_string())}

def create_message_with_attachment(
    sender, to, subject, msgHtml, msgText, attachmentFile):

    message = MIMEMultipart('mixed')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    messageA = MIMEMultipart('alternative')
    messageR = MIMEMultipart('related')

    messageR.attach(MIMEText(msgHtml, 'html'))
    messageA.attach(MIMEText(msgText, 'plain'))
    messageA.attach(messageR)

    message.attach(messageA)

    print "create_message_with_attachment: file:", attachmentFile
    content_type, encoding = mimetypes.guess_type(attachmentFile)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(attachmentFile, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(attachmentFile, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(attachmentFile, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(attachmentFile, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()
    filename = os.path.basename(attachmentFile)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_string())}

def send_message(service, user_id, message):
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print 'Message Id: %s' % message['id']
    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error

def send_google_email(sender, to, msg_obj):
    credentials = get_credentials(ADMIN_CONFIG_PATH, ['https://www.googleapis.com/auth/gmail.send'])

    delegated_credentials = credentials.create_delegated(SUBJECT)

    http = delegated_credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    sender = sender
    to = to
    subject = msg_obj['subject']
    msg_text = msg_obj['msg_text']

    message = create_message(sender, to, subject, msg_text)
    send_message(service, "me", message)

def start_of_day(ts):
    return datetime(ts.year, ts.month, ts.day)

def write_notification(msg_filename):
    msg_text = ""
    msg_filename = os.path.join(config.CLOSET_DIR, msg_filename)
    if not os.path.exists(msg_filename):
        sys.exit(0)

    with open(msg_filename) as infile:
        msg_json = infile.read()

    try:
        msg_obj = json.loads(msg_json)
    except Exception as exc:
        # bad or empty json file
        print "Invalid notificiation file...removing"
        os.remove(msg_filename)
        sys.exit(2)

    now = datetime.now()
    notified_at = parse(msg_obj['notified_at'])
    start_now = start_of_day(now)
    start_notified_at = start_of_day(notified_at)
    if start_notified_at < start_now:
        send_google_email(config.EMAIL_SENDER, config.EMAIL_TO, msg_obj)

        if msg_obj['system_status'] == 'down':
            # update notification stamp and write it back out
            print "system down: updating notification file"
            msg_obj['notified_at'] = now.isoformat()
            json_str = json.dumps(msg_obj)
            with open(msg_filename, 'w') as outfile:
                outfile.write(json_str)
        else:
            print "system up: removing notification file"
            os.remove(msg_filename)
    else:
        print "Recent notification made"

if __name__ == '__main__':
    from os import listdir
    from os.path import isfile, join
    closet_files = [f for f in listdir(config.CLOSET_DIR) if isfile(join(config.CLOSET_DIR, f))]

    for filename in closet_files:
        write_notification(filename)