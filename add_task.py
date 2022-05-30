from aiogram.dispatcher.filters.state import State,StatesGroup
class Add_task(StatesGroup):
    step1 = State()
    step2 = State()
    step3 = State()
    menu = State()
    change_time_zone=State()
