from scrapy import cmdline

name = 'zhihu'
cmd = 'scrapy crawl {0} -s JOBDIR=../zhihu'.format(name)
cmdline.execute(cmd.split())