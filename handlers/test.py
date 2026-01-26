# Временный код в хендлере
@dp.message()
async def get_chat_id(message: Message):
    await message.answer(f"ID этого чата: `{message.chat.id}`", parse_mode="Markdown")