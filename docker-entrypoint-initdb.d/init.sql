create database control_db;
use control_db;
CREATE USER 'control_user'@'%' IDENTIFIED BY 'passw0rd';
GRANT ALL PRIVILEGES ON *.* TO 'control_user'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;