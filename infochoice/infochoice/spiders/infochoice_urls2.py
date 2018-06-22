import scrapy

#scrapy runspider infochoice_urls.py

class infochoice_urls(scrapy.Spider):
    name = 'infochoice_urls2'
    start_urls = ['http://www.infochoice.com.au/infochoice/sitemap.xml']
    
    def parse(self, response):
        print(response)
        all_urls = []
        for url in response.xpath('//text()').extract():
            if "http://www.infochoice.com.au/institutions/" in url:
                print(url)
                all_urls.append(url)

        print(len(all_urls))      
        f = open("URLS.txt", "w+")
        f.write("\n".join(all_urls))
        f.close()
