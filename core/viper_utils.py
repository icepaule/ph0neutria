#!/usr/bin/python3

from .config_utils import get_base_config
from .geo_utils import resolve_asn, resolve_country
from .log_utils import get_module_logger
from requests_toolbelt.multipart.encoder import MultipartEncoder
from urllib.parse import urljoin, urlparse


import json
import os
import requests
import sys
import time
import re


CDIR = os.path.dirname(os.path.realpath(__file__))
ROOTDIR = os.path.abspath(os.path.join(CDIR, os.pardir))
BASECONFIG = get_base_config(ROOTDIR)
LOGGING = get_module_logger(__name__)


def upload_to_viper(mal_url, file_path, mal_class='Malware.Generic'):
    try:
        file_name = urlparse(mal_url.url).path.strip('/')

        sample_data = {'tag_list': make_tags(mal_url, mal_class), 'note_title': 'Sample Source', 'note_body': make_note(mal_url), 'file_name': file_name}

        auth_header = {'Authorization': BASECONFIG.viper_token}

        LOGGING.info('Adding to Viper: {0}'.format(file_name))

        with open(file_path, 'rb') as raw_file:
            response = requests.post(BASECONFIG.viper_add_url, headers=auth_header, files={'file': raw_file}, data=sample_data)

            if response.status_code == 201:
                responsejson = json.loads(response.content.decode('utf-8'))

                LOGGING.info('Submitted file to Viper. Sample URL: {0}'.format(responsejson[0]['url']))

                return True

            elif response.status_code == 400:
                LOGGING.info('File already exists in Viper.')

            else:
                LOGGING.error('Problem submitting file {0} to Viper. Status code: {1}. Continuing.'.format(file_name, response.status_code))

    except requests.exceptions.ConnectionError as e:
        LOGGING.error('Problem connecting to Viper. Error: {0}'.format(e))

    except Exception as e:
        LOGGING.error('Problem connecting to Viper. Aborting task.')
        LOGGING.exception(sys.exc_info())
        LOGGING.exception(type(e))
        LOGGING.exception(e.args)
        LOGGING.exception(e)

    return False


def make_tags(mal_url, mal_class):
    tags = ''

    tags += normaltag(time.strftime(BASECONFIG.date_format))
    tags += ','
    tags += normaltag(urlparse(mal_url.url).hostname)
    tags += ','
    tags += normaltag(resolve_asn(mal_url.address))
    tags += ','
    tags += normaltag(resolve_country(mal_url.address))
  
    if BASECONFIG.tag_samples:
        tags += ','
        tags += normaltag(mal_class)

    LOGGING.debug('tags={0}'.format(tags))

    return tags


def normaltag( str ):
    str = re.sub('[^a-z0-9A-Z\ \-\_\.]+','', str)
    str = re.sub('[\ ]+','_', str)
    str = str.lower()
    return str;


def make_note(mal_url):
    note = '{0} ({1}) via {2}'.format(
        mal_url.url,
        mal_url.address,
        mal_url.source)

    LOGGING.debug('note={0}'.format(note))

    return note
