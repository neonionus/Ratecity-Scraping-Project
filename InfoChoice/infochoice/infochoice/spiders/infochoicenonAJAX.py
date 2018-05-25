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

#Usage: "scrapy crawl infochoice"
#Crawls all comapany pages in URLS.txt, finds attached home loan product pages
#and takes all data from them. Then puts data into csv file. 

##################################################################

def getURLS(filename):
    f = open(filename, "r")
    return [i.strip("\n") for i in f.readlines()]

class infochoice(CrawlSpider):
    name = "infochoicenonAJAX"
    #start_urls = getURLS("URLS.txt")
    
    #test sample links so testing doesn't take forever
    start_urls = ['https://www.infochoice.com.au/institutions/adelaidebank/98',
               'https://www.infochoice.com.au/institutions/westpac/19',
                'https://www.infochoice.com.au/institutions/amo/384',
                'https://www.infochoice.com.au/institutions/emoney/807',
                'https://www.infochoice.com.au/institutions/firstoptioncreditunion/760']
    
    #allowed_domains=["infochoice.com.au"]
    #only crawl home loan product pages
    rules = [
        Rule(
            LinkExtractor(
                #allow='.+/home-loans/.+', 
                deny='.+/interest-rates/.+',
                #restrict_xpaths='//a[@class="reportProductLink"]'
                #
                ),
            callback='parse_item',
            follow=True
        )
    ]
    
    def __init__(self, *a, **kw):
        print("derp")
        super(infochoice, self).__init__(*a, **kw)
        self._data = []
        self._headers = set()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    #writes data to csv when spider is finished    
    def spider_closed(self, spider):   
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
    def parse_item(self, response):
        derp = re.match(r"-[0-9]+$")

        #checks if product page is Variable or Fixed as they have different rate formats
        if response.xpath('//h4[@class="ratesTableTitle"]'):
            homeLoanType = "FIXED"
        elif response.xpath('//div[@class="variableRatePanel"]'):
            homeLoanType = "VARIABLE"
        else: homeLoanType = "ERROR"

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
            fixNode = response.xpath('//tr[contains(@class, "ratesTableRow")]')
        else:
            #pull variable rates
            percentNode = response.xpath('//span[@class="percentage"]/text()').extract()
            percentNode = [x.strip() for x in percentNode]
            #if intro rate
            if len(percentNode) > 2:
                introRate = percentNode[0]
                rate = percentNode[1]
                compRate = percentNode[2]
            #if no intro rate, also handles equity rates
            else:
                rate = percentNode[0]
                compRate = ""
                if len(percentNode) > 1:
                    compRate = percentNode[1]

        while True:
            if homeLoanType == "FIXED":
                #loops through and pulls fixed rates, allocating each its own row
                realFixMonth = fixNode[tableRow].xpath('td/div[@class="cellTitle"]/text()').extract()[0].strip()
                rate = fixNode[tableRow].xpath('td/div[@class="cellRate"]/text()').extract()[0].strip().replace("%","")
                compRate = fixNode[tableRow].xpath('td/div[@class="cellRate comparisonRate"]/text()').extract()[0].strip().replace("%","")
                derp=derp+tableRow
                tableRow+=1
                #if the page has stupid revert and intro rate format
                if response.xpath('//div[@class="onGoingRatePanel"]'):
                    percentNode = response.xpath('//div[@class="onGoingRatePanel"]/div[@class="interestRate"]/text()').extract()
                    percentNode = [x.strip().split(' ',1)[0].strip() for x in percentNode]
                    revertRate = percentNode[0].replace("%","")
                #just revert rate
                elif response.xpath('//div[@class="variableRatePanel"]'):
                    percentNode = response.xpath('//div[@class="interestRate"]/span/text()').extract()
                    percentNode = [x.strip().split(' ',1)[0].strip() for x in percentNode]
                    revertRate = percentNode[0].replace("%","")

            #regex match names
            product = response.xpath('//meta[@name="description"]/@content').re(r'does\s(.+)\sfrom')[0]
            company = response.xpath('//meta[@name="description"]/@content').re(r'from\s(.+)\scomp')[0]
            
            #setup basic data gathered so far
            output = OrderedDict({
                "Company":company, 
                "Product":product, 
                "url":response.url,
                "Home Loan Type":homeLoanType,
                "Rate": rate,
                "CodeID": derp,
                "Comparison Rate":compRate,
                "Fixed Months":realFixMonth,
                "Revert Rate":revertRate,
                "Introductory Rate":introRate
                })

            #loops through and gathers other information
            labels = []
            details = []
            for node in response.xpath('//div[@class="row"]/div[@class="details"]'):
                #handles tick or cross fields
                if "cross.png" in str(node.xpath('img/@src')):
                    details.append("FALSE")
                elif "tick.png" in str(node.xpath('img/@src')):
                    details.append("TRUE")
                #grabs text fields
                elif not node.xpath('img'):
                    details.extend(node.xpath('text()').extract())
                else: 
                    details.append("ERROR")
                #grabs associated label for detail data parsed
                labels.extend(node.xpath('preceding-sibling::*/text()').extract())

            #clean format
            labels = [x.strip() for x in labels]
            details = [x.strip() for x in details]
            details = [x.replace("\n"," ") for x in details]

            #attach data to main
            for i in range(len(labels)):
                output[labels[i]] = details[i]
            self._data.append(output)
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