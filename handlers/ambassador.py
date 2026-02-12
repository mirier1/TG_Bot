from aiogram import Router, F, html
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import AsyncSessionLocal
from models import AmbassadorApplication
from datetime import datetime
from config import ADMIN_CHAT_ID
from aiogram.enums import ParseMode

router = Router()

# Состояния формы
class AmbassadorForm(StatesGroup):
    name = State()
    age = State()
    institution = State()
    city = State()
    contact = State()
    role = State()
    confirm = State()

# Кнопки для выбора роли
ROLES = {
    "ambassador": "🏫 Амбассадор в школе",
    "lecturer": "📚 Волонтёр-лектор",
    "eco": "🌿 Эко-волонтёр"
}

# Старт формы - ЭТОТ ХЕНДЛЕР ВЫЗЫВАЕТСЯ ИЗ ГЛАВНОГО МЕНЮ
@router.callback_query(F.data == "menu_ambassador")
async def start_ambassador_form(callback: CallbackQuery, state: FSMContext):
    """Начало формы 'Стать посланником'"""
    await callback.message.answer(
        "🎓 <b>Стать посланником ЦУР</b>\n\n"
        "Заполните анкету. Это займёт 2 минуты.\n\n"
        "<b>Шаг 1/6:</b> Введите ваше имя и фамилию:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AmbassadorForm.name)
    await callback.answer()

@router.message(AmbassadorForm.name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    if len(message.text) < 2:
        await message.answer("❌ Слишком короткое имя. Введите имя и фамилию:")
        return
    
    await state.update_data(name=message.text)
    await message.answer(
        "<b>Шаг 2/6:</b> Введите ваш возраст:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AmbassadorForm.age)

@router.message(AmbassadorForm.age)
async def process_age(message: Message, state: FSMContext):
    """Обработка возраста"""
    try:
        age = int(message.text)
        if age < 7 or age > 100:
            await message.answer("❌ Возраст должен быть от 7 до 100 лет. Введите корректный возраст:")
            return
    except ValueError:
        await message.answer("❌ Введите число (ваш возраст):")
        return
    
    await state.update_data(age=age)
    await message.answer(
        "<b>Шаг 3/6:</b> Введите название вашей школы/вуза:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AmbassadorForm.institution)

@router.message(AmbassadorForm.institution)
async def process_institution(message: Message, state: FSMContext):
    """Обработка учебного заведения"""
    if len(message.text) < 2:
        await message.answer("❌ Введите корректное название:")
        return
    
    await state.update_data(institution=message.text)
    await message.answer(
        "<b>Шаг 4/6:</b> Введите ваш город:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AmbassadorForm.city)

@router.message(AmbassadorForm.city)
async def process_city(message: Message, state: FSMContext):
    """Обработка города"""
    if len(message.text) < 2:
        await message.answer("❌ Введите корректное название города:")
        return
    
    await state.update_data(city=message.text)
    
    # Клавиатура для выбора роли
    builder = InlineKeyboardBuilder()
    for role_id, role_text in ROLES.items():
        builder.row(InlineKeyboardButton(
            text=role_text,
            callback_data=f"amb_role_{role_id}"
        ))
    
    await message.answer(
        "<b>Шаг 5/6:</b> Выберите вашу роль:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AmbassadorForm.role)

@router.callback_query(F.data.startswith("amb_role_"))
async def process_role(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора роли"""
    role = callback.data.replace("amb_role_", "")
    role_text = ROLES.get(role, role)
    
    await state.update_data(role=role, role_text=role_text)
    
    await callback.message.delete()
    await callback.message.answer(
        "<b>Шаг 6/6:</b> Введите ваш контакт (телефон или Telegram):",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AmbassadorForm.contact)
    await callback.answer()

@router.message(AmbassadorForm.contact)
async def process_contact(message: Message, state: FSMContext):
    """Обработка контакта и показ подтверждения"""
    if len(message.text) < 5:
        await message.answer("❌ Введите корректный контакт:")
        return
    
    await state.update_data(contact=message.text)
    data = await state.get_data()
    
    # Показываем сводку с экранированием HTML
    text = (
        f"📋 <b>Проверьте данные:</b>\n\n"
        f"<b>Имя:</b> {html.quote(data['name'])}\n"
        f"<b>Возраст:</b> {data['age']}\n"
        f"<b>Уч. заведение:</b> {html.quote(data['institution'])}\n"
        f"<b>Город:</b> {html.quote(data['city'])}\n"
        f"<b>Роль:</b> {html.quote(data['role_text'])}\n"
        f"<b>Контакт:</b> {html.quote(data['contact'])}\n\n"
        f"Всё верно?"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, отправить", callback_data="amb_confirm"),
        InlineKeyboardButton(text="✏️ Заполнить заново", callback_data="amb_restart")
    )
    
    await message.answer(
        text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AmbassadorForm.confirm)

@router.callback_query(F.data == "amb_confirm")
async def confirm_application(callback: CallbackQuery, state: FSMContext, bot):
    """Подтверждение и сохранение заявки"""
    data = await state.get_data()
    
    # Сохраняем в БД
    async with AsyncSessionLocal() as session:
        application = AmbassadorApplication(
            user_id=callback.from_user.id,
            full_name=data['name'],
            age=data['age'],
            institution=data['institution'],
            city=data['city'],
            contact=data['contact'],
            role=data['role'],
            status='pending'
        )
        session.add(application)
        await session.flush()
        
        # Отправляем в админ-чат с экранированием
        admin_text = (
            f"🆕 <b>Новая заявка посланника!</b>\n\n"
            f"<b>ID:</b> {application.id}\n"
            f"<b>От:</b> @{html.quote(callback.from_user.username or 'нет')}\n"
            f"<b>Имя:</b> {html.quote(data['name'])}\n"
            f"<b>Возраст:</b> {data['age']}\n"
            f"<b>Уч. заведение:</b> {html.quote(data['institution'])}\n"
            f"<b>Город:</b> {html.quote(data['city'])}\n"
            f"<b>Роль:</b> {html.quote(data['role_text'])}\n"
            f"<b>Контакт:</b> {html.quote(data['contact'])}\n\n"
            f"Статус: ⏳ Ожидает рассмотрения"
        )
        
        await bot.send_message(
            ADMIN_CHAT_ID,
            admin_text,
            parse_mode=ParseMode.HTML
        )
        
        await session.commit()
    
    # Отвечаем пользователю
    await callback.message.edit_text(
        "✅ <b>Заявка отправлена!</b>\n\n"
        "Мы рассмотрим её в ближайшее время и свяжемся с вами.\n"
        "Спасибо за ваше желание изменить мир к лучшему! 🌍",
        parse_mode=ParseMode.HTML
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "amb_restart")
async def restart_application(callback: CallbackQuery, state: FSMContext):
    """Перезапуск формы"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🔄 <b>Заполните анкету заново</b>\n\n"
        "Шаг 1/6: Введите ваше имя и фамилию:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(AmbassadorForm.name)
    await callback.answer()

@router.callback_query(F.data == "amb_cancel")
async def cancel_application(callback: CallbackQuery, state: FSMContext):
    """Отмена заполнения"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Заполнение анкеты отменено.\n"
        "Если передумаете - нажмите кнопку в меню.",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()