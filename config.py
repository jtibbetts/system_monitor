import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CLOSET_DIR = os.path.abspath(os.path.join(PROJECT_DIR, "../closet"))

ROOT_DIR=os.path.expanduser('~')
CREDENTIALS_DIR = os.path.abspath(os.path.join(ROOT_DIR, ".credentials/OpenChannel/"))

ADMIN_CONFIG_PATH = os.path.join(CREDENTIALS_DIR, 'OpenChannel-SrvAcct.json')

EMAIL_SENDER = 'john.tibbetts@kinexis.com'
EMAIL_TO = 'john.tibbetts@kinexis.com'      # can be comma-separated recipients


