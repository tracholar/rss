# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import mysql.connector
import time

class RssPipeline(object):
    def process_item(self, item, spider):
        c = self.db.cursor()
        c.execute("INSERT INTO rss (title, link, `desc`, body, `date`) VALUES (%s, %s, %s, %s, %s)",
                  (item['title'], item['link'], item['desc'], item['body'], time.asctime()))
        self.db.commit()

        #input('continue>')


    def open_spider(self, spider):
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="123456",
            database="rss"
        )

        c = self.db.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS rss (id int(11) NOT NULL AUTO_INCREMENT, title text, link text, `desc` text, body longtext, date varchar(32), PRIMARY KEY (`id`))")


    def close_spider(self, spider):
        self.db.close()
