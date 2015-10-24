#!/usr/bin/env python2

import sys
import argparse 
import getpass
import requests # Handling HTTP Requests and cookies
from bs4 import BeautifulSoup

__version__ = "0.1-HEAD"
__author__ = "Andrew Klaus"
__author_email__ = "andrewklaus@gmail.com"
__copyright__ = "2015"


def main():
    parser = argparse.ArgumentParser()

    carriers = ("telus_wireline","koodo_mobile")
    #items = ("usage","allotment","plan","days_left","all")
    #output = ("zabbix","terminal")

    parser.add_argument("username", help="Username for account access")
    parser.add_argument("-p", "--password", default=None, help="Password for account access (Optional: will prompt if required)")
    parser.add_argument("-c", "--carrier", default='telus_wireline', help='Carrier to query from (default=telus)', choices=carriers)
#    parser.add_argument("-i", "--item", default='usage', help='Item to request (default=usage)', choices=items)
#    parser.add_argument("-t", "--cache_time", default=0, type=int, help='Seconds to keep data cached (default=0)')
    parser.add_argument("-a", "--http_user_agent", default="Mozilla/5.0 (X11; Linux x86_64)")
#    parser.add_argument("-o", "--output", default='terminal', help='Type of output (default=terminal)', choices=output)
    args = parser.parse_args()

    # Get password if none was specified
    if args.password is None:
        password = getpass.getpass(prompt='Carrier password (will not echo): ')
    else:
        password = args.password

    if args.carrier == "telus_wireline":
        scraper = TelusWirelineScraper(args.username, password, args.http_user_agent)
    elif args.carrier == "koodo_mobile":
        scraper = KoodoMobileScraper(args.username, password, args.http_user_agent)
    else:
        sys.exit("Invalid carrier specified")

    scraper.go()

    print scraper.get_data_usage()


class CarrierUsageScraper(object):
    """
    name = name of the carrier
    description = description of the carrier
    post_data = HTTP POST data that is passed to the url_login script. Dictionary format.
    http_headers = HTTP Header to use for the website scraping

    url_login = login script that handles the POST authentication and cookies
    url_data = web page that presents the data to parse (post-login)

    """
    def __init__(self, name,
                 description,
                 post_data,
                 url_login,
                 url_data,
                 http_headers):
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


class TelusWirelineScraper(CarrierUsageScraper):

    def __init__(self, username, password, user_agent):
        name = "TelusWireline"
        description = "Telus Wireline Services (Internet + TTV)"
        url_login = "https://www.telus.com/sso/UI/Login?realm=telus&service=telus&locale=en"
        url_data = "https://www.telus.com/my-account/usage/overview/usage?INTCMP=USSLeftNavLnkUsage"

        post_data = { "goto": "https://www.telus.com/my-account/usage/overview/usage?INTCMP=USSLeftNavLnkUsage",
        "encoded": "false",
        "service": "telus",
        "realm": "telus",
        "portal": "telus",
        "userLanguage": "en",
        "IDToken1": username,
        "IDToken2": password,
        "remember-me-checkbox[]" : ""}

        http_headers = {'user-agent': user_agent }

        CarrierUsageScraper.__init__(self, name, description, post_data, url_login, url_data, http_headers)

    def parse(self, parse_page):
        usage = parse_page.find(class_="used")
        self._usage = usage.string.strip()


class KoodoMobileScraper(CarrierUsageScraper):

    def __init__(self, username, password, user_agent):
        name = "KoodoMobile"
        description = "Koodo Wireless Services"
        url_login = "https://secure.koodomobile.com/sso/UI/Login?realm=koodo"
        url_data = "https://selfserveaccount.koodomobile.com/my-account/usage/overview/usage?INTCMP=KMNew_NavBar_Usage"

        post_data = { "goto": "aHR0cHM6Ly9pZGVudGl0eS5rb29kb21vYmlsZS5jb206NDQzL2FzL1FWVktuL3Jlc3VtZS9hcy9hdXRob3JpemF0aW9uLnBpbmc=",
        "encoded": "true",
        "service": "koodo",
        "realm": "koodo",
        "portal": "koodo",
        "locale": "en",
        "IDToken1": username,
        "IDToken2": password,
        "check1": "on",
        "Login.Submit": "Log in"}

        http_headers = {'user-agent': user_agent }

        CarrierUsageScraper.__init__(self, name, description, post_data, url_login, url_data, http_headers)

    def parse(self, parse_page):
        usage = parse_page.find(class_="used")
        self._usage = usage.string.strip()


if __name__ == "__main__":
    sys.exit(main())

