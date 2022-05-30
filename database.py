host="127.0.0.1"
user="postgres"
password=open("sequrites.gitignore").read().split()[1]
db_name="bot_timer"
import asyncio
import psycopg2


class MyDB():
    def __init__(self):
        try:
            self.connection=psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            self.cursor=self.connection.cursor()
            self.cursor.execute("set time zone 0;")
            self.connection.commit()
            # self.cursor.execute(f""" set client_encoding to 'UTF8';""")
            # self.cursor.fetchone()
        except Exception as ex:
            print("[INFO] Error while wokring with PostgreSQL",ex)

    def close(self):
        if self.connection:
            self.connection.close()
            print("[INFO] PostgreQSL connection closed")

    # Добавляем новых пользователей в наш БД или обновляем его часовой пояс
    async def add_person(self,id_chat,time_zone):
        self.cursor.execute(f"""SELECT id FROM users WHERE chat_id={id_chat}""")
        self.cursor.execute(f"""INSERT INTO users(chat_id,timezone) VALUES ({id_chat},{time_zone}) ON CONFLICT(chat_id) DO UPDATE SET timezone=EXCLUDED.timezone;""")
        self.connection.commit()

    # Добавляем новые чаты в наш БД
    async def add_task(self, id_chat,text,time_remember):
        try:
            self.cursor.execute(f"""SELECT id,timezone FROM users WHERE chat_id={id_chat};""")
            id_user, timezone = map(int, self.cursor.fetchone())
            self.cursor.execute(f"""INSERT INTO tasks(id_user,text,time_notif) VALUES({id_user},'{text}','{time_remember}+{timezone}') ON CONFLICT(text,time_notif) DO NOTHING;""")
            self.connection.commit()
        except:
            self.connection.rollback()
            return False

    # Получение списка задач
    async def get_task(self,id_chat):
        self.cursor.execute(f"""SELECT id,timezone FROM users WHERE users.chat_id={int(id_chat)};""")
        id_user,timezone = map(int,self.cursor.fetchone())
        self.cursor.execute(f"""SELECT text,time_notif FROM tasks WHERE tasks.id_user={int(id_user)};""")
        return self.cursor.fetchall(),timezone

    # Получение списка задач
    async def del_task(self,id_chat,num_task):
        self.cursor.execute(f"""SELECT id FROM users WHERE users.chat_id={int(id_chat)};""")
        id_user = int(self.cursor.fetchone()[0])
        self.cursor.execute(f"""SELECT * FROM tasks WHERE tasks.id_user={int(id_user)};""")
        tasks_user = self.cursor.fetchall()
        id_task=int(tasks_user[num_task-1][0])
        self.cursor.execute(f"""DELETE FROM tasks WHERE id={id_task};""")
        self.connection.commit()

    # Получение информацию по часовому поясу
    async def get_hour(self,id_chat):
        self.cursor.execute(f"""SELECT timezone FROM users WHERE users.chat_id={int(id_chat)};""")
        return int(self.cursor.fetchone()[0])

    # Получение списка задач, о которых сейчас нужно напомнить
    async def get_tasks_by_time(self):
        self.cursor.execute(f"""SELECT date_trunc('minute', now());""")
        self.cursor.execute(f"""SELECT id_user,text FROM tasks WHERE time_notif=date_trunc('minute', now());""")
        self.connection.commit()
        q=self.cursor.fetchall()
        return q
    async def get_chat_id(self,id_user):
        self.cursor.execute(f"""SELECT chat_id FROM users WHERE id={id_user};""")
        return self.cursor.fetchone()[0]