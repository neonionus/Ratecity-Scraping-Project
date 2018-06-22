import scrapy
from scrapy import signals
from pydispatch import dispatcher
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from collections import OrderedDict
from copy import deepcopy
import re
import codecs
import selenium
from selenium import webdriver

#Usage: "scrapy crawl infochoice"
#Crawls all comapany pages in URLS.txt, finds attached home loan product pages
#and takes all data from them. Then puts data into csv file. 

##################################################################

def getURLS(filename):
    f = open(filename, "r")
    return [i.strip("\n") for i in f.readlines()]

class infochoice(scrapy.Spider):
    name = "infochoice2"
    #start_urls = getURLS("URLS.txt")
    
    #test sample links so testing doesn't take forever
    start_urls = ['https://www.infochoice.com.au/institutions/adelaidebank/98',
               'https://www.infochoice.com.au/institutions/westpac/19',
                'https://www.infochoice.com.au/institutions/amo/384',
                'https://www.infochoice.com.au/institutions/emoney/807',
                'https://www.infochoice.com.au/institutions/firstoptioncreditunion/760']

    def parse(self,response):
        print("SDFSEDFSDFSDFSDFSDFSDF")
        print("######################################")