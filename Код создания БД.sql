#Создаем БД и сущности
CREATE DATABASE bot_timer;
CREATE TABLE IF NOT EXISTS users(id BIGSERIAL NOT NULL PRIMARY KEY, chat_id  INT8 NOT NULL,timezone INT2 NOT NULL);
CREATE TABLE IF NOT EXISTS tasks(id BIGSERIAL NOT NULL PRIMARY KEY, id_user  INT8 REFERENCES users(id), text VARCHAR(500),time_notif TIMESTAMPTZ);
#Добавляем ограничение на повторения
ALTER TABLE users ADD CONSTRAINT ch_id UNIQUE(chat_id);
ALTER TABLE tasks ADD CONSTRAINT not_copy_str UNIQUE (text,time_notif);
