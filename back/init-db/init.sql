CREATE DATABASE IF NOT EXISTS `my_app_db`;
CREATE USER IF NOT EXISTS 'my_app_user'@'%' IDENTIFIED BY 'my_app_password';
GRANT ALL PRIVILEGES ON `my_app_db`.* TO 'my_app_user'@'%';
FLUSH PRIVILEGES;
