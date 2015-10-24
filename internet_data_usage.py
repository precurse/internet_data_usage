#!/usr/bin/env python2

import sys
import argparse 
import getpass
import requests # Handling HTTP Requests and cookies
from bs4 import BeautifulSoup

__version__ = "0.1"
__author__ = 'Andrew Klaus'
__author_email__ = 'andrewklaus@gmail.com'
__copyright__ = '2015'


def main():
    parser = argparse.ArgumentParser()

    carriers = ('telus_wireline','koodo_mobile')
    items = ('usage','allotment','plan','days_left','all')
    output = ('zabbix','terminal')

    parser.add_argument('username', help='Username for account access')
    parser.add_argument('-p', '--password', default=None, help='Password for account access (Optional: will prompt if required)')
    parser.add_argument('-c', '--carrier', default='telus', help='Carrier to query from (default=telus)', choices=carriers)
    parser.add_argument('-i', '--item', default='usage', help='Item to request (default=usage)', choices=items)
    parser.add_argument('-o', '--output', default='terminal', help='Type of output (default=terminal)', choices=output)
    parser.add_argument('-t', '--cache_time', default=0, help='Seconds to keep cached items (default=0)')

    args = parser.parse_args()

    if args.password is None:
        password = getpass.getpass(prompt='Carrier password (will not echo): ')
    else:
        password = args.password

    headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64)' }
    login_post = "https://www.telus.com/sso/UI/Login?realm=telus&service=telus&locale=en"
    data_pg = "https://www.telus.com/my-account/usage/overview/usage?INTCMP=USSLeftNavLnkUsage"

    data = { "goto": "https://www.telus.com/my-account/usage/overview/usage?INTCMP=USSLeftNavLnkUsage",
        "encoded": "false",
        "service": "telus",
        "realm": "telus",
        "portal": "telus",
        "userLanguage": "en",
        "IDToken1": args.username,
        "IDToken2": password,
        "remember-me-checkbox[]" : ""}

    scraper = TelusScraper("Telus","Telus",data,login_post, data_pg, headers)

    scraper.go()

    print scraper.get_data_usage()

    #s = requests.session()
    #s.post(login_post, data, headers=headers)

    #r = s.get(data_pg, headers=headers)

    #print r.text.encode("utf8")

    #page = BeautifulSoup(r.text.encode("utf8"))

    #usage = page.find(class_="used")
    #cycle = page.find(class_="meters-bill-cycle")
    #plan = page.find(class_="usage-plan-header usage-type-header")

    #print usage.string.strip()

class CarrierUsageScraper(object):
    """
    name = name of the carrier
    description = description of the carrier
    post_data = HTTP POST data that is passed to the url_login script. Dictionary format.
    http_header = HTTP Header to use for the website scraping

    url_login = login script that handles the POST authentication and cookies
    url_data = web page that presents the data to parse (post-login)

    """
    def __init__(self, name, description, post_data, url_login, url_data, http_headers):
        self.name = name
        self.description = description
        self.post_data = post_data 
        self.http_headers = http_headers
        
        self.url_login = url_login
        self.url_data = url_data

        self._usage = None

    def _login(self):
        # Create web session

        try:
            self.s = requests.session()
            self.s.post(self.url_login, self.post_data, headers=self.http_headers)
        except Exception as e:
            # Login failed
            self.login_failed = 1

        self._logged_in = True

    def get_data_usage(self):
        return self._usage

    def _get_data_pg_html(self):
        # Returns HTML for data page
        if self._logged_in is not True:
            raise Exception("Not logged in")
        else:
            r = self.s.get(self.url_data, headers=self.http_headers)
            page = BeautifulSoup(r.text.encode("utf8"), "lxml")

        return page
 
    def parse(self, parse_page):
        pass

    def go(self):
        self._login()
        page = self._get_data_pg_html()
        self.parse(page)


class TelusScraper(CarrierUsageScraper):
    def parse(self, parse_page):
        usage = parse_page.find(class_="used")
        self._usage = usage.string.strip()
 
if __name__ == "__main__":
    sys.exit(main())

