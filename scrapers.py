import logging
import re
import requests
from bs4 import BeautifulSoup
import sys
import json
import urllib2
from decimal import *


class CarrierUsageScraper(object):
    """
    This class should only be inherited by another class.

    name = name of the carrier
    description = description of the carrier
    post_data = HTTP POST data that is passed to the url_login script. Dictionary format.
    http_headers = HTTP Header to use for the website scraping

    url_login = login script that handles the POST authentication and cookies
    url_data = web page that presents the data to parse (post-login)

    A _parse method is required to be created at the minimum

    """
    def __init__(self, name,
                 description,
                 post_data,
                 url_login,
                 url_data,
                 http_headers,
                 logger=None):
        self.logger = logger or logging.getLogger(__name__)

        self.name = name
        self.description = description
        self.post_data = post_data
        self.http_headers = http_headers

        self.url_login = url_login
        self.url_data = url_data
        self.s = None   # Session manager
        self._logged_in = False

        # scraped data
        self.data_unit = None

        # Propertied variables
        self._plan_title = None
        self._data_plan_total = None
        self._data_usage_total = None
        self._data_plan_days_left = None

        # Extended / In-detail stats
        self.extended_stats = True
        self._data_usage_down = None
        self._data_usage_up = None

    @property
    def plan_title(self):
        return self._plan_title

    @property
    def data_plan_total(self):
        return self._data_plan_total

    @property
    def data_plan_days_left(self):
        return self._data_plan_days_left

    @property
    def data_usage_total(self):
        return self._data_usage_total

    @property
    def data_usage_down(self):
        return self._data_usage_down

    @property
    def data_usage_up(self):
        return self._data_usage_up

    @property
    def data_usage_pct(self):
        # (used data - total plan data)/ total plan data
        pct = (self.data_plan_total - self.data_usage_total) / self.data_plan_total
        return 100-pct*100

    @plan_title.setter
    def plan_title(self, v):
        self._plan_title = v.strip()

    @data_plan_total.setter
    def data_plan_total(self, v):
        n_v = re.sub("[^0-9]", "", v)
        self._data_plan_total = Decimal(n_v)

    @data_plan_days_left.setter
    def data_plan_days_left(self, v):
        n_v = re.sub("[^0-9]", "", v)
        self._data_plan_days_left = Decimal(n_v)

    @data_usage_total.setter
    def data_usage_total(self, v):
        n_v = re.sub("[^0-9]", "", v)
        self._data_usage_total = Decimal(n_v)

    @data_usage_down.setter
    def data_usage_down(self, v):
        n_v = re.sub("[^0-9\.]", "", v)
        self._data_usage_down = Decimal(n_v)

    @data_usage_up.setter
    def data_usage_up(self, v):
        n_v = re.sub("[^0-9\.]", "", v)
        self._data_usage_up = Decimal(n_v)

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

        # Send page html to the parser
        page = self._get_data_pg_html()
        self._parse(page)

    def print_all(self):
        print "{} Plan: {}".format(self.name, self.plan_title)
        print "Usage: {}/{} {}".format(self.data_usage_total, self.data_plan_total, self.data_unit)
        print "Days left: {}".format(self.data_plan_days_left)
        print "Percent used: {}".format(self.data_usage_pct)

        if self.extended_stats:
            print "Download: {}".format(self.data_usage_down)
            print "Upload: {}".format(self.data_usage_up)


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
        try:
            self.plan_title = parse_page.find(class_="usage-plan-header usage-type-header").h2.string
            self.data_unit = parse_page.find(class_="usage-card-info").span.string.strip()[-2:]
            self.data_usage_total = parse_page.find(class_="used").string
            self.data_plan_total = parse_page.find(class_="usage-card-info").span.string.strip()[1:-2].strip()
            self.data_plan_days_left = parse_page.find(class_="meters-bill-cycle").p.strong.string

            # Get json data
            json_url = "https://www.telus.com" + parse_page.find(class_="usage-bar-chart mobile-chart").find(class_="item visually-hidden")["data-url"]

            if len(json_url) > len("https://www.telus.com") and self._logged_in:
                self.extended_stats = True
                r = self.s.get(json_url, headers=self.http_headers)
                self.json_data = json.loads(r.text.encode("utf8"))

                self.data_usage_down = self.json_data['meters'][0]["used_download"] # used upload
                self.data_usage_up = self.json_data['meters'][0]["used_upload"] # used upload

        except Exception as e:
            logging.error("Failed to parse Telus Wireline Scraper")
            sys.exit("Unable to parse: {}".format(e.message))


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

        post_data = { "goto": "https://identity.koodomobile.com:443/as/QVVKn/resume/as/authorization.ping",
                    "encoded": "false",
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
        try:
            self.plan_title = parse_page.find(class_="usage-plan-header usage-type-header").h2.string
            self.data_unit = parse_page.find(class_="usage-card-info").span.string.strip()[-2:]
            self.data_usage_total = parse_page.find(class_="used").string
            self.data_plan_total = parse_page.find(class_="usage-card-info").span.string.strip()[1:-2].strip()
            self.data_plan_days_left = parse_page.find(class_="records-header-info").strong.string

        except Exception as e:
            logging.error("Failed to parse Koodo Mobile Scraper")
            sys.exit("Unable to parse: {}".format(e.message))