#!/usr/bin/env python2

import sys
import logging
import argparse 
import getpass
import requests # Handling HTTP Requests and cookies
from bs4 import BeautifulSoup

__version__ = "0.1-HEAD"
__author__ = "Andrew Klaus"
__author_email__ = "andrewklaus@gmail.com"
__copyright__ = "2015"


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("main")

    parser = argparse.ArgumentParser()

    carriers = ("telus_wireline","koodo_mobile")
    #items = ("usage","allotment","plan","days_left","all")
    #output = ("zabbix","terminal")

    parser.add_argument("username", help="Username for account access")
    parser.add_argument("-p", "--password", default=None, \
                        help="Password for account access (Optional: will prompt if required)")
    parser.add_argument("-c", "--carrier", default='telus_wireline',\
                        help='Carrier to query from (default=telus_wireline)', choices=carriers)
#    parser.add_argument("-i", "--item", default='usage', help='Item to request (default=usage)', choices=items)
#    parser.add_argument("-t", "--cache_time", default=0, type=int, help='Seconds to keep data cached (default=0)')
    parser.add_argument("-a", "--http_user_agent", default="Mozilla/5.0 (X11; Linux x86_64)")
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
#    parser.add_argument("-o", "--output", default='terminal', help='Type of output (default=terminal)', choices=output)
    args = parser.parse_args()

    if args.verbose > 0:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    # Get password if none was specified
    if args.password is None:
        password = getpass.getpass(prompt='Carrier password (will not echo): ')
        logger.debug("Password length: {}".format(len(password)))
    else:
        password = args.password

    if len(password) < 1:
        logger.debug("Password is less than 1")
        sys.exit("Password empty. Exiting.")

    if args.carrier == "telus_wireline":
        logger.debug("Using telus_wireline carrier")
        scraper = TelusWirelineScraper(args.username, password, args.http_user_agent)
    elif args.carrier == "koodo_mobile":
        logger.debug("Using koodo_mobile carrier")
        scraper = KoodoMobileScraper(args.username, password, args.http_user_agent)
    else:
        sys.exit("Invalid carrier {} specified".format(args.carrier))

    logger.debug("Starting scraping process")
    scraper.go()
    logger.debug("Finished scraping process")

    scraper.print_all()


class CarrierUsageScraper(object):
    """
    This class should only be inherited by another class.

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

        self._data_usage = None
        self._plan = None
        self._data_usage_unit = None
        self._data_plan_total = None

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
        return self._data_usage

    def get_plan(self):
        return self._plan

    def _get_data_pg_html(self):
        # Returns HTML for data page
        if self._logged_in is not True:
            raise Exception("Not logged in")
        else:
            r = self.s.get(self.url_data, headers=self.http_headers)
            page = BeautifulSoup(r.text.encode("utf8"), "lxml")

        return page
 
    def _parse(self, parse_page):
        pass

    def go(self):
        self._login()
        page = self._get_data_pg_html()
        self._parse(page)

    def print_all(self):
        print "{} Plan: {}".format(self.name, self._plan)
        print "Usage: {}/{} {}".format(self._data_usage, self._data_plan_total, self._data_usage_unit)


class TelusWirelineScraper(CarrierUsageScraper):
    """

    Other meaningful data that can be pulled:
    Billing cycle
    Days left in cycle

    """
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

    def _parse(self, parse_page):
        usage = parse_page.find(class_="used").string
        plan = parse_page.find(class_="usage-plan-header usage-type-header").h2.string
        self._data_usage = usage.strip()
        self._plan = plan.strip()
        self._data_usage_unit = parse_page.find(class_="usage-card-info").span.string.strip()[-2:]
        self._data_plan_total = parse_page.find(class_="usage-card-info").span.string.strip()[1:-2].strip()

class KoodoMobileScraper(CarrierUsageScraper):
    """

    Other meaningful data that could be pulled:
    Messaging usage
    Airtime usage
    Billing Cycle
    Days left in cycle

    """
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

    def _parse(self, parse_page):
        usage = parse_page.find(class_="used").string
        plan = parse_page.find(class_="usage-plan-header usage-type-header").h2.string
        self._data_usage = usage.strip()
        self._plan = plan.strip()
        self._data_usage_unit = parse_page.find(class_="usage-card-info").span.string.strip()[-2:]
        self._data_plan_total = parse_page.find(class_="usage-card-info").span.string.strip()[1:-2].strip()

if __name__ == "__main__":
    sys.exit(main())

