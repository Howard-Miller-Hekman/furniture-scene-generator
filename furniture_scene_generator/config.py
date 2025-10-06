'''
Furniture scene generator configuration
'''

import os
from furniture_scene_generator import version

import os

PROJECT_ROOT = os.path.dirname(__file__)

PROJECT_VERSION = version.__version__

PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
LOCATION = os.getenv('GOOGLE_LOCATION', 'us-central1')
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
EXCEL_INPUT_PATH = os.getenv('EXCEL_INPUT_PATH', './Overstock White Label Project 093025.xlsx')
EXCEL_OUTPUT_PATH = os.getenv('EXCEL_OUTPUT_PATH', './output/Overstock White Label Project 093025_updated.xlsx')

SFTP_HOST = os.getenv('SFTP_HOST')
SFTP_PORT = int(os.getenv('SFTP_PORT', 22))
SFTP_USERNAME = os.getenv('SFTP_USERNAME')
SFTP_PASSWORD = os.getenv('SFTP_PASSWORD')
SFTP_REMOTE_PATH = os.getenv('SFTP_REMOTE_PATH')
SFTP_BASE_URL = os.getenv('SFTP_BASE_URL')
