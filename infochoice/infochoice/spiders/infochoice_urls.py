import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

#Usage: "scrapy crawl infochoice_urls"
#Crawls for list of all company page urls from sitemap.xml and puts them in URLS.txt file

class infochoice_urls(CrawlSpider):
    name = 'infochoice_urls'
    start_urls = ['http://www.infochoice.com.au/infochoice/sitemap.xml']
    allowed_domains=["infochoice.com.au"]
    rules = [
        Rule(
            LinkExtractor(
                allow='/home-loans/.+/.+', 
                restrict_xpaths='//a[@class="reportProductLink"]'
                ),
            callback='parse_item'
        )
    ]

    def parse_item(self, response):      
        print(response.url)
        print("#########")
        f = open("URLS.txt", "a+")
        f.write(response.request.url)
        f.write("\n")
        f.close()
