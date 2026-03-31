import json
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, delete

from database import AsyncSessionLocal
from models import User, StorySave
from data.story_engine import GameEngine
from keyboards.story_kb import story_next_kb, story_end_kb
from keyboards.main_menu_kb import get_main_kb
from handlers.games.utils import save_game_result, create_game_keyboard
from services.analytics import log_activity

logger = logging.getLogger(__name__)
router = Router()

class StoryGameStates(StatesGroup):
    viewing_intro = State()
    answering = State()
    viewing_result = State()
    viewing_checkpoint = State()
    viewing_epilogue = State()
    viewing_ending = State()

engine = GameEngine("data/scenario.json")

async def get_user_age_group(user_id: int) -> str | None:
    async with AsyncSessionLocal() as session:
        stmt = select(User.age_group).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar()

async def save_game_progress(user_id: int, state_data: dict) -> bool:
    try:
        save_data = {
            "scores": state_data.get("scores", {}),
            "choices": state_data.get("choices", {}),
            "bonuses": state_data.get("bonuses", 0),
            "branch": state_data.get("branch"),
            "qid": state_data.get("qid"),
            "next_step": state_data.get("next_step"),
            "next_qid": state_data.get("next_qid"),
            "age_group": state_data.get("age_group"),
            "game_type": state_data.get("game_type"),
            "state": state_data.get("state"),
        }
        async with AsyncSessionLocal() as session:
            stmt = select(StorySave).where(StorySave.user_id == user_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.save_data = json.dumps(save_data, ensure_ascii=False)
                existing.updated_at = datetime.utcnow()
            else:
                new_save = StorySave(
                    user_id=user_id,
                    save_data=json.dumps(save_data, ensure_ascii=False)
                )
                session.add(new_save)
            await session.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка сохранения прогресса: {e}")
        return False

async def load_game_progress(user_id: int) -> dict | None:
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(StorySave).where(StorySave.user_id == user_id)
            result = await session.execute(stmt)
            save = result.scalar_one_or_none()
            if save and save.save_data:
                return json.loads(save.save_data)
    except Exception as e:
        logger.error(f"Ошибка загрузки сохранения: {e}")
    return None

async def delete_game_progress(user_id: int) -> bool:
    try:
        async with AsyncSessionLocal() as session:
            stmt = delete(StorySave).where(StorySave.user_id == user_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"Ошибка удаления сохранения: {e}")
        return False

async def start_new_story_game(callback: CallbackQuery, state: FSMContext, age_group: str):
    try:
        await callback.message.delete()
    except:
        pass

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
    await callback.message.answer(
        engine.intro_text,
        reply_markup=story_next_kb()
    )
    await callback.answer()

# Основной обработчик запуска
@router.callback_query(F.data == "game_story")
async def start_story_game(callback: CallbackQuery, state: FSMContext):
    """Запуск сюжетной игры – доступен всем"""
    # Логирование запуска игры
    await log_activity(
        user_id=callback.from_user.id,
        action="game",
        target_id=None,
        details="story"
    )

    # Проверяем наличие сохранения
    saved_data = await load_game_progress(callback.from_user.id)
    if saved_data:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="▶️ Продолжить", callback_data="story_continue"),
            InlineKeyboardButton(text="🔄 Начать заново", callback_data="story_new")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Выйти в меню", callback_data="back_main_menu")
        )
        await callback.message.answer(
            "📀 **Найдено сохранение!**\n\n"
            "Хотите продолжить игру с того места, где остановились?",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return

    # Если сохранения нет, определяем возраст (используется только для статистики)
    user_age = await get_user_age_group(callback.from_user.id) or "teen"
    await start_new_story_game(callback, state, user_age)

# Остальные обработчики (story_next, story_option и т.д.) остаются без изменений
# Они приведены ниже для полноты, но вы можете оставить свои, если они работают.

@router.callback_query(F.data == "story_next")
async def story_next(callback: CallbackQuery, state: FSMContext):
    cur_state = await state.get_state()
    data = await state.get_data()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    if cur_state == StoryGameStates.viewing_intro.state:
        await show_question(callback.message, state, "1")
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
    elif cur_state == StoryGameStates.viewing_checkpoint.state:
        nq = data.get("next_qid")
        if nq:
            await show_question(callback.message, state, nq)
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

    if not engine.check_requirement(opt, scores):
        await callback.answer(engine.requirement_text(opt), show_alert=True)
        return

    result = engine.process_choice(qid, label, scores, choices, bonuses)
    new_scores = result["scores"]
    result_text = result["result_text"]
    new_bonuses = result["finale_bonuses"]
    choices[qid] = label

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
        scores=new_scores,
        choices=choices,
        bonuses=new_bonuses,
        next_step=next_step,
        next_qid=next_qid
    )
    await state.set_state(StoryGameStates.viewing_result)

    await callback.message.edit_text(
        result_text if result_text else "✅ Выбор сделан.",
        reply_markup=story_next_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "story_end")
async def story_end(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    age_group = data.get("age_group")
    scores = data.get("scores", {})

    if scores:
        total_score = sum(scores.values())
        await save_game_result(
            user_id=callback.from_user.id,
            game_type="story",
            age_group=age_group,
            score=total_score,
            max_score=0,
            steps=0
        )

    await delete_game_progress(callback.from_user.id)

    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "🎮 **Игра завершена!**\n\nЧто дальше?",
        reply_markup=create_game_keyboard(age_group, "story"),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "story_show_stats")
async def show_stats(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    scores = data.get("scores", {})
    if scores:
        text = f"📊 **Текущие баллы:**\n\n{engine.format_scores(scores)}"
    else:
        text = "📊 Статы пока не накоплены."
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "story_save")
async def save_progress(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["state"] = await state.get_state()
    if await save_game_progress(callback.from_user.id, data):
        await callback.answer("💾 Прогресс сохранён!", show_alert=True)
    else:
        await callback.answer("❌ Ошибка сохранения", show_alert=True)

@router.callback_query(F.data == "story_quit")
async def quit_game(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["state"] = await state.get_state()
    await save_game_progress(callback.from_user.id, data)
    await state.clear()
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "🎮 **Игра сохранена!**\n\nЧтобы продолжить, выберите 'Сюжетная игра' в меню.",
        reply_markup=get_main_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "story_continue")
async def continue_game(callback: CallbackQuery, state: FSMContext):
    saved_data = await load_game_progress(callback.from_user.id)
    if not saved_data:
        await callback.answer("❌ Нет сохранённой игры", show_alert=True)
        return
    await state.update_data(saved_data)
    saved_state = saved_data.get("state")
    if saved_state:
        await state.set_state(saved_state)
    qid = saved_data.get("qid")
    current_state = await state.get_state()
    if qid and (current_state == StoryGameStates.answering.state or current_state == StoryGameStates.viewing_result.state):
        await show_question(callback.message, state, qid)
    else:
        await callback.message.answer(
            "📖 **Продолжаем игру**\n\nНажмите 'Далее', чтобы продолжить с того же места.",
            reply_markup=story_next_kb()
        )
    await callback.answer()

@router.callback_query(F.data == "story_new")
async def new_game(callback: CallbackQuery, state: FSMContext):
    await delete_game_progress(callback.from_user.id)
    await state.clear()
    user_age = await get_user_age_group(callback.from_user.id) or "teen"
    await start_new_story_game(callback, state, user_age)
    await callback.answer()

@router.callback_query(F.data == "story_delete_save")
async def delete_save(callback: CallbackQuery, state: FSMContext):
    if await delete_game_progress(callback.from_user.id):
        await callback.answer("🗑️ Сохранение удалено", show_alert=True)
    else:
        await callback.answer("❌ Не найдено сохранение", show_alert=True)

async def show_question(msg: Message, state: FSMContext, qid: str):
    data = await state.get_data()
    scores = data.get("scores", dict(engine.initial_scores))
    choices = data.get("choices", {})
    branch = data.get("branch")

    q = engine.questions.get(qid)
    if not q:
        await msg.answer("⚠️ Вопрос не найден.")
        return

    # pre_condition
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

    # auto_effects
    auto = q.get("auto_effects")
    auto_text = ""
    if auto:
        scores = engine._apply(scores, auto)
        auto_text = engine._fmt_effects(auto)
        await state.update_data(scores=scores)

    display = engine.question_display(q)
    if auto_text:
        display = auto_text + "\n\n" + display

    await state.update_data(qid=qid)
    await state.set_state(StoryGameStates.answering)

    builder = InlineKeyboardBuilder()
    for opt in q["options"]:
        builder.add(InlineKeyboardButton(
            text=f"{opt['label']}) {opt['text'][:50]}...",
            callback_data=f"story_opt_{opt['label']}"
        ))
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="💾 Сохранить", callback_data="story_save"),
        InlineKeyboardButton(text="🚪 Выйти", callback_data="story_quit")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="story_show_stats")
    )

    await msg.answer(display, reply_markup=builder.as_markup(), parse_mode="Markdown")