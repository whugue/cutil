import os
import time
import json
import urllib
import hashlib
import logging
import requests
import traceback
from bs4 import BeautifulSoup
from datetime import datetime


class CustomUtils:

    def __init__(self):
        # For cprint()
        self._prev_cstr = ''

    ####
    # Terminal/display related functions
    ####
    def cprint(self, cstr):
        """
        Clear line, then reprint on same line
        :param cstr: string to print on current line
        """
        cstr = str(cstr)  # Force it to be a string
        cstr_len = len(cstr)
        prev_cstr_len = len(self._prev_cstr)
        num_spaces = 0
        if cstr_len < prev_cstr_len:
            num_spaces = abs(prev_cstr_len - cstr_len)
        try:
            print(cstr + " "*num_spaces, end='\r')
            self._prev_cstr = cstr
        except UnicodeEncodeError:
            print('Processing...', end='\r')
            self._prev_cstr = 'Processing...'

    ####
    # Time related functions
    ####
    def get_utc_epoch(self):
        """
        :return: utc time as epoch
        """
        return int(time.time())

    ####
    # Other functions
    ####
    def get_default_header(self):
        default_header = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        return default_header

    def sanitize(self, string):
        """
        Catch and replace invalid path chars
        [replace, with]
        """
        replace_chars = [
            ['\\', '-'], [':', '-'], ['/', '-'],
            ['?', ''], ['<', ''], ['>', ''],
            ['`', '`'], ['|', '-'], ['*', '`'],
            ['"', '\''], ['.', ''], ['&', 'and']
        ]
        for ch in replace_chars:
            string = string.replace(ch[0], ch[1])
        return string

    def rreplace(self, s, old, new, occurrence):
        """
        Taken from: http://stackoverflow.com/questions/2556108/how-to-replace-the-last-occurence-of-an-expression-in-a-string
        """
        li = s.rsplit(old, occurrence)
        return new.join(li)

    ####
    # File/filesystem related function
    ####
    def get_file_ext(self, url):
        file_name, file_extension = os.path.splitext(url)
        return file_extension

    def norm_path(self, path):
        """
        :return: Proper path for os
        """
        # path = os.path.normcase(path)
        path = os.path.normpath(path)
        return path

    def create_path(self, path, is_dir=False):
        """
        Check if path exists, if not create it
        :param path: path or file to create directory for
        :param is_dir: pass True if we are passing in a directory, default = False
        :return: os safe path from `path`
        """
        path = self.norm_path(path)
        path_check = path
        if not is_dir:
            path_check = os.path.dirname(path)

        does_path_exists = os.path.exists(path_check)

        if does_path_exists:
            return path

        try:
            os.makedirs(path_check)
        except OSError:
            pass

        return path

    def save_props(self, data):
        self.create_path(data['save_path'])
        with open(data['save_path'] + ".json", 'w') as outfile:
            json.dump(data, outfile, sort_keys=True, indent=4)

    def download(self, url, file_path, header={}):
        self.create_path(file_path)

        try:
            with urllib.request.urlopen(
              urllib.request.Request(url, headers=header)) as response, \
                open(file_path, 'wb') as out_file:
                    data = response.read()
                    out_file.write(data)

            return_value = file_path

        except urllib.error.HTTPError as e:
            return_value = False
            # self.log("Error [download]: " + str(e.code) + " " + url, level='error')
        except Exception as e:
            return_value = False
            # self.log("Exception [download]: " + str(e) + " " + url, level='error')

        return return_value

    ####
    # BeautifulSoup Related functions
    ####
    def get_site(self, url, header={}, is_json=False):
        """
        Try and return soup or json content, if not throw a RequestsError
        """
        if not url.startswith('http'):
            url = "http://" + url
        try:
            response = requests.get(url, headers=header)
            if response.status_code == requests.codes.ok:
                if is_json:
                    data = response.json()
                else:
                    data = BeautifulSoup(response.text, "html5lib")

                return data 
                
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # self.log("HTTPError [get_site]: " + str(e.response.status_code) + " " + url, level='error')
            raise RequestsError(str(e))
        except requests.exceptions.ConnectionError as e:
            # self.log("ConnectionError [get_site]: " + str(e) + " " + url, level='error')
            raise RequestsError(str(e))
        except requests.exceptions.TooManyRedirects as e:
            # self.log("TooManyRedirects [get_site]: " + str(e) + " " + url, level='error')
            raise RequestsError(str(e))
        except Exception as e:
            # self.log("Exception [get_site]: " + str(e) + " " + url + "\n" + str(traceback.format_exc()), level='critical')
            raise RequestsError(str(e))