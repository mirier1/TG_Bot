import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import AsyncSessionLocal
from models import User
from sqlalchemy import select

from data.story_engine import GameEngine
from keyboards.story_kb import story_next_kb, story_end_kb, story_options_kb
from handlers.games.utils import save_game_result, create_game_keyboard

logger = logging.getLogger(__name__)
router = Router()

# Состояния игры
class StoryGameStates(StatesGroup):
    viewing_intro = State()
    answering = State()
    viewing_result = State()
    viewing_checkpoint = State()
    viewing_epilogue = State()
    viewing_ending = State()

# Инициализация движка
engine = GameEngine("data/scenario.json")

# Вспомогательная функция для получения age_group пользователя
async def get_user_age_group(user_id: int) -> str | None:
    async with AsyncSessionLocal() as session:
        stmt = select(User.age_group).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar()

# Обработчик запуска игры
@router.callback_query(F.data.startswith("game_story_"))
async def start_story_game(callback: CallbackQuery, state: FSMContext):
    age_group = callback.data.split("_")[2]  # 'teen' или 'student'
    user_age = await get_user_age_group(callback.from_user.id)

    if user_age not in ("teen", "student"):
        await callback.answer(
            "❌ Эта игра доступна только для 9–11 классов и студентов.\n"
            "Измените возраст в настройках профиля.",
            show_alert=True
        )
        return

    # Удаляем предыдущее сообщение меню игр
    try:
        await callback.message.delete()
    except:
        pass

    # Инициализируем состояние
    await state.update_data(
        scores=dict(engine.initial_scores),
        choices={},
        bonuses=0,
        branch=None,
        qid=None,
        next_step=None,
        next_qid=None,
        age_group=age_group,
        game_type="story"
    )
    await state.set_state(StoryGameStates.viewing_intro)

    # Показываем интро
    await callback.message.answer(
        engine.intro_text,
        reply_markup=story_next_kb()
    )
    await callback.answer()

# Обработчик "Далее"
@router.callback_query(F.data == "story_next")
async def story_next(callback: CallbackQuery, state: FSMContext):
    cur_state = await state.get_state()
    data = await state.get_data()

    # Удаляем клавиатуру у текущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    # 1. Просмотр интро → первый вопрос
    if cur_state == StoryGameStates.viewing_intro.state:
        await show_question(callback.message, state, "1")

    # 2. Просмотр результата
    elif cur_state == StoryGameStates.viewing_result.state:
        step = data.get("next_step", "question")

        if step == "checkpoint":
            sc = data["scores"]
            txt = f"📊 **Твои текущие баллы:**\n\n{engine.format_scores(sc)}"
            await state.set_state(StoryGameStates.viewing_checkpoint)
            await callback.message.answer(txt, reply_markup=story_next_kb(), parse_mode="Markdown")

        elif step == "finale":
            sc = data["scores"]
            fb = data.get("bonuses", 0)
            branch = engine.calculate_finale(sc, fb)
            await state.update_data(branch=branch)
            await show_question(callback.message, state, f"46{branch}")

        elif step == "epilogue":
            await state.set_state(StoryGameStates.viewing_epilogue)
            await callback.message.answer(engine.epilogue_text, reply_markup=story_next_kb())

        else:
            nq = data.get("next_qid")
            if nq:
                await show_question(callback.message, state, nq)

    # 3. Просмотр чекпоинта → следующий вопрос
    elif cur_state == StoryGameStates.viewing_checkpoint.state:
        nq = data.get("next_qid")
        if nq:
            await show_question(callback.message, state, nq)

    # 4. Просмотр эпилога → концовка
    elif cur_state == StoryGameStates.viewing_epilogue.state:
        sc = data["scores"]
        ending = engine.determine_ending(sc)
        txt = (
            f"🏆 **{ending['title']}**\n\n"
            f"📊 **Финальные баллы:**\n{engine.format_scores(sc)}\n\n"
            f"{ending['epilogue']}\n\n"
            f"💡 **Рекомендация:**\n{ending['recommendation']}"
        )
        await state.set_state(StoryGameStates.viewing_ending)
        await callback.message.answer(txt, reply_markup=story_end_kb(), parse_mode="Markdown")

    await callback.answer()

# Обработчик выбора варианта
@router.callback_query(StoryGameStates.answering, F.data.startswith("story_opt_"))
async def story_option(callback: CallbackQuery, state: FSMContext):
    label = callback.data.replace("story_opt_", "")
    data = await state.get_data()

    qid = data.get("qid")
    scores = data.get("scores", dict(engine.initial_scores))
    choices = data.get("choices", {})
    bonuses = data.get("bonuses", 0)
    branch = data.get("branch")

    q = engine.questions.get(qid)
    if not q:
        await callback.answer("⚠️ Вопрос не найден", show_alert=True)
        return

    opt = next((o for o in q["options"] if o["label"] == label), None)
    if not opt:
        await callback.answer("⚠️ Вариант не найден", show_alert=True)
        return

    # Проверка requirement (например, для вопроса 39)
    if not engine.check_requirement(opt, scores):
        await callback.answer(engine.requirement_text(opt), show_alert=True)
        return

    # Обработка выбора
    result = engine.process_choice(qid, label, scores, choices, bonuses)
    new_scores = result["scores"]
    result_text = result["result_text"]
    new_bonuses = result["finale_bonuses"]
    choices[qid] = label

    # Определяем следующий шаг
    nq = engine.next_qid(qid, branch)
    is_cp = engine.is_checkpoint(qid)

    if nq == "_FINALE_":
        next_step, next_qid = "finale", None
    elif nq == "_EPILOGUE_":
        next_step, next_qid = "epilogue", None
    elif is_cp:
        next_step, next_qid = "checkpoint", nq
    else:
        next_step, next_qid = "question", nq

    # Обновляем состояние
    await state.update_data(
        scores=new_scores,
        choices=choices,
        bonuses=new_bonuses,
        next_step=next_step,
        next_qid=next_qid
    )
    await state.set_state(StoryGameStates.viewing_result)

    # Показываем результат
    await callback.message.edit_text(
        result_text if result_text else "✅ Выбор сделан.",
        reply_markup=story_next_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик завершения игры (после концовки)
@router.callback_query(F.data == "story_end")
async def story_end(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    age_group = data.get("age_group")
    scores = data.get("scores", {})

    # Сохраняем результат в БД
    if scores:
        total_score = sum(scores.values())
        await save_game_result(
            user_id=callback.from_user.id,
            game_type="story",
            age_group=age_group,
            score=total_score,
            max_score=0,  # не применимо для сюжетной игры
            steps=0
        )

    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Показываем клавиатуру с действиями после игры
    await callback.message.answer(
        "🎮 **Игра завершена!**\n\nЧто дальше?",
        reply_markup=create_game_keyboard(age_group, "story"),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()

# Вспомогательная функция показа вопроса
async def show_question(msg: Message, state: FSMContext, qid: str):
    data = await state.get_data()
    scores = data.get("scores", dict(engine.initial_scores))
    choices = data.get("choices", {})
    branch = data.get("branch")

    q = engine.questions.get(qid)
    if not q:
        await msg.answer("⚠️ Вопрос не найден.")
        return

    # Обработка pre_condition (вопрос 28)
    pc = engine.check_pre_condition(qid, choices)
    if pc and pc.get("skip"):
        effects = pc.get("effects", {})
        sc = engine._apply(scores, effects)
        choices[qid] = "_SKIPPED_"

        txt_parts = [q["text"]]
        etxt = engine._fmt_effects(effects)
        if etxt:
            txt_parts.append(etxt)
        txt_parts.append(pc["text"])
        full_text = "\n\n".join(txt_parts)

        nq = engine.next_qid(qid, branch)
        is_cp = engine.is_checkpoint(qid)

        if nq == "_FINALE_":
            next_step, next_qid = "finale", None
        elif nq == "_EPILOGUE_":
            next_step, next_qid = "epilogue", None
        elif is_cp:
            next_step, next_qid = "checkpoint", nq
        else:
            next_step, next_qid = "question", nq

        await state.update_data(
            scores=sc, choices=choices, qid=qid,
            next_step=next_step, next_qid=next_qid
        )
        await state.set_state(StoryGameStates.viewing_result)
        await msg.answer(full_text, reply_markup=story_next_kb(), parse_mode="Markdown")
        return

    # Обработка auto_effects (для вопросов 46A/B/C)
    auto = q.get("auto_effects")
    auto_text = ""
    if auto:
        scores = engine._apply(scores, auto)
        auto_text = engine._fmt_effects(auto)
        await state.update_data(scores=scores)

    # Формируем текст вопроса
    display = engine.question_display(q)
    if auto_text:
        display = auto_text + "\n\n" + display

    await state.update_data(qid=qid)
    await state.set_state(StoryGameStates.answering)
    await msg.answer(display, reply_markup=story_options_kb(q["options"]), parse_mode="Markdown")