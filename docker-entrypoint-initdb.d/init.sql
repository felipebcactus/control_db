CREATE USER control_user;
alter user control_user ENCRYPTED password 'passw0rd';
CREATE DATABASE control_user;
GRANT ALL PRIVILEGES ON DATABASE control_user TO control_user;