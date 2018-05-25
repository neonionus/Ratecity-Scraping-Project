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
from selenium.webdriver.common.keys import Keys
from scrapy.http.request import Request
from selenium.webdriver.chrome.options import Options
import time

#Usage: "scrapy crawl infochoice"
#Crawls all comapany pages in URLS.txt, finds attached home loan product pages
#and takes all data from them. Then puts data into csv file. 

##################################################################

def getURLS(filename):
    f = open(filename, "r")
    return [i.strip("\n") for i in f.readlines()]

class infochoice(scrapy.Spider):
    name = "infochoice"
    start_urls = getURLS("URLS.txt")
    
    #test sample links so testing doesn't take forever
    '''
    start_urls = [
                #'https://www.infochoice.com.au/institutions/aussie/101',
                #'https://www.infochoice.com.au/institutions/adelaidebank/98',
                #'https://www.infochoice.com.au/institutions/westpac/19',
                #'https://www.infochoice.com.au/institutions/amo/384',
                #'https://www.infochoice.com.au/institutions/emoney/807',
                #'https://www.infochoice.com.au/institutions/firstoptioncreditunion/760'
                #"https://www.infochoice.com.au/institutions/anz/78"
                "https://www.infochoice.com.au/institutions/easystreetfinancialservices/292"
                ]
    '''
    allowed_domains=["infochoice.com.au"]

    def __init__(self, *a, **kw):
        print("derp")
        super(infochoice, self).__init__(*a, **kw)
        self._data = []
        self._headers = set()
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome("C:\phantomjs-2.1.1-windows\chromedriver.exe",chrome_options=options)
        #time.sleep(3)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    #writes data to csv when spider is finished    
    def spider_closed(self, spider):
        self.driver.quit()       
        #will raise PemissionError if csv file is open
        with codecs.open("infochoice.csv", "w+", "utf-8-sig") as f:
            headings = list()

            #get all headings (some are unique)
            for row in self._data:
                for key in list(row.keys()):
                    if key not in headings:
                        headings.append(key)
            
            #write headings
            f.write(",".join(headings)+"\n")

            #write data from self._data
            for row in self._data:
                for heading in headings:
                    try:
                        f.write(str(row[heading]).replace(",",""))
                        #print(row)
                    except KeyError:
                        pass
                    f.write(",")
                f.write("\n")
            f.close()

    #process text on pages
    def parse(self, response):
        if 'institution' in response.url:
            print("derp")
            self.driver.get(response.url)
            time.sleep(1)
            sel = scrapy.Selector(text=self.driver.page_source)
            #print(self.driver.page_source)
            #print(sel.xpath('//a[@class="reportProductLink"]/@href').extract())
            for a in sel.xpath('//a[@class="reportProductLink"]/@href').extract():
                if 'home-loans' in a:
                    #print(a)
                    yield(scrapy.Request('https://www.infochoice.com.au'+a,callback=self.parse_item))


    def parse_item(self, response):
        print("asdfasdfasdfsad")
        url = response.url
        self.driver.get(response.url)
        time.sleep(1)
        response = scrapy.Selector(text=self.driver.page_source)


        #checks if product page is Variable or Fixed as they have different rate formats
        if response.xpath('//th'):
            homeLoanType = "FIXED"
        else:
            #response.xpath('//div[@class="variableRatePanel"]'):
            homeLoanType = "VARIABLE"
        #else: homeLoanType = "ERROR"
        #print(homeLoanType)

        #initialise stuff
        #tableRow starts at 1 because 0th row is the titles
        tableRow = 1
        realFixMonth = 0
        rate = 0
        compRate = 0
        revertRate = 0
        introRate = 0

        #Pulls rates from page
        if homeLoanType == "FIXED":
            fixNode = response.xpath('//div[@class="loan-categories-right"]//table[@class="product-inner-table"]/tbody/tr')
            print(len(fixNode))
        else:
            #pull variable rates
            percentNode = response.xpath('//div[@class="col-md-6 col-sm-6 col-lg-6 bigtext-con push-bottom-20"]/text()').extract()
            percentNode = [x.strip() for x in percentNode]
            #print(percentNode)
            #if intro rate
            if len(percentNode) > 8:
                introRate = percentNode[2]
                rate = percentNode[5]
                compRate = percentNode[8]
            #if no intro rate, also handles equity rates
            else:
                rate = percentNode[2]
                compRate = ""
                if len(percentNode) > 4:
                    compRate = percentNode[5] 

        while True: 
            search = re.search('.*-([0-9]+)$',url)
            code = str(search.group(1))

            if homeLoanType == "FIXED":
                #loops through and pulls fixed rates, allocating each its own row
                t = fixNode[tableRow].xpath('td/text()').extract()
                realFixMonth = t[0].strip()
                rate = t[1].strip()
                compRate = t[2].strip()
                tableRow+=1
                

                revertNode = response.xpath('//div[@class="col-md-6 col-sm-6 col-lg-6 bigtext-con push-bottom-20"]/text()').extract()

                if revertNode:
                    if len(revertNode) > 8:
                        revertRate = revertNode[8].strip()
                    #if no intro rate, also handles equity rates
                    else:
                        revertRate = revertNode[2].strip()


                #if the page has stupid revert and intro rate format
                if response.xpath('//div[@class="onGoingRatePanel"]'):
                    revertNode = response.xpath('//div[@class="onGoingRatePanel"]/div[@class="interestRate"]/text()').extract()
                    revertNode = [x.strip().split(' ',1)[0].strip() for x in revertNode]
                    revertRate = percentNode[0].replace("%","")
                #just revert rate
                elif response.xpath('//div[@class="variableRatePanel"]'):
                    revertNode = response.xpath('//div[@class="interestRate"]/span/text()').extract()
                    revertNode = [x.strip().split(' ',1)[0].strip() for x in revertNode]
                    revertRate = revertNode[0].replace("%","")

            #regex match names
            product = response.xpath('//meta[@name="description"]/@content').re(r'\sdoes\s(.+)\sfrom\s')[0]
            company = response.xpath('//meta[@name="description"]/@content').re(r'\sfrom\s(.+)\scompare')[0]
            code = str(code)+str(realFixMonth).split()[0]

            #setup basic data gathered so far
            output = OrderedDict({
                "Company":company, 
                "Product":product, 
                "url":url,
                "Home Loan Type":homeLoanType,
                "Rate": rate,
                "CodeID": code,
                "Comparison Rate":compRate,
                "Fixed Months":realFixMonth,
                "Revert Rate":revertRate,
                "Introductory Rate":introRate
                })

            #print(output)

            #loops through and gathers other information
            labels = []
            details = []
            search = []
            search.extend(response.xpath('//div[@class=" plain-container product-loan-details"]/div[@class="tow-col-label-con"]/div[@class="row"]/div[position()=2]'))
            search.extend(response.xpath('//div[@class=" plain-container product-loan-details"]/div[@class="plain-container"]/div/div[@class="row"]/div[position()=2]'))
            for node in search:    
                labels.extend(node.xpath('preceding-sibling::*/text()').extract())
                #handles tick or cross fields
                if "Interest Rate Notes" in node.xpath('preceding-sibling::*/text()').extract()[0]:
                    details.append('')
                elif "Loan Term" in node.xpath('preceding-sibling::*/text()').extract()[0]:
                    node2 = node.xpath('div')
                    details.extend(node2.xpath('div[1]/text()').extract())
                    labels.extend(node2.xpath('div[2]/text()').extract())
                    details.extend(node2.xpath('div[3]/text()').extract())
                elif "Loan Amount" in node.xpath('preceding-sibling::*/text()').extract()[0]:
                    details.extend(node.xpath('div/div/text()').extract())
                elif "cross" in str(node.xpath('img/@src')):
                    details.append("FALSE")
                elif "tick" in str(node.xpath('img/@src')):
                    details.append("TRUE")
                #grabs text fields
                elif not node.xpath('img'):
                    details.extend(node.xpath('text()').extract())
                else: 
                    details.append("ERROR")
                    #print(str(node.xpath('img/@src')))

            #clean format
            labels = [x.strip() for x in labels]
            details = [x.strip() for x in details]
            details = [x.replace("\n"," ") for x in details]

            #print(len(labels))
            #print(len(details))
            #print(labels)
            #print(details)
            #attach data to main
            for i in range(len(labels)):
                output[labels[i]] = details[i]
            self._data.append(output)
            print(output)
            output = {}
            
            #stop while loop once all rates on page completed
            if homeLoanType == 'VARIABLE':
                break
            elif homeLoanType == 'FIXED' and tableRow == len(fixNode):
                break

#avoid detection
#process = CrawlerProcess()
#process.crawl(infochoice)
#process.start()