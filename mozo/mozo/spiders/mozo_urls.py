import scrapy

#scrapy runspider mozo_urls.py

class mozo_urls(scrapy.Spider):
    name = 'mozo_urls'
    start_urls = ['https://mozo.com.au/sitemap-remaining.xml']
    
    def parse(self, response):
        print(response)
        all_urls = []
        for url in response.xpath('//text()').extract(): #xpath not working properly
            if "https://mozo.com.au/home-loans/information/" in url:
                print(url)
                all_urls.append(url)

        print(len(all_urls))      
        f = open("URLS.txt", "w+")
        f.write("\n".join(all_urls))
        f.close()
