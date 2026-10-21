-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: politory
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `politory`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `politory` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `politory`;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=109 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add broiler rate',7,'add_broilerrate'),(26,'Can change broiler rate',7,'change_broilerrate'),(27,'Can delete broiler rate',7,'delete_broilerrate'),(28,'Can view broiler rate',7,'view_broilerrate'),(29,'Can add core users',8,'add_coreusers'),(30,'Can change core users',8,'change_coreusers'),(31,'Can delete core users',8,'delete_coreusers'),(32,'Can view core users',8,'view_coreusers'),(33,'Can add expensedetail',9,'add_expensedetail'),(34,'Can change expensedetail',9,'change_expensedetail'),(35,'Can delete expensedetail',9,'delete_expensedetail'),(36,'Can view expensedetail',9,'view_expensedetail'),(37,'Can add expense head',10,'add_expensehead'),(38,'Can change expense head',10,'change_expensehead'),(39,'Can delete expense head',10,'delete_expensehead'),(40,'Can view expense head',10,'view_expensehead'),(41,'Can add fat rate',11,'add_fatrate'),(42,'Can change fat rate',11,'change_fatrate'),(43,'Can delete fat rate',11,'delete_fatrate'),(44,'Can view fat rate',11,'view_fatrate'),(45,'Can add mortality',12,'add_mortality'),(46,'Can change mortality',12,'change_mortality'),(47,'Can delete mortality',12,'delete_mortality'),(48,'Can view mortality',12,'view_mortality'),(49,'Can add parties',13,'add_parties'),(50,'Can change parties',13,'change_parties'),(51,'Can delete parties',13,'delete_parties'),(52,'Can view parties',13,'view_parties'),(53,'Can add purchase payments',14,'add_purchasepayments'),(54,'Can change purchase payments',14,'change_purchasepayments'),(55,'Can delete purchase payments',14,'delete_purchasepayments'),(56,'Can view purchase payments',14,'view_purchasepayments'),(57,'Can add purchase receiving',15,'add_purchasereceiving'),(58,'Can change purchase receiving',15,'change_purchasereceiving'),(59,'Can delete purchase receiving',15,'delete_purchasereceiving'),(60,'Can view purchase receiving',15,'view_purchasereceiving'),(61,'Can add purchase receiving view',16,'add_purchasereceivingview'),(62,'Can change purchase receiving view',16,'change_purchasereceivingview'),(63,'Can delete purchase receiving view',16,'delete_purchasereceivingview'),(64,'Can view purchase receiving view',16,'view_purchasereceivingview'),(65,'Can add sells invoice',17,'add_sellsinvoice'),(66,'Can change sells invoice',17,'change_sellsinvoice'),(67,'Can delete sells invoice',17,'delete_sellsinvoice'),(68,'Can view sells invoice',17,'view_sellsinvoice'),(69,'Can add sellspayment',18,'add_sellspayment'),(70,'Can change sellspayment',18,'change_sellspayment'),(71,'Can delete sellspayment',18,'delete_sellspayment'),(72,'Can view sellspayment',18,'view_sellspayment'),(73,'Can add usermodule',19,'add_usermodule'),(74,'Can change usermodule',19,'change_usermodule'),(75,'Can delete usermodule',19,'delete_usermodule'),(76,'Can view usermodule',19,'view_usermodule'),(77,'Can add userpage',20,'add_userpage'),(78,'Can change userpage',20,'change_userpage'),(79,'Can delete userpage',20,'delete_userpage'),(80,'Can view userpage',20,'view_userpage'),(81,'Can add waste rate',21,'add_wasterate'),(82,'Can change waste rate',21,'change_wasterate'),(83,'Can delete waste rate',21,'delete_wasterate'),(84,'Can view waste rate',21,'view_wasterate'),(85,'Can add cash record',22,'add_cashrecord'),(86,'Can change cash record',22,'change_cashrecord'),(87,'Can delete cash record',22,'delete_cashrecord'),(88,'Can view cash record',22,'view_cashrecord'),(89,'Can add purchase payment history',23,'add_purchasepaymenthistory'),(90,'Can change purchase payment history',23,'change_purchasepaymenthistory'),(91,'Can delete purchase payment history',23,'delete_purchasepaymenthistory'),(92,'Can view purchase payment history',23,'view_purchasepaymenthistory'),(93,'Can add receipt history',24,'add_receipthistory'),(94,'Can change receipt history',24,'change_receipthistory'),(95,'Can delete receipt history',24,'delete_receipthistory'),(96,'Can view receipt history',24,'view_receipthistory'),(97,'Can add voucher',25,'add_voucher'),(98,'Can change voucher',25,'change_voucher'),(99,'Can delete voucher',25,'delete_voucher'),(100,'Can view voucher',25,'view_voucher'),(101,'Can add chart of account',26,'add_chartofaccount'),(102,'Can change chart of account',26,'change_chartofaccount'),(103,'Can delete chart of account',26,'delete_chartofaccount'),(104,'Can view chart of account',26,'view_chartofaccount'),(105,'Can add voucher detail',27,'add_voucherdetail'),(106,'Can change voucher detail',27,'change_voucherdetail'),(107,'Can delete voucher detail',27,'delete_voucherdetail'),(108,'Can view voucher detail',27,'view_voucherdetail');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `broiler_rate`
--

DROP TABLE IF EXISTS `broiler_rate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `broiler_rate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date DEFAULT NULL,
  `rate` decimal(18,0) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `broiler_rate`
--

LOCK TABLES `broiler_rate` WRITE;
/*!40000 ALTER TABLE `broiler_rate` DISABLE KEYS */;
/*!40000 ALTER TABLE `broiler_rate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cash_record`
--

DROP TABLE IF EXISTS `cash_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cash_record` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cash_in_hand` int DEFAULT NULL,
  `cash_in_bank` int DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `discription` varchar(450) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cash_record`
--

LOCK TABLES `cash_record` WRITE;
/*!40000 ALTER TABLE `cash_record` DISABLE KEYS */;
INSERT INTO `cash_record` VALUES (1,50000,30000,'2026-10-17 00:00:00','Opening Cash & Bank Balance'),(2,35000,30000,'2026-10-17 21:11:35','[CPV] #CPV-2026-00001: BAKI AIK HAFTY TK A JAO GY');
/*!40000 ALTER TABLE `cash_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chart_of_accounts`
--

DROP TABLE IF EXISTS `chart_of_accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chart_of_accounts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` int NOT NULL,
  `account_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `opening_balance` decimal(18,2) NOT NULL,
  `current_balance` decimal(18,2) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci,
  `created_at` datetime(6) NOT NULL,
  `parent_id` bigint DEFAULT NULL,
  `party_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `chart_of_accounts_parent_id_8b283fae_fk_chart_of_accounts_id` (`parent_id`),
  KEY `chart_of_accounts_party_id_51486332_fk_parties_id` (`party_id`),
  CONSTRAINT `chart_of_accounts_parent_id_8b283fae_fk_chart_of_accounts_id` FOREIGN KEY (`parent_id`) REFERENCES `chart_of_accounts` (`id`),
  CONSTRAINT `chart_of_accounts_party_id_51486332_fk_parties_id` FOREIGN KEY (`party_id`) REFERENCES `parties` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=86 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chart_of_accounts`
--

LOCK TABLES `chart_of_accounts` WRITE;
/*!40000 ALTER TABLE `chart_of_accounts` DISABLE KEYS */;
INSERT INTO `chart_of_accounts` VALUES (1,'01','Assets',1,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.207972',NULL,NULL),(2,'02','Liabilities',1,'Liability',0.00,0.00,1,NULL,'2026-10-13 17:30:48.213957',NULL,NULL),(3,'03','Equity & Capital',1,'Equity',0.00,0.00,1,NULL,'2026-10-13 17:30:48.218943',NULL,NULL),(4,'04','Revenue & Sales',1,'Revenue',0.00,0.00,1,NULL,'2026-10-13 17:30:48.222931',NULL,NULL),(5,'05','Expenses',1,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.226921',NULL,NULL),(6,'0101','Current Assets',2,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.229913',1,NULL),(7,'0102','Fixed & Non-Current Assets',2,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.233903',1,NULL),(8,'0201','Current Liabilities',2,'Liability',0.00,0.00,1,NULL,'2026-10-13 17:30:48.237893',2,NULL),(9,'0202','Long-term Liabilities',2,'Liability',0.00,0.00,1,NULL,'2026-10-13 17:30:48.241882',2,NULL),(10,'0301','Owner\'s Equity & Capital',2,'Equity',0.00,0.00,1,NULL,'2026-10-13 17:30:48.245872',3,NULL),(11,'0401','Operating Revenue & Sales',2,'Revenue',0.00,0.00,1,NULL,'2026-10-13 17:30:48.250857',4,NULL),(12,'0501','Direct Cost of Sales',2,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.254847',5,NULL),(13,'0502','Operating & Administrative Expenses',2,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.257839',5,NULL),(14,'010101','Cash & Bank Balances',3,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.260831',6,NULL),(15,'010102','Trade Receivables (Parties)',3,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.264821',6,NULL),(16,'010103','Inventory & Stock',3,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.268810',6,NULL),(17,'010201','Vehicles & Transport Assets',3,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.271801',7,NULL),(18,'010202','Plant & Equipment',3,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.274794',7,NULL),(19,'020101','Trade Payables (Parties)',3,'Liability',0.00,0.00,1,NULL,'2026-10-13 17:30:48.278782',8,NULL),(20,'020102','Short Term Borrowings',3,'Liability',0.00,0.00,1,NULL,'2026-10-13 17:30:48.281775',8,NULL),(21,'030101','Capital Account',3,'Equity',0.00,0.00,1,NULL,'2026-10-13 17:30:48.285765',10,NULL),(22,'040101','Poultry & Broiler Sales',3,'Revenue',0.00,0.00,1,NULL,'2026-10-13 17:30:48.289754',11,NULL),(23,'040102','By-Product Sales',3,'Revenue',0.00,0.00,1,NULL,'2026-10-13 17:30:48.293742',11,NULL),(24,'050101','Broiler Purchase Cost',3,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.296733',12,NULL),(25,'050102','Mortality Loss',3,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.300724',12,NULL),(26,'050201','Vehicle & Transport Expenses',3,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.303715',13,NULL),(27,'050202','Utilities & Bills',3,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.307705',13,NULL),(28,'050203','Salaries & Wages',3,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.310697',13,NULL),(29,'050204','Office & General Expenses',3,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.314686',13,NULL),(30,'010101001','Cash in Hand',4,'Asset',50000.00,35000.00,1,NULL,'2026-10-13 17:30:48.318681',14,NULL),(31,'010101002','Bank Al-Habib Main',4,'Asset',30000.00,30000.00,1,NULL,'2026-10-13 17:30:48.326654',14,NULL),(32,'010101003','Meezan Bank Account',4,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.331641',14,NULL),(33,'010101004','MCB Bank Account',4,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.336629',14,NULL),(34,'010102000','General Party Receivables',4,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.339619',15,NULL),(35,'010103001','Live Broiler Stock',4,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.343610',16,NULL),(36,'010201001','Delivery Vehicles',4,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.346614',17,NULL),(37,'010202001','Cages & Weighing Scales',4,'Asset',0.00,0.00,1,NULL,'2026-10-13 17:30:48.350590',18,NULL),(38,'020101001','General Party Payables',4,'Liability',0.00,0.00,1,NULL,'2026-10-13 17:30:48.359567',19,NULL),(39,'020102001','Temporary Loans',4,'Liability',0.00,0.00,1,NULL,'2026-10-13 17:30:48.363555',20,NULL),(40,'030101001','Owner Capital',4,'Equity',0.00,0.00,1,NULL,'2026-10-13 17:30:48.367548',21,NULL),(41,'030101002','Owner Drawings',4,'Equity',0.00,0.00,1,NULL,'2026-10-13 17:30:48.370537',21,NULL),(42,'040101001','Broiler Sales',4,'Revenue',0.00,0.00,1,NULL,'2026-10-13 17:30:48.375523',22,NULL),(43,'040102001','Fat Sales',4,'Revenue',0.00,0.00,1,NULL,'2026-10-13 17:30:48.378515',23,NULL),(44,'040102002','Waste Sales',4,'Revenue',0.00,0.00,1,NULL,'2026-10-13 17:30:48.382505',23,NULL),(45,'050101001','Broiler Purchases',4,'Expense',0.00,10000.00,1,NULL,'2026-10-13 17:30:48.385496',24,NULL),(46,'050102001','Mortality Loss',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.389488',25,NULL),(47,'050201001','Diesel & Fuel Expense',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.392478',26,NULL),(48,'050201002','Vehicle Maintenance & Repair',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.396467',26,NULL),(49,'050202001','Electricity Bill',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.399459',27,NULL),(50,'050202002','Mobile & Internet Expense',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.403449',27,NULL),(51,'050203001','Staff Monthly Salaries',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.406440',28,NULL),(52,'050203002','Daily Labour Wages',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.409432',28,NULL),(53,'050204001','Office Tea & Entertainment',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.412424',29,NULL),(54,'050204002','Office Rent',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.416413',29,NULL),(55,'050204003','Stationery & Printing',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.419407',29,NULL),(56,'050204004','Miscellaneous Expense',4,'Expense',0.00,0.00,1,NULL,'2026-10-13 17:30:48.423402',29,NULL),(82,'010102001','vendor1',4,'Asset',-20000.00,-15000.00,1,'Level 4 Party Account: vendor1 (Party)','2026-10-17 15:58:46.096523',15,1),(83,'010102002','vendor2',4,'Asset',10000.00,10000.00,1,'Level 4 Party Account: vendor2 (Party)','2026-10-17 15:58:55.216222',15,2),(84,'010102003','customer1',4,'Asset',12000.00,12000.00,1,'Level 4 Party Account: customer1 (Party)','2026-10-17 15:59:02.226675',15,3),(85,'010102004','customer2',4,'Asset',-13000.00,-13000.00,1,'Level 4 Party Account: customer2 (Party)','2026-10-17 15:59:11.605961',15,4);
/*!40000 ALTER TABLE `chart_of_accounts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_users`
--

DROP TABLE IF EXISTS `core_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_users`
--

LOCK TABLES `core_users` WRITE;
/*!40000 ALTER TABLE `core_users` DISABLE KEYS */;
INSERT INTO `core_users` VALUES (2,'tabish','03106411072','123','tabish@gmail.com','Admin','abcd');
/*!40000 ALTER TABLE `core_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(7,'core','broilerrate'),(22,'core','cashrecord'),(26,'core','chartofaccount'),(8,'core','coreusers'),(9,'core','expensedetail'),(10,'core','expensehead'),(11,'core','fatrate'),(12,'core','mortality'),(13,'core','parties'),(23,'core','purchasepaymenthistory'),(14,'core','purchasepayments'),(15,'core','purchasereceiving'),(16,'core','purchasereceivingview'),(24,'core','receipthistory'),(17,'core','sellsinvoice'),(18,'core','sellspayment'),(19,'core','usermodule'),(20,'core','userpage'),(25,'core','voucher'),(27,'core','voucherdetail'),(21,'core','wasterate'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-09-09 16:54:37.641702'),(2,'auth','0001_initial','2026-09-09 16:54:38.509032'),(3,'admin','0001_initial','2026-09-09 16:54:38.774530'),(4,'admin','0002_logentry_remove_auto_add','2026-09-09 16:54:38.790361'),(5,'admin','0003_logentry_add_action_flag_choices','2026-09-09 16:54:38.807635'),(6,'contenttypes','0002_remove_content_type_name','2026-09-09 16:54:38.960757'),(7,'auth','0002_alter_permission_name_max_length','2026-09-09 16:54:39.070030'),(8,'auth','0003_alter_user_email_max_length','2026-09-09 16:54:39.103144'),(9,'auth','0004_alter_user_username_opts','2026-09-09 16:54:39.107179'),(10,'auth','0005_alter_user_last_login_null','2026-09-09 16:54:39.203268'),(11,'auth','0006_require_contenttypes_0002','2026-09-09 16:54:39.207408'),(12,'auth','0007_alter_validators_add_error_messages','2026-09-09 16:54:39.220704'),(13,'auth','0008_alter_user_username_max_length','2026-09-09 16:54:39.317488'),(14,'auth','0009_alter_user_last_name_max_length','2026-09-09 16:54:39.416520'),(15,'auth','0010_alter_group_name_max_length','2026-09-09 16:54:39.439447'),(16,'auth','0011_update_proxy_permissions','2026-09-09 16:54:39.453416'),(17,'auth','0012_alter_user_first_name_max_length','2026-09-09 16:54:39.542982'),(19,'sessions','0001_initial','2026-09-09 16:54:39.606814'),(20,'core','0002_alter_broilerrate_options_alter_coreusers_options_and_more','2026-09-09 17:07:17.947425'),(21,'core','0001_initial','2026-09-11 12:03:45.062306'),(22,'core','0002_cashrecord_purchasepaymenthistory_receipthistory_and_more','2026-10-13 17:22:23.379773'),(23,'core','0003_chartofaccount_party_alter_voucher_voucher_type_and_more','2026-10-14 16:07:49.091475');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('087z3jydq301jht6pzxz0pk93qoivaun','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xEqkf:XmCvGHkYjGb1diZfANS7B7TO6xX-xAuEoP5xKDeJyZ0','2026-10-22 16:13:49.614931'),('0lqmdypvlbw9os9xdd96pcmafh0uxjzj','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x8grN:pbmh1I9TAGE_CbyDBK-2XjFsQEuVORvW-m3FO8iJjFw','2026-10-05 16:27:17.627715'),('0mjfwue8imwguih39vhu953jgkd0nux2','eyJ1c2VyX2lkIjoyfQ:1xFEph:2hrSJGm2Vq_qQZWtDhpVWQLmV6qD2y75asr2wW2srf8','2026-10-23 17:56:37.695231'),('13sualk382j1m66waoao3a9unffjcknp','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xGKjn:4nn7EVk1C0IVnktfXTWO2VKVL3etxcyRybUCWEuZxng','2026-10-26 18:27:03.940153'),('18y8xtj1t2smidw6fakd4lzn23otjx3q','eyJ1c2VyX2lkIjoyfQ:1xHPi3:kyjek0z1D-RGEENzpqAMaY2T8KQl7ay8kEHh5N2XM98','2026-10-29 17:57:43.706130'),('1en9lzf0i6cyowq444wjiehb47dsx0pu','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xHA36:1Zs4PIp9TrikQMLvNelyp_FOU4Ik95t9ZBSkDuQgV9U','2026-10-29 01:14:24.433655'),('1zidrp91lihvio8nw2twe9wf963dm2f0','eyJ1c2VyX2lkIjoiMiIsInVzZXJfbmFtZSI6InRhYmlzaCJ9:1xGKKB:sXZuBp80vBRZBh_p60kDhzDvQ4ONsinLq5_hSDxunQs','2026-10-26 18:00:35.044556'),('251f9eu0xstycfktmkd3w1wqeekov0kn','eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRhYmlzaCIsInJvbGUiOiJBZG1pbiJ9:1xHAdN:so1A2YN2wpV8VCGBETqsgxxInLA6kN7Rf3xSCv2vYF4','2026-10-29 01:51:53.821949'),('2mtze2vu8k20umu42d4cbri91l8oklon','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x9dTX:Ni11b0dS1fWPww7cajy7Xcs1wFTk68rvwCj4KO9wSTM','2026-10-08 07:02:35.869750'),('2pkim3sbya4712k7m9mv7h1jwhxybwzr','eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRhYmlzaCIsInJvbGUiOiJBZG1pbiJ9:1xHAcw:MIT9A_Exb_V4fWCQ3Jadk-yvRAuzBCIO3Dv3vL_mehQ','2026-10-29 01:51:26.338215'),('35aq2o3dryix5kaalvhz6z8dlj81twaj','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x50Va:qzBa-7w0SAO6FFSOKaYct6NoqBu-2eAN0HTkPDDG1Yg','2026-09-25 12:37:34.885401'),('39kr2xzlvejq0tweh5ev1wu1wppc2zg2','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xGKhJ:JCh5Bt3SERZ2EQ4oRNi2Yw004ekqinm6Q5xmy9WA8Xg','2026-10-26 18:24:29.920668'),('41w78870dbpd05gf57xkjf8wf00nfbjv','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xE8Kw:zoE0pFpU-4dbTw2aZKhyr5Sx5wugu9FjP7SKQhwFs9k','2026-10-20 16:48:18.929249'),('45n4845zdp4xxtfjgiwkg5hdy6q1dc32','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xDuQL:WwDsxJ5Bu_DSqxfCvaELJp6bF-etN4YlkoV7vfQ2kIw','2026-10-20 01:56:57.767156'),('48xw6fsmwzwqcuaw8vj6ib1301t5yjmh','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xEUrv:1bfqqorM8cpUyP9uuVQP7kQIVvZjOl12IPjzwHHhAuY','2026-10-21 16:51:51.905605'),('4hc2le81kj41ts1u2a9os4a5vror52b0','eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRhYmlzaCIsInJvbGUiOiJBZG1pbiJ9:1xHB4m:3FCNltya2QDDTw500X0LGOi6hcpwBV0gS-Clq_tipGM','2026-10-29 02:20:12.171854'),('4lfny3hwosm09ekhaqyerht2d5o26nvb','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x8HGO:xUsTHpN8rI-iuivBsREguSZ8cT8oDhd3sD4eypsrQVw','2026-10-04 13:07:24.149208'),('4pho7hdeu60hvc43vqo4t3g0vxnzzdyi','eyJ1c2VyX2lkIjoiMiIsInVzZXJfbmFtZSI6InRhYmlzaCJ9:1xGKTj:S2AxtbbkYqKpkY_7lfRoz8WdH5Mqx5BQKSVSTw220QI','2026-10-26 18:10:27.869977'),('4qihdqocvh9rijgo16tkvc1qq3x7ahjx','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xCzKz:PEAe7wNx27We6mUQL96n9vpJA8lOQgLZ0Lyrp0txSAE','2026-10-17 12:59:37.830433'),('5eoqo7huip4784j5vjnye1iphkwuhqix','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xGKYy:fsIpOCqmFNmf1iztTmww9rL7KEGfnAmUvVmFcg0oI5U','2026-10-26 18:15:52.840209'),('5plx62owksnj1nrgw606vplukf6026eo','eyJ1c2VyX2lkIjoiMiJ9:1xGKcA:qmfhoVYm0JJVTpTLpxZDM_xARb2AF4V3N70uK_xNWDU','2026-10-26 18:19:10.719082'),('6nmsz7zdfqpnwn8zllzaowqa9upn4qv2','eyJ1c2VyX2lkIjoiMiJ9:1xGKge:Mf8oTlFurlb1Vj4xv0WV-OF-graW7r7oFyijibXrWjY','2026-10-26 18:23:48.975765'),('6u20302zbga0zgkeqjxnmp1je3cfy3ln','eyJ1c2VyX2lkIjoyfQ:1xHPiR:0ae2n4GdUBtNa9m6d5p27HvI50YeVezk7f_wzkl9y7c','2026-10-29 17:58:07.005210'),('7y81qixe23ixwgi2q8qz38wa22xgvrzc','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xE929:9fY-GLRim0kEo0fFdgPCG9hq2STD7a6AeEmG9E1cYE4','2026-10-20 17:32:57.771414'),('96b5l4nlrc087tsmy59eyv2ag9nqkad8','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x7shF:qXX7m0xgVHbtUWui7tUpEHCrrP7FAGFjLZPl7tNcnVM','2026-10-03 10:53:29.625000'),('avjbh4egx12orqtqr5n0xcvdkrrg1xk5','eyJ1c2VyX2lkIjoyfQ:1xFrx6:ombsiJGJY_JpaxuupgHckyMWBfxKJLdzwut0wC4phkI','2026-10-25 11:42:52.934697'),('ay46kgxdpkhpzxnfadfkvzep37ndbrda','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xIPVF:swYqZVieX4U5TjpfxxteuP_tmBm6GkuTqgg-i57gNtE','2026-11-01 11:56:37.272272'),('byz1f9a7tqz5uhhi6rlb0uo3o5oyw1q4','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x7kUl:khKTa2Ck-qePwBFCyDhAYcczHDysAO6iBtv0JPdlYk0','2026-10-03 02:08:03.061163'),('cb34hioqmaal2heck4k25s72pqcr51hy','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xGKK1:tsUl5xC8HXOBZgAyhDQG5NX9cHxstMYjBSQmdEqTpkI','2026-10-26 18:00:25.013390'),('cgdvrr209ug98k5bk2okqt0vv12fx7y1','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xE8LA:ITiinzxTBBxp5HeCHECpLTAD0iVSE44An3yzeOqmBOo','2026-10-20 16:48:32.697339'),('cmn4xx195t3xjvpfxklse34h4k81i1n7','eyJ1c2VyX2lkIjoxfQ:1xByod:BFpSlxG2hUw-LpVWgrpUYnnIfDUgsYFkZfZKa6w7SIE','2026-10-14 18:14:03.421258'),('d9gl0xs8c80nzbrgj5748s4teuikvy6i','eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRhYmlzaCIsInJvbGUiOiJBZG1pbiJ9:1xHAdF:YfVp0DGoYNhrNc77oFplVUvuNo3v1OwRUl2724QG_fA','2026-10-29 01:51:45.592311'),('dd1ki2k7ygxgdxgop2ei75x6uu6smaup','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xCgpi:MkdCNgnPtdylBcFh_jHZvQbswp_iAkUeqXglZ73Yxrk','2026-10-16 17:14:06.480413'),('ex791lbf30q2ze5bi3q3au8534kwnwvo','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xA7nv:9MiLIPYVLbxureNkad515bcfGmPukmEP8kknFsgdIoY','2026-10-09 15:25:39.074572'),('fbp50ewm8f4oelfy8bqdwqig4dqmeq9w','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xGfRe:BXtEFw4xvz8pjeWqX5hDBHbAB8_MOEcWzdhzkFNavBg','2026-10-27 16:33:42.579496'),('g0pgc85ee8pl3i39xv8xwr76gvyp2vfd','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xE7Xo:N5atAjoFBS1DcbOQ6C00x99-z1wO_UK8ESCHYMBJT4o','2026-10-20 15:57:32.228101'),('h6jmld7trw8bk3qnfeyumnde9o3i6vou','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xFvX9:SLjpnVUUaqdVsgOJOX544XfSj-px6847jDzN9M0gWSI','2026-10-25 15:32:19.843538'),('i7lkixoibagr0cwb69heo5l8u2yppukv','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xBjTq:bVv7KVVIFPhoYYQjVGZgQ6JgQ7ulU0rUuVE3EZO1hUE','2026-10-14 01:51:34.671946'),('i7wj7cwu5owlqz30jpzz5i5dg80qzy3q','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xHjmC:y65qSnRlZ7aynhDu8ywu0IQsRrlBWk4AZKSh-3dtIvI','2026-10-30 15:23:20.461050'),('ig94i6ecw9ceva9q9ah8t4ksiqgfpras','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x4zcB:J7y8wfTFDh0Css4uRq7owtU-oMhbfpRwIhsZ7lFDX0g','2026-09-25 11:40:19.268423'),('l758m1ryepf0u7b67qpa0rdpezo4s4l8','eyJ1c2VyX2lkIjoiMiIsInVzZXJfbmFtZSI6InRhYmlzaCJ9:1xGKUW:sEw1gFK3ZXms8MzKRWqq2YCDRV6XXIPrZpXGfC4DSQg','2026-10-26 18:11:16.994648'),('low8uei3no3cjjbnu1twog8mst5fco1t','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xHOPe:rkt63YIlCSqZnxaBuO9ecTo0eD3W9rDF1LcIiMBuCdQ','2026-10-29 16:34:38.040758'),('m2iss8tzbmut3q7hhnz91suae2erpl2c','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x52Wi:4DiFSe9BFeTwOS1v5PuA9DtxJhZUKcmPOCnk3CWpPXg','2026-09-25 14:46:52.569967'),('o2jz4i11c3kta3jahda36nhdibupbh6b','e30:1xHAcZ:qnNefXWSviHJiHyrGRzp3AdP8aoagZMP37Fb4wuKQx4','2026-10-29 01:51:03.742672'),('p82ypawvixwmdfn53tciol5rvkk1th1e','eyJ1c2VyX2lkIjoyfQ:1xFEpz:oIfDQQisQoeqMLNIzlAVtphxgJPrVFg850VTXzz-etk','2026-10-23 17:56:55.652568'),('qgam7k77j7yn1e8cmbhlvjfgcpuihjn8','eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRhYmlzaCIsInJvbGUiOiJBZG1pbiJ9:1xHB51:UhbCIJ107hmzB5DUrpwX57YtistLIwezd0icVT1kXFw','2026-10-29 02:20:27.522933'),('qisvhpm99a084hbn5qn2dszakkuztlee','eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRhYmlzaCIsInJvbGUiOiJBZG1pbiJ9:1xHAdc:THjpFusq_HvU88G-2ez9fituP-MRm7Uhf_HA2O9K5B0','2026-10-29 01:52:08.666110'),('qs9ejh1rpb8ojb1qi97vshf4rbmk3335','eyJ1c2VyX2lkIjoiMiJ9:1xGKiT:IcCEsgGqWTsgiLCiZosP6Cj5ELf7lPhuMoTdWoiHHqA','2026-10-26 18:25:41.939681'),('r7pmt2624jju2znqr3hst9n3b3i27udf','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xFDDk:PM1bNHo2XVBf4QDDChhUn44AC_GDT5iL_P4YBPGEvbc','2026-10-23 16:13:20.400229'),('r9f5vcyg6ty53nps2tgoxcs15uhzrjj8','eyJ1c2VyX2lkIjoiMiJ9:1xGKKJ:R948FQmt4qQJNFZFwKZvzUJWcFabjXxBhn-ectDIMMo','2026-10-26 18:00:43.583115'),('rc4kj69kx16y4tvqq5qnyat90tjs0y5c','eyJ1c2VyX2lkIjoiMiJ9:1xGKc0:sfxAOmIHUm-RoW4kjRbxgHyIVMNbd9As1EZVfkJvXMw','2026-10-26 18:19:00.547661'),('ryla7yjsnwb7xkhm3cf3hv6n8cso5f6h','eyJ1c2VyX2lkIjoyfQ:1xFEqE:52ZewTza5BxGQ2LOyXJAyLsrATzUyJPd0Qt9N7qGgBQ','2026-10-23 17:57:10.203032'),('tsneo7vvaw5w2c8camzgrcbgkn37ow9s','eyJ1c2VyX2lkIjoiMiIsInVzZXJfbmFtZSI6InRhYmlzaCJ9:1xGKbq:tyJbTyVwoTUNXbJOeag45Zder84y2auA5IjnFPtejmw','2026-10-26 18:18:50.817306'),('u42ydflnvqlaadls1az99xebdn555avq','eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRhYmlzaCIsInJvbGUiOiJBZG1pbiJ9:1xHAcn:X_flZjx18o0DWiGZl88iPsic8zBEyjc4yiRDlQF7Btc','2026-10-29 01:51:17.808456'),('u702rbqde13lwzs2fa6yihpl7uburbzd','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x93A9:67isNddCkJJ5IcaFu-QIzKqz44z7WRCWj1yRZAcTRbA','2026-10-06 16:16:09.961732'),('ul4mt9i4yqtsos7ham131wr8dhy1y8lc','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xDeLO:kPLXhE_h9s_4BkzqQ-WzmM7Q_im0ZyjTlAGlSwANYhk','2026-10-19 08:46:46.293688'),('usglay3giog07qnz8wvi8o7j0w6dzhbf','eyJ1c2VyX2lkIjoiMiJ9:1xGKgS:rCXaGILqGslsf7m_nXB-Lr5nNO68O9wDXdXIRvc448k','2026-10-26 18:23:36.919746'),('v774fzk233x4yk6bevtkec8omxbj59u8','eyJ1c2VyX2lkIjoyfQ:1xFEpS:BmG1yzEsVmL3HCHyJMSlu8PgL7pdr--avLcllFyQBoo','2026-10-23 17:56:22.332350'),('v7zgoqmay3bb8enzs1l70qk4r8cfqsab','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xHkts:FcXyLD4RFROL5JxHAKtupIwicYBrxj9vnHeW2F2xwI4','2026-10-30 16:35:20.177117'),('vmkqwqambm3pjgw55emignim2n9ypjwp','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1x9ofJ:ciD1Z208bpGP2bvNeS9tVWs9hDhMv1hpVW36kJKO6vk','2026-10-08 18:59:29.210274'),('w60gemr4mc9vvohwpoea3kryhf48p728','eyJ1c2VyX2lkIjoyfQ:1xHPiG:wzbZXz6NYBCSw363-0UgTvxp3H4Q3WhYK9oOcegk3_c','2026-10-29 17:57:56.247419'),('wx2ezfwkv91672xyk7bxg6sq8qp1fye6','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xAfm6:TKOSJgVy6Ss7_HtLAAMaoT1bo_PIJdxnEvqn2hzZ34Y','2026-10-11 03:42:02.968136'),('x6j69bhecjkys4wo62ckqlpu19wvh113','eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRhYmlzaCIsInJvbGUiOiJBZG1pbiJ9:1xHAd6:4XJpwI4ctrUmmlP3RjXZjEEiY8szZzNQPtcDhOPKs8I','2026-10-29 01:51:36.355030'),('x8ptgokt9mgpblepuoh2mt5me1b17gah','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xDEP0:LLub1efVBCqXVgl0LZa6xO1BWgscUApfmBxZgO94TcU','2026-10-18 05:04:46.931913'),('xffvoem5y70l8s7yz3qszpunnr22e4vl','eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRhYmlzaCIsInJvbGUiOiJBZG1pbiJ9:1xHAdV:HJdAqhucZCem_hq1ogoKqBxF4kQAlUOHijQGLaS_uvs','2026-10-29 01:52:01.189619'),('yip41tyzmu1mh6om6xxzny4x2tznekxj','.eJyrViotTi2Kz0xRslIyUtKB8PISc1OB_JLEpMziDJhgUX4OSNAxJTczT6kWAA-CEqc:1xBwN5:C4T2vJRdhHiU_MsBRFMdbyi0L4GKffuaLh4TjnuPTx8','2026-10-14 15:37:27.051033');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `expense_head`
--

DROP TABLE IF EXISTS `expense_head`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expense_head` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entry_date` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expense_head`
--

LOCK TABLES `expense_head` WRITE;
/*!40000 ALTER TABLE `expense_head` DISABLE KEYS */;
/*!40000 ALTER TABLE `expense_head` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `expensedetail`
--

DROP TABLE IF EXISTS `expensedetail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expensedetail` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `head_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `head_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date` datetime(6) DEFAULT NULL,
  `amount` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `remarks` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expensedetail`
--

LOCK TABLES `expensedetail` WRITE;
/*!40000 ALTER TABLE `expensedetail` DISABLE KEYS */;
/*!40000 ALTER TABLE `expensedetail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fat_rate`
--

DROP TABLE IF EXISTS `fat_rate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fat_rate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `month` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `year` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rate` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fat_rate`
--

LOCK TABLES `fat_rate` WRITE;
/*!40000 ALTER TABLE `fat_rate` DISABLE KEYS */;
/*!40000 ALTER TABLE `fat_rate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mortality`
--

DROP TABLE IF EXISTS `mortality`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mortality` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `purchase_no` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vehicle_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `weight` decimal(18,0) DEFAULT NULL,
  `rate` decimal(18,0) DEFAULT NULL,
  `amount` decimal(18,0) DEFAULT NULL,
  `entry_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mortality`
--

LOCK TABLES `mortality` WRITE;
/*!40000 ALTER TABLE `mortality` DISABLE KEYS */;
/*!40000 ALTER TABLE `mortality` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `parties`
--

DROP TABLE IF EXISTS `parties`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parties` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `company_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `owner_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `party_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entry_date` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parties`
--

LOCK TABLES `parties` WRITE;
/*!40000 ALTER TABLE `parties` DISABLE KEYS */;
INSERT INTO `parties` VALUES (1,'0001','vendor1','','','Party','jknk','2026-10-17 15:58:46.088183'),(2,'0002','vendor2','','','Party','asd','2026-10-17 15:58:55.206766'),(3,'0003','customer1','','','Party','ad','2026-10-17 15:59:02.218696'),(4,'0004','customer2','','','Party','asd','2026-10-17 15:59:11.596407');
/*!40000 ALTER TABLE `parties` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_payment_history`
--

DROP TABLE IF EXISTS `purchase_payment_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_payment_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `party_code` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `party_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` datetime DEFAULT NULL,
  `totall_amount` int DEFAULT NULL,
  `payed_amount` int DEFAULT NULL,
  `due` int DEFAULT NULL,
  `advanced` int DEFAULT NULL,
  `remarks` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_payment_history`
--

LOCK TABLES `purchase_payment_history` WRITE;
/*!40000 ALTER TABLE `purchase_payment_history` DISABLE KEYS */;
INSERT INTO `purchase_payment_history` VALUES (1,'0001','vendor1','2026-10-17 21:09:16',10000,0,10000,0,'huhu');
/*!40000 ALTER TABLE `purchase_payment_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_payments`
--

DROP TABLE IF EXISTS `purchase_payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_payments` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `purchase_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `party_code` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `part_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date` datetime(6) DEFAULT NULL,
  `amount` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payment_mood` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `remarks` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_payments`
--

LOCK TABLES `purchase_payments` WRITE;
/*!40000 ALTER TABLE `purchase_payments` DISABLE KEYS */;
/*!40000 ALTER TABLE `purchase_payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_receiving`
--

DROP TABLE IF EXISTS `purchase_receiving`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_receiving` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `Purchase_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vendor_code` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vendor_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date` datetime(6) DEFAULT NULL,
  `vendor_rate` decimal(18,0) DEFAULT NULL,
  `market_rate` decimal(18,0) DEFAULT NULL,
  `weight` decimal(18,0) DEFAULT NULL,
  `vehicle_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `remaining_weight` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(18,0) DEFAULT NULL,
  `payed_amount` decimal(18,0) DEFAULT NULL,
  `remaining_amount` decimal(18,0) GENERATED ALWAYS AS ((`amount` - `payed_amount`)) STORED,
  `discription` varchar(450) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_receiving`
--

LOCK TABLES `purchase_receiving` WRITE;
/*!40000 ALTER TABLE `purchase_receiving` DISABLE KEYS */;
INSERT INTO `purchase_receiving` (`id`, `Purchase_number`, `vendor_code`, `vendor_name`, `date`, `vendor_rate`, `market_rate`, `weight`, `vehicle_number`, `status`, `remaining_weight`, `amount`, `payed_amount`, `discription`) VALUES (1,'PUR-00001','0001','vendor1','2026-10-17 21:09:16.475861',100,0,100,'9090','Active','100',10000,0,'huhu');
/*!40000 ALTER TABLE `purchase_receiving` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `purchase_receiving_view`
--

DROP TABLE IF EXISTS `purchase_receiving_view`;
/*!50001 DROP VIEW IF EXISTS `purchase_receiving_view`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `purchase_receiving_view` AS SELECT 
 1 AS `id`,
 1 AS `Purchase_number`,
 1 AS `vendor_name`,
 1 AS `date`,
 1 AS `vendor_rate`,
 1 AS `market_rate`,
 1 AS `weight`,
 1 AS `vehicle_number`,
 1 AS `status`,
 1 AS `remaining_weight`,
 1 AS `amount`,
 1 AS `payed_amount`,
 1 AS `remaining_amount`,
 1 AS `discription`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `receipt_history`
--

DROP TABLE IF EXISTS `receipt_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `receipt_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `party_name` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `part_code` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount` int DEFAULT NULL,
  `received_amount` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payment_method` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `due` int DEFAULT NULL,
  `advance` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `receipt_history`
--

LOCK TABLES `receipt_history` WRITE;
/*!40000 ALTER TABLE `receipt_history` DISABLE KEYS */;
INSERT INTO `receipt_history` VALUES (1,'vendor1','0001',0,'20000','Opening Advance','2026-10-17 00:00:00',0,20000),(2,'vendor2','0002',10000,'0','Opening Balance','2026-10-17 00:00:00',10000,0),(3,'customer1','0003',12000,'0','Opening Balance','2026-10-17 00:00:00',12000,0),(4,'customer2','0004',0,'13000','Opening Advance','2026-10-17 00:00:00',0,13000);
/*!40000 ALTER TABLE `receipt_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sells_invoice`
--

DROP TABLE IF EXISTS `sells_invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sells_invoice` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `purchase_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sells_no` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `customer_code` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `customer_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `weight` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rate` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `received_amount` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `remaining_amount` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vehicle_no` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entry_date` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sells_invoice`
--

LOCK TABLES `sells_invoice` WRITE;
/*!40000 ALTER TABLE `sells_invoice` DISABLE KEYS */;
INSERT INTO `sells_invoice` VALUES (1,'','OPEN-0001','0002','vendor2','0','0','10000','0','10000','OPENING','2026-10-17 00:00:00.000000'),(2,'','OPEN-0002','0003','customer1','0','0','12000','0','12000','OPENING','2026-10-17 00:00:00.000000');
/*!40000 ALTER TABLE `sells_invoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sellspayment`
--

DROP TABLE IF EXISTS `sellspayment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sellspayment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sell_no` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `customer_code` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `customer_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `weight` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rate` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vehicle_no` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `received_amount` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payment_method` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entry_date` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sellspayment`
--

LOCK TABLES `sellspayment` WRITE;
/*!40000 ALTER TABLE `sellspayment` DISABLE KEYS */;
INSERT INTO `sellspayment` VALUES (1,'OPEN(ADV)-0001','0001','vendor1','0','0','OPENING','0','20000','Opening Customer Advance - opening','Opening Balance','2026-10-17 00:00:00.000000'),(2,'OPEN(ADV)-0002','0004','customer2','0','0','OPENING','0','13000','Opening Customer Advance - kasji','Opening Balance','2026-10-17 00:00:00.000000');
/*!40000 ALTER TABLE `sellspayment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usermodule`
--

DROP TABLE IF EXISTS `usermodule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usermodule` (
  `ModuleID` int NOT NULL AUTO_INCREMENT,
  `UserID` int DEFAULT NULL,
  `ModuleName` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Module_url` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ShowModule` tinyint(1) DEFAULT NULL,
  `can_module_add` tinyint(1) DEFAULT NULL,
  `can_module_edit` tinyint(1) DEFAULT NULL,
  `can_module_delete` tinyint(1) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT NULL,
  `DisplayOrder` int NOT NULL,
  PRIMARY KEY (`ModuleID`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usermodule`
--

LOCK TABLES `usermodule` WRITE;
/*!40000 ALTER TABLE `usermodule` DISABLE KEYS */;
INSERT INTO `usermodule` VALUES (4,2,'New Accounts','parties/',1,1,1,1,1,2),(6,2,'Inventory Management','purchase_receiving/',1,1,1,1,1,3),(13,2,'Reports','party_ledger/',1,1,1,1,1,6),(15,2,'Chart of Accounts','voucher-entry/',1,1,1,1,1,1),(16,2,'User Management','user-management/',1,1,1,1,1,7),(17,2,'Market Rate','broiler-rate/',1,1,1,1,1,4),(18,2,'Opening','opening/',1,1,1,1,1,5);
/*!40000 ALTER TABLE `usermodule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userpage`
--

DROP TABLE IF EXISTS `userpage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `userpage` (
  `UserID` int DEFAULT NULL,
  `ModuleName` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `PageId` int NOT NULL AUTO_INCREMENT,
  `PageName` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Pageurl` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ShowPage` tinyint(1) DEFAULT NULL,
  `can_Page_add` tinyint(1) DEFAULT NULL,
  `can_Page_edit` tinyint(1) DEFAULT NULL,
  `can_Page_delete` tinyint(1) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT NULL,
  `DisplayOrder` int NOT NULL,
  `ModuleID` int DEFAULT NULL,
  PRIMARY KEY (`PageId`),
  KEY `UserPage_ModuleID_b0803175_fk_UserModule_ModuleID` (`ModuleID`),
  CONSTRAINT `UserPage_ModuleID_b0803175_fk_UserModule_ModuleID` FOREIGN KEY (`ModuleID`) REFERENCES `usermodule` (`ModuleID`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userpage`
--

LOCK TABLES `userpage` WRITE;
/*!40000 ALTER TABLE `userpage` DISABLE KEYS */;
INSERT INTO `userpage` VALUES (2,'New Accounts',2,'Parties Management','parties/',1,1,1,1,1,1,4),(2,'Market Rate',3,'Waste Rate','waste-rate/',1,1,1,1,1,3,17),(2,'Market Rate',4,'Fat Rate','fat-rate/',1,1,1,1,1,2,17),(2,'Market Rate',5,'Broiler Rate','broiler-rate/',1,1,1,1,1,1,17),(2,'New Accounts',6,'Expense Head Setup','expense-head/',1,1,1,1,1,2,4),(2,'Inventory Management',8,'Purchase Receiving','purchase_receiving/',1,1,1,1,1,1,6),(2,'Inventory Management',9,'Sells Invoice','sells/',1,1,1,1,1,2,6),(2,'Reports',10,'Party Ledger','party_ledger/',1,1,1,1,1,1,13),(2,'Reports',11,'Purchase Report','purchase_report/',1,1,1,1,1,4,13),(2,'Reports',12,'Sell Report','sells_report/',1,1,1,1,1,5,13),(2,'Reports',13,'Profit & Loss Report','profit_loss_report/',1,1,1,1,1,8,13),(2,'Opening',14,'Opening Page','opening/',1,1,1,1,1,1,18),(2,'Opening',15,'Cash Opening','cash/',1,1,1,1,1,2,18),(2,'Reports',16,'Cash Ledger','cash_ledger/',1,1,1,1,1,2,13),(2,'Reports',18,'Broiler Report','broiler_report/',1,1,1,1,1,7,13),(2,'Reports',20,'Daily Cash Report','cashreport/',1,1,1,1,1,3,13),(2,'Reports',22,'Net Position','net_position/',1,1,1,1,1,6,13),(2,'Chart of Accounts',23,'Chart of Accounts','chart-of-accounts/',1,1,1,1,1,2,15),(2,'Chart of Accounts',24,'Voucher Entry','voucher-entry/',1,1,1,1,1,1,15),(2,'Chart of Accounts',25,'Account Ledger','account-ledger/',1,1,1,1,1,3,15),(2,'Chart of Accounts',26,'Daily Expenses','expenses/',1,1,1,1,1,4,15),(2,'Inventory Management',27,'Waste Entry','waste_entry/',1,1,1,1,1,3,6),(2,'Inventory Management',28,'Waste Payment','waste-payment/',1,1,1,1,1,4,6),(2,'Market Rate',29,'Today Rate','today-rate/',1,1,1,1,1,4,17),(2,'User Management',30,'User Management & Permissions','user-management/',1,1,1,1,1,1,16),(2,'User Management',31,'Hierarchy Control','hierarchy/',1,1,1,1,1,2,16);
/*!40000 ALTER TABLE `userpage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `voucher_details`
--

DROP TABLE IF EXISTS `voucher_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `voucher_details` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `debit` decimal(18,2) NOT NULL,
  `credit` decimal(18,2) NOT NULL,
  `narration` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `account_id` bigint NOT NULL,
  `party_id` bigint DEFAULT NULL,
  `voucher_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `voucher_details_account_id_e76f368b_fk_chart_of_accounts_id` (`account_id`),
  KEY `voucher_details_party_id_92a137d5_fk_parties_id` (`party_id`),
  KEY `voucher_details_voucher_id_c782ff42_fk_vouchers_id` (`voucher_id`),
  CONSTRAINT `voucher_details_account_id_e76f368b_fk_chart_of_accounts_id` FOREIGN KEY (`account_id`) REFERENCES `chart_of_accounts` (`id`),
  CONSTRAINT `voucher_details_party_id_92a137d5_fk_parties_id` FOREIGN KEY (`party_id`) REFERENCES `parties` (`id`),
  CONSTRAINT `voucher_details_voucher_id_c782ff42_fk_vouchers_id` FOREIGN KEY (`voucher_id`) REFERENCES `vouchers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `voucher_details`
--

LOCK TABLES `voucher_details` WRITE;
/*!40000 ALTER TABLE `voucher_details` DISABLE KEYS */;
INSERT INTO `voucher_details` VALUES (1,10000.00,0.00,'Purchase #PUR-00001: 100kg @ 100',45,NULL,1),(2,0.00,10000.00,'Purchase Bill #PUR-00001',82,1,1),(3,15000.00,0.00,'BAKI AIK HAFTY TK A JAO GY',82,1,2),(4,0.00,15000.00,'BAKI AIK HAFTY TK A JAO GY',30,NULL,2);
/*!40000 ALTER TABLE `voucher_details` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vouchers`
--

DROP TABLE IF EXISTS `vouchers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vouchers` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `voucher_no` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `voucher_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` date NOT NULL,
  `reference_no` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_amount` decimal(18,2) NOT NULL,
  `remarks` longtext COLLATE utf8mb4_unicode_ci,
  `created_by` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `voucher_no` (`voucher_no`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vouchers`
--

LOCK TABLES `vouchers` WRITE;
/*!40000 ALTER TABLE `vouchers` DISABLE KEYS */;
INSERT INTO `vouchers` VALUES (1,'PUR-PUR-00001','JV','2026-10-17','9090',10000.00,'Purchase #PUR-00001 - vendor1 (100kg @ Rs. 100) - huhu','System / Purchase','2026-10-17 16:09:16.495439'),(2,'CPV-2026-00001','CPV','2026-10-17','CPV-2026-00001',15000.00,'BAKI AIK HAFTY TK A JAO GY','tabish','2026-10-17 16:11:35.247067');
/*!40000 ALTER TABLE `vouchers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `waste_rate`
--

DROP TABLE IF EXISTS `waste_rate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `waste_rate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `month` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `year` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rate` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `waste_rate`
--

LOCK TABLES `waste_rate` WRITE;
/*!40000 ALTER TABLE `waste_rate` DISABLE KEYS */;
/*!40000 ALTER TABLE `waste_rate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `politory`
--

USE `politory`;

--
-- Final view structure for view `purchase_receiving_view`
--

/*!50001 DROP VIEW IF EXISTS `purchase_receiving_view`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `purchase_receiving_view` AS select `purchase_receiving`.`id` AS `id`,`purchase_receiving`.`Purchase_number` AS `Purchase_number`,`purchase_receiving`.`vendor_name` AS `vendor_name`,`purchase_receiving`.`date` AS `date`,`purchase_receiving`.`vendor_rate` AS `vendor_rate`,`purchase_receiving`.`market_rate` AS `market_rate`,`purchase_receiving`.`weight` AS `weight`,`purchase_receiving`.`vehicle_number` AS `vehicle_number`,`purchase_receiving`.`status` AS `status`,`purchase_receiving`.`remaining_weight` AS `remaining_weight`,`purchase_receiving`.`amount` AS `amount`,`purchase_receiving`.`payed_amount` AS `payed_amount`,`purchase_receiving`.`remaining_amount` AS `remaining_amount`,`purchase_receiving`.`discription` AS `discription` from `purchase_receiving` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-18 17:00:59
