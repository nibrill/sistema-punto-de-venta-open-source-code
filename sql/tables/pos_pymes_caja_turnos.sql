-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: pos_pymes
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `caja_turnos`
--

DROP TABLE IF EXISTS `caja_turnos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `caja_turnos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_apertura_id` int NOT NULL,
  `usuario_cierre_id` int DEFAULT NULL,
  `fecha_apertura` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_cierre` datetime DEFAULT NULL,
  `monto_inicial` decimal(12,2) NOT NULL DEFAULT '0.00',
  `monto_ventas_efectivo` decimal(12,2) NOT NULL DEFAULT '0.00',
  `monto_ventas_tarjeta` decimal(12,2) NOT NULL DEFAULT '0.00',
  `monto_ventas_transferencia` decimal(12,2) NOT NULL DEFAULT '0.00',
  `monto_ventas_total` decimal(12,2) NOT NULL DEFAULT '0.00',
  `monto_retiros` decimal(12,2) NOT NULL DEFAULT '0.00',
  `monto_ingresos_extra` decimal(12,2) NOT NULL DEFAULT '0.00',
  `monto_esperado_caja` decimal(12,2) NOT NULL DEFAULT '0.00',
  `monto_real_cierre` decimal(12,2) DEFAULT NULL,
  `diferencia` decimal(12,2) DEFAULT NULL,
  `estado` enum('ABIERTA','CERRADA') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ABIERTA',
  `observacion_apertura` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `observacion_cierre` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_caja_usuario_apertura` (`usuario_apertura_id`),
  KEY `fk_caja_usuario_cierre` (`usuario_cierre_id`),
  KEY `idx_caja_estado` (`estado`),
  KEY `idx_caja_fecha_apertura` (`fecha_apertura`),
  CONSTRAINT `fk_caja_usuario_apertura` FOREIGN KEY (`usuario_apertura_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `fk_caja_usuario_cierre` FOREIGN KEY (`usuario_cierre_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-01 17:34:50
