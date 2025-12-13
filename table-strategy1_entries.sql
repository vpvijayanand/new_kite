-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               PostgreSQL 16.2, compiled by Visual C++ build 1937, 64-bit
-- Server OS:                    
-- HeidiSQL Version:             12.12.0.7122
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES  */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Dumping data for table public.strategy1_entries: 8 rows
DELETE FROM "strategy1_entries";
/*!40000 ALTER TABLE "strategy1_entries" DISABLE KEYS */;
INSERT INTO "strategy1_entries" ("id", "entry_timestamp", "entry_date", "nifty_high_912_933", "nifty_low_912_933", "nifty_price_912", "nifty_price_933", "range_size", "trigger_type", "trigger_nifty_price", "sell_strike", "buy_strike", "option_type", "sell_ltp_entry", "buy_ltp_entry", "net_premium_entry", "lots", "quantity_per_lot", "total_quantity", "capital_used", "is_active", "closed_timestamp", "close_reason") VALUES
	(1, '2025-12-05 10:04:28.57555', '2025-12-05', 26061.95, 25985.35, 25999.8, 26036.2, 76.60000000000218, 'HIGH_BREAK', 26073.1, 25900, 25700, 'PE', 130.2, 98, 32.19999999999999, 3, 75, 225, 45000, 'true', NULL, NULL),
	(2, '2025-12-08 09:36:05.923067', '2025-12-08', 26178.7, 26127.05, 26159.8, 26128.7, 51.650000000001455, 'LOW_BREAK', 26115.05, 26300, 26500, 'CE', 236, 157.15, 78.85, 3, 75, 225, 45000, 'true', NULL, NULL),
	(3, '2025-12-09 09:40:58.918038', '2025-12-09', 25890.95, 25758.75, 25867.1, 25763.1, 132.20000000000073, 'LOW_BREAK', 25758.35, 26000, 26200, 'CE', 210, 154.4, 55.599999999999994, 3, 75, 225, 45000, 'true', NULL, NULL),
	(4, '2025-12-09 12:07:58.927729', '2025-12-09', 25890.95, 25758.75, 25867.1, 25763.1, 132.20000000000073, 'HIGH_BREAK', 25893.3, 25650, 25450, 'PE', 108.45, 91.55, 16.900000000000006, 3, 75, 225, 45000, 'true', NULL, NULL),
	(5, '2025-12-10 09:36:49.559259', '2025-12-10', 25905.55, 25832.65, 25864.05, 25903, 72.89999999999782, 'HIGH_BREAK', 25907.4, 25750, 25550, 'PE', 135.45, 85.5, 49.94999999999999, 3, 75, 225, 45000, 'true', NULL, NULL),
	(6, '2025-12-10 11:00:47.613642', '2025-12-10', 25905.55, 25832.65, 25864.05, 25903, 72.89999999999782, 'LOW_BREAK', 25823.25, 26000, 26200, 'CE', 204.95, 132, 72.94999999999999, 3, 75, 225, 45000, 'true', NULL, NULL),
	(7, '2025-12-11 09:39:44.724131', '2025-12-11', 25803.05, 25727.15, 25771.4, 25788.2, 75.89999999999782, 'LOW_BREAK', 25726.8, 25900, 26100, 'CE', 203, 138.85, 64.15, 3, 75, 225, 45000, 'true', NULL, NULL),
	(8, '2025-12-11 10:16:43.6475', '2025-12-11', 25803.05, 25727.15, 25771.4, 25788.2, 75.89999999999782, 'HIGH_BREAK', 25815.35, 25650, 25450, 'PE', 122.1, 75, 47.099999999999994, 3, 75, 225, 45000, 'true', NULL, NULL);
/*!40000 ALTER TABLE "strategy1_entries" ENABLE KEYS */;

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
