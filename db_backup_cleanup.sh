#!/bin/bash

# Exit immediately if any command fails
set -e

# Variables
DB_USER="postgres"
DB_NAME="kite_db"
LOG_FILE="/var/newai/new_kite/logs/db_backup_cleanup.log"

echo "========== $(date) : Job started ==========" >> $LOG_FILE

psql -U $DB_USER -d $DB_NAME <<EOF >> $LOG_FILE 2>&1
INSERT INTO backup_nifty_prices SELECT * FROM nifty_prices;
TRUNCATE TABLE nifty_prices;

INSERT INTO backup_banknifty_prices SELECT * FROM banknifty_prices;
TRUNCATE TABLE banknifty_prices;

INSERT INTO backup_option_chain_data SELECT * FROM option_chain_data;
TRUNCATE TABLE option_chain_data;
EOF

echo "========== $(date) : Job completed ==========" >> $LOG_FILE

