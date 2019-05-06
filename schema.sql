-- MySQL dump 10.13  Distrib 5.7.15, for osx10.11 (x86_64)
--
-- Host: localhost    Database: rss
-- ------------------------------------------------------
-- Server version	5.7.15

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `article`
--

DROP TABLE IF EXISTS `article`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `article` (
  `id` int(11) NOT NULL,
  `title` text,
  `link` text,
  `body` longtext COMMENT '处理过的内容',
  `date` varchar(32) DEFAULT NULL,
  `score` float DEFAULT NULL COMMENT '推荐评分',
  `site` text COMMENT '来源网站',
  `n_like` int(5) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `article_event`
--

DROP TABLE IF EXISTS `article_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `article_event` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'primary key',
  `name` varchar(32) NOT NULL COMMENT 'event name',
  `time` int(11) NOT NULL COMMENT 'event timestamp',
  `evt_attr` text COMMENT 'event attribute json string',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3138 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `article_feat`
--

DROP TABLE IF EXISTS `article_feat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `article_feat` (
  `id` int(11) NOT NULL,
  `y` int(11) DEFAULT NULL COMMENT 'target',
  `f_site` varchar(64) DEFAULT NULL,
  `f_title_keywords` text,
  `f_content_keywords` text,
  `f_date` varchar(32) DEFAULT NULL,
  `f_content_len` int(11) DEFAULT NULL,
  `f_img_n` int(11) DEFAULT NULL,
  `f_like_similarity` float DEFAULT NULL,
  `f_hate_similarity` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `article_tags`
--

DROP TABLE IF EXISTS `article_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `article_tags` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) DEFAULT NULL,
  `article_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_id` (`name`,`article_id`),
  KEY `article_id` (`article_id`),
  CONSTRAINT `article_tags_ibfk_1` FOREIGN KEY (`article_id`) REFERENCES `article` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=98621 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `main_content_feat`
--

DROP TABLE IF EXISTS `main_content_feat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_content_feat` (
  `body` longtext,
  `f_text_n` int(11) DEFAULT NULL COMMENT 'text len',
  `f_p_n` int(11) DEFAULT NULL COMMENT 'p tag number',
  `f_tag_n` int(11) DEFAULT NULL COMMENT 'tag number',
  `f_h_n` int(11) DEFAULT NULL COMMENT 'h tag number',
  `f_link_density` float DEFAULT NULL COMMENT 'link density',
  `y` int(11) DEFAULT NULL,
  `f_np_n` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rss`
--

DROP TABLE IF EXISTS `rss`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rss` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` text,
  `link` text,
  `desc` text,
  `body` longtext,
  `date` varchar(32) DEFAULT NULL,
  `score` float DEFAULT NULL COMMENT 'score',
  `n_show` int(5) DEFAULT NULL COMMENT '曝光次数',
  `n_click` int(5) DEFAULT '0' COMMENT '点击次数',
  `n_like` int(5) DEFAULT '0' COMMENT 'like次数',
  `n_hate` int(5) DEFAULT '0' COMMENT 'hate次数',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9750 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_feat`
--

DROP TABLE IF EXISTS `user_feat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_feat` (
  `like_title_kw` text,
  `like_content_kw` text,
  `hate_title_kw` text,
  `hate_content_kw` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-05-06 20:07:54
