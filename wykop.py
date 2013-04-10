#!/usr/bin/env python
# coding: utf-8

import cookielib
import urllib2
import urllib
import re
import simplejson
from time import sleep
import random

__version__ = "0.1"
__license__ = "BSD"
__author__ = "Adrian Cendrowski"
__author_email__ = "zs@ztbsauer.com"

VERSION = "%prog v" + __version__
AGENT = "%s/%s" % (__name__, __version__)

VOTEDFILE = '/tmp/wykop_voted_links.txt'
COOKIEFILE = '/tmp/wykop.cookie'
USERNAME = ''
PASSWORD = ''


class Wykop(object):

  def __init__(self):
		self.url = "http://wykop.pl"
		self.data = None
		self.headers =  {'User-agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19'}
		self.html_doc = ""


	def parse_url(self):

		urlopen = urllib2.urlopen
		cj = cookielib.LWPCookieJar()
		Request = urllib2.Request

		try:
			cj.load(COOKIEFILE)
		except IOError, e:
			print 'We failed to open cookie. Creating one'
			cj.save(COOKIEFILE)
			cj.load(COOKIEFILE)

		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		urllib2.install_opener(opener)

		try:
			req = Request(self.url, self.data, self.headers)
			handle = urlopen(req)
		except IOError, e:
			print 'We failed to open "%s".' % self.url
			if hasattr(e, 'code'):
				print 'We failed with error code - %s.' % e.code
		else:
			self.html_doc = handle.read()

		try:
			self._logged = re.findall('var logged = (\S+)\;', self.html_doc)[0]
			self._token = re.findall('var token = \'(\S+)\'', self.html_doc)[0]
			self._hash = re.findall('var hash = \'(\S+)\'', self.html_doc)[0]
			self._ajaxhash = re.findall('var ajaxhash = \'(\S+)\'', self.html_doc)[0]

			if(self._logged =='false'):
				self.__token = re.findall('name="__token" value="(\S[^\"]+)"', self.html_doc)[0]
			else:
				self.__token = ""
				cj.save(COOKIEFILE)

		except IndexError:
			return


	def check_if_logged(self):

		self.url = "https://www.wykop.pl/zaloguj/"
		self.parse_url()

		if(self._logged=='false'):
			print "Not logged in"
			print "Trying to login"

			values = {
				'user[username]' : USERNAME,
				'user[password]' : PASSWORD,
				'__token' : self.__token
			}

			self.data = urllib.urlencode( values )

			self.url = "https://www.wykop.pl/zaloguj/"
			self.parse_url()

			print "Successfully logged in" if (self._logged=='true') else "Login failed"
		else:
			print "Logged in"

	def vote_link(self, linkid):
		print "Digging link %s" % linkid
		self.url = "http://www.wykop.pl/ajax/link/vote/link/%s/hash/%s" % (linkid , self._hash);
		self.data = None
		self.parse_url()

	def bury_link(self, linkid, t=5):
		print "Burying link %s" % linkid
		self.url = "http://www.wykop.pl/ajax/link/bury/type,%s,link,%s,hash,%s" % (t, linkid, self._hash)
		self.data = None
		self.parse_url()

	def wpisik(self):
		print "Wpisikuje"
		self.url = "http://www.wykop.pl/wpis/dodaj/%7E1/1/log_ref_0,stream,log_ref_m_0,index,log_ref_n_0,"
		values = {
			'entry[body]' : 'Nabijam wpisy #nabijamwpisy',
			'__token' : self._token
		}

		self.data = urllib.urlencode( values )	
		self.parse_url()

	def parse_links(self):
		print "Parsing links"
		self.url = "http://www.wykop.pl/wykopalisko/aktywne/"
		self.data = None
		self.parse_url()

		links = re.findall('\<p class=\"lheight18\"\>(.*)\<\/p\>', self.html_doc)

		try:
			voted_links = open(VOTEDFILE).read()
			voted_links = simplejson.loads(voted_links)
		except IOError, e:
			voted_links = []

		for x in range(0,len(links)):
			link = links[x]

			link_url = re.findall('\<a href=\"(.*)\" ', link)[0]
			link_description = re.findall('\<span class=\"c22\"\>(.*)\<\/span\>', link)[0]

			try:
				link_id = re.findall('http:\/\/www.wykop.pl\/link\/([0-9]+)\/', link_url)[0]
			except IndexError:
				link_id = 0

			if(link_id and link_description.find(" się ")>=0):

				if(link_id not in voted_links):
					voted_links.append( link_id )

					self.url = link_url
					self.data = None
					self.parse_url()

					_time = random.randrange(25,255,1)
					print "Found article about: %s" % link_description
					print "Going reading, will be back in %s seconds" % _time;

					sleep(_time)
					self.vote_link(link_id)


		f = open(VOTEDFILE, 'w')
		simplejson.dump(voted_links, f)
		f.close()


def main():

	w = Wykop()
	w.check_if_logged()
	w.parse_links()


if __name__ == "__main__":
    main()
