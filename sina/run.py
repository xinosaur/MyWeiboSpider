from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging

from sina.spiders import weibo_spider

configure_logging()
runner = CrawlerRunner()
runner.crawl(weibo_spider)
d = runner.join()
d.addBoth(lambda _: reactor.stop())

reactor.run()