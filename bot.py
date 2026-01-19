import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BOT_TOKEN
from database import create_table
from database import AsyncSessionLocal
from models import User
from sqlalchemy import select


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

SDG_TITLES = {
    1: "ЦУР 1 Повсеместная ликвидация нищеты во всех её формах",
    2: "ЦУР 2 Ликвидация голода, обеспечение продовольственной безопасности и улучшение питания и содействие устойчивому развитию сельского хозяйства",
    3: "ЦУР 3 Обеспечение здорового образа жизни и содействие благополучию для всех в любом возрасте",
    4: "ЦУР 4 Обеспечение всеохватного и справедливого качественного образования и поощрение возможности обучения на протяжении всей жизни для всех",
    5: "ЦУР 5 Обеспечение гендерного равенства и расширение прав и возможностей всех женщин и девочек",
    6: "ЦУР 6 Обеспечение наличия и рационального использования водных ресурсов и санитарии для всех",
    7: "ЦУР 7 Обеспечение доступа к недорогостоящим, надёжным, устойчивым и современным источникам энергии для всех",
    8: "ЦУР 8 Содействие неуклонному, всеохватному и устойчивому экономическому росту, полной и производительной занятости и достойной работе для всех",
    9: "ЦУР 9 Создание прочной инфраструктуры, содействие обеспечению всеохватной и устойчивой индустриализации и внедрению инноваций",
    10: "ЦУР 10 Снижение уровня неравенства внутри стран и между ними",
    11: "ЦУР 11 Обеспечение открытости, безопасности, жизнестойкости и устойчивости городов и населённых пунктов",
    12: "ЦУР 12 Обеспечение рациональных моделей потребления и производства",
    13: "ЦУР 13 Принятие срочных мер по борьбе с изменением климата и его последствиями",
    14: "ЦУР 14 Сохранение и рациональное использование океанов, морей и морских ресурсов в интересах устойчивого развития",
    15: "ЦУР 15 Защита, восстановление экосистем суши и содействие их рациональному использованию, рациональное управление лесами, борьба с опустыниванием, прекращение и обращение вспять процесса деградации земель и прекращение процесса утраты биологического разно",
    16: "ЦУР 16 Содействие построению миролюбивых и открытых обществ в интересах устойчивого развития, обеспечение доступа к правосудию для всех и создание эффективных, подотчётных и основанных на широком участии учреждений на всех уровнях",
    17: "ЦУР 17 Укрепление средств достижения устойчивого развития и активизация работы механизмов глобального партнёрства в интересах устойчивого развития",
}

#КЛАВИАТУРА -----------------
#Создаем клавиатуру для главного меню
def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Цели устойчивого развития")],
            [KeyboardButton(text="🎮 Мини-игры")],
            [KeyboardButton(text="❓ Вопрос эксперту")],
            [KeyboardButton(text="🎓 Стать посланником ЦУР")],
            [KeyboardButton(text="🎥 Конкурс «Я есть ЦУР»")],
            [KeyboardButton(text="📊 Обратная связь")]
        ],
        resize_keyboard=True
    )

def get_age_kb():
    return ReplyKeyboardMarkup (
        keyboard=[
            [KeyboardButton(text="5-7 класс")],
            [KeyboardButton(text="9-11 класс")],
            [KeyboardButton(text="Студент")]
        ],
        resize_keyboard=True
    )

#----------------------------
#Обработчик команды /start
@dp.message(Command("start"))
async def command_start(message: Message):
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(
                "Привет! Для начала выбери свою возрастную группу:",
                reply_markup=get_age_kb()
            )
        elif not user.age_group:
            await message.answer(
                "Выбери свою возрастную группу:",
                reply_markup=get_age_kb()
            )
        else:
            await message.answer(
                "Добро пожаловать! Выберите раздел:",
                reply_markup=get_main_kb()
            )

@dp.message(F.text.in_(["5-7 класс", "9-11 класс", "Студент"]))
async def set_age_group(message: Message):
    age_map = {
        "5-7 класс": "young",
        "9-11 класс": "teen",
        "Студент": "student"
    }
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Создаём нового пользователя
            user = User(
                id=message.from_user.id,
                username=message.from_user.username or message.from_user.first_name or "Пользователь",
                age_group=age_map[message.text]
            )
            session.add(user)
        else:
            # Обновляем существующего
            user.age_group = age_map[message.text]
        
        await session.commit()
    
    await message.answer(
        "Отлично! Теперь ты можешь пользоваться ботом.",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📚 Цели устойчивого развития")
async def handler_uroky(message: Message):
    builder = InlineKeyboardBuilder()

    for num, title in SDG_TITLES.items():
        short_title = title[:30] + "..." if len(title) > 30 else title
        builder.add(InlineKeyboardButton(
            text=f"{num}. {short_title}",
            callback_data=f"sdg_{num}"
        ))
    
    builder.adjust(2)

    await message.answer(
        "Выберите цель устойчивого развития:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("sdg_"))
async def show_sdg_detail(callback: CallbackQuery):
    sdg_num = int(callback.data.split("_")[1])
    title = SDG_TITLES.get(sdg_num)
    
    await callback.message.edit_text(
        f"🎯 **Цель {sdg_num}: {title}**\n\n"
        f"*Описание:* В разработке\n"
        f"*Ваш возраст:* {callback.from_user.age_group if hasattr(callback.from_user, 'age_group') else 'не выбран'}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Пройти квиз", callback_data=f"quiz_{sdg_num}")],
            [InlineKeyboardButton(text="🎥 Смотреть видео", callback_data=f"video_{sdg_num}")],
            [InlineKeyboardButton(text="📖 Читать подробнее", callback_data=f"more_{sdg_num}")],
            [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="back_to_sdg_list")]
        ])
    )
    await callback.answer()



@dp.callback_query(F.data == "back_to_sdg_list")
async def back_to_sdg_list(callback: CallbackQuery):
    await callback.message.delete()
    await handler_uroky(callback.message)
    await callback.answer()

@dp.message()
async def echo(message: Message):
    await message.answer("Привет! Бот работает.")

async def on_startup():
    await create_table()
    print("✅ Таблицы созданы/проверены")

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())