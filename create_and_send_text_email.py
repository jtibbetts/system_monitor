import os
import sys
import httplib2
import select

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

import config

def create_message(sender, to, subject, message_text):
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_string())}

def create_message_with_attachment(
    sender, to, subject, msgHtml, msgText, attachmentFile):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      msgHtml: Html message to be sent
      msgText: Alternative plain text message for older email clients
      attachmentFile: The path to the file to be attached.

    Returns:
      An object containing a base64url encoded email object.
    """
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

def get_credentials(config_path, scopes):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        config_path,
        scopes)
    return credentials

def send_message(service, user_id, message):
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print 'Message Id: %s' % message['id']
    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error

def set_up_email_and_send(admin_config_path, sender, to, subject, msg_text):
    credentials = get_credentials(admin_config_path, ['https://www.googleapis.com/auth/gmail.send'])

    delegated_credentials = credentials.create_delegated(sender)

    http = delegated_credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    message = create_message(sender, to, subject, msg_text)
    send_message(service, "me", message)


if __name__ == '__main__':

    try:
        import argparse

        argparser = argparse.ArgumentParser()
        argparser.add_argument("--input", help="input filename")
        argparser.add_argument("--output", help="optional output file")
        argparser.add_argument("sender", help="email FROM")
        argparser.add_argument("to", help="email TO")
        argparser.add_argument("subject", help="subject")
        args = argparser.parse_args()
    except ImportError:
        args = None

    msgText = ""
    if args.input != None:
        with open(args.input) as infile:
            msgText = infile.read()
    else:
        if select.select([sys.stdin, ], [], [], 0.0)[0]:
            msgText = sys.stdin.read()
        else:
            print "No data"
            sys.exit(2)

    set_up_email_and_send(config.ADMIN_CONFIG_PATH, args.sender, args.to, args.subject, msgText)

