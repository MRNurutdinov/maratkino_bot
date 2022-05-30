from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import asyncio
from aiogram.dispatcher import  FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import re
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import MyDB
import sys
import logging
from logging import FileHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = FileHandler("job_information.log",'w', 'utf-8')
logger.addHandler(handler)

citys={"Калининград":2,"Москва":3,"Самара":4,"Екатеренбург":5,"Омск":6,
       "Красноярск":7,"Новосибирск":7,"Иркутск":8,"Чита":9,"Владивосток":10,
       "Магадан":11,"Южный-Сахалинск":11,"Среднеколымск":11,"Анадырь":12,"Петропавловск-Камчатский":12}

db=MyDB()
loop=asyncio.new_event_loop()
TOKEN=open("sequrites.gitignore").read().split()[0]
bot = Bot(token=TOKEN,parse_mode="HTML")
storage=MemoryStorage()
dp = Dispatcher(bot,storage=storage,loop=loop)


@dp.message_handler(commands=['start'],state=None)
async def process_start_command(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items=[types.KeyboardButton(city) for city in citys.keys()]
    markup.add(*items)
    await bot.send_sticker(message.chat.id, open("Stikers/start.webp", "rb"))
    await bot.send_message(message.chat.id,
                     f"<b>Сэлэм,{message.from_user.first_name}!</b>\nМин хинен планировщик! Какой у тебя часовой пояс?",
                     parse_mode="html",reply_markup=markup)
    await Add_task.step3.set()

from add_task import Add_task
@dp.message_handler(state=Add_task.step3)
async def get_name_task(message: types.Message,state:FSMContext):
    time_zone = message.text
    if time_zone not in citys.keys():
        await message.answer("<b>Эээй, балам, попробуй еще раз!</b>\n")
    else:
        await message.answer("Эйбэт! Я запомнил.")
        await db.add_person(message.chat.id,int(citys[time_zone]))
        await state.finish()
        await menu(message)

@dp.message_handler(commands=['🏡Меню'], state=None)
async def menu(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items = [types.KeyboardButton("/📝Создать_задачу"), types.KeyboardButton("/🌍Изменить_часовой_пояс"),types.KeyboardButton("/🧾Список_задач")]
    markup.add(*items)
    await bot.send_message(message.from_user.id, "<b>Что будем делать?</b>", parse_mode="html",
                           reply_markup=markup)

#Секция добавления записи, нового задания
@dp.message_handler(commands=['📝Создать_задачу'], state=None)
async def create_task(message: types.Message):
    await bot.send_message(message.from_user.id, "<b>Напиши свою задачу, балам</b>", parse_mode="html")
    await Add_task.step1.set()

@dp.message_handler(state=Add_task.step1)
async def get_name_task(message: types.Message,state:FSMContext):
    name_task=message.text
    await state.update_data(
        {
            'name_task':name_task
        }
    )
    await message.answer("<b>Когда напомнить?</b>\nФормат ввода: ДД.ММ.ГГ чч:мм")
    await Add_task.step2.set()

@dp.message_handler(state=Add_task.step2)
async def get_time_task(message: types.Message,state:FSMContext):
    text=await state.get_data()
    name_task=text.get("name_task")
    time_remember=message.text
    if re.search(r'\d\d\.\d\d\.\d{2} \d\d:\d\d',time_remember)==None:
        await message.answer("<b>Эээй, балам, попробуй еще раз!</b>\nФормат: ДД.ММ.ГГ чч:мм")
        logger.warning(f"[WARNING] Неверный формат ввода, ввели={time_remember} (id_chat={message.chat.id})")
    else:
        r=await db.add_task(message.chat.id, name_task, time_remember)
        if r!=False:
            logger.info(f"[INFO] В чате={message.chat.id} пользователь добавил задачу={name_task}. Время напоминания:{time_remember})")
            await message.answer("Эйбэт! Я запомнил.")
            await state.finish()
        else:
            await message.answer("<b>Эээй, балам, несуществует такого дня!</b>\nФормат: ДД.ММ.ГГ чч:мм")
#Секция добавления задания закончилась

#Секция: А покажи ка мне мой to-do list, а так же удалить некоторые записи
@dp.message_handler(commands=['🧾Список_задач'])
async def show_tasks(message: types.Message):
    info_tasks,timezone= await db.get_task(int(message.chat.id))
    msg="<b>🧾Список задач:</b>\n\n"
    count=0
    for task in info_tasks:
        time_rem=str(task[1]).split('+')[0].split()
        date = time_rem[0].split("-")
        if int(time_rem[1][:2])+timezone>=24:
            oclock = str(int(time_rem[1][:2]) + timezone-24) + ":" + time_rem[1][3:5]
            date[2]=str(int(date[2])+1)
        else:
            oclock=str(int(time_rem[1][:2])+timezone)+":"+time_rem[1][3:5]
        msg=msg+f"{count+1}){task[0]}\n  Время напоминания: {oclock+' '+'.'.join(date[2::-1])}\n\n"
        count=count+1
    msg+="<b>Какую задачу снять?</b>"
    ikb_menu=types.InlineKeyboardMarkup(row_width=5,
                                        inline_keyboard=[[types.InlineKeyboardButton(text=str(i+1+num_row),callback_data="del_"+str(i+1+num_row))
                                                          for i in range(3) if i+1+num_row<=len(info_tasks)] for num_row in range(0,len(info_tasks),3)])
    await message.answer(msg,reply_markup=ikb_menu)

from aiogram.dispatcher.filters import Text
@dp.callback_query_handler(Text(startswith="del_"))
async def delete_an_task(call: types.CallbackQuery):
    # Парсим строку и извлекаем число, номер задачи для удаления
    num_task = int(call.data.split("del_")[1])
    await db.del_task(call.message.chat.id,num_task)
    await call.message.edit_text(f"Готово. Задача №{num_task} удалена")

#Изменение часового пояса
async def get_hour_city(num): #Получаем информацию по часовому поясу
    for k in citys.keys():
        if citys[k] == num:
            return k

@dp.message_handler(commands=['🌍Изменить_часовой_пояс'],state=None)
async def process_start_command(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items=[types.KeyboardButton(city) for city in citys.keys()]
    markup.add(*items)
    time_zone_now=await db.get_hour(message.chat.id)
    city_now=await get_hour_city(time_zone_now)
    await bot.send_message(message.chat.id,
                     f"<b>Внимание!</b> Смена часового пояса сместит время напоминаний на разницу поясов.\nВаш текущий часовой пояс: <b>{city_now}</b>\nНа какой хотите изменить?"
                     f"",
                     parse_mode="html",reply_markup=markup)
    await Add_task.change_time_zone.set()

@dp.message_handler(state=Add_task.change_time_zone)
async def get_name_task(message: types.Message,state:FSMContext):
    time_zone = message.text
    if time_zone not in citys.keys():
        await message.answer("<b>Эээй, балам, попробуй еще раз!</b>\n")
    else:
        await message.answer("Эйбэт! Часовой пояс измёнен.")
        time_zone_past = await db.get_hour(message.chat.id)
        time_zone_now=int(citys[time_zone])
        # await db.update_time_zone(message.chat.id,time_zone_now,time_zone_past)
        await db.add_person(message.chat.id, time_zone_now)
        await state.finish()
        await menu(message)

async def time_1_min():
    datas=await db.get_tasks_by_time()
    if len(datas)>0:
        for id,text in datas:
            chat_id=await db.get_chat_id(id)
            await bot.send_message(chat_id=int(chat_id),text=f"<b>Напоминание!\n</b>{text}")



if __name__ == '__main__':
    scheduler=AsyncIOScheduler()
    scheduler.add_job(time_1_min,"interval",seconds=60)
    scheduler.start()
    executor.start_polling(dp,skip_updates=True)