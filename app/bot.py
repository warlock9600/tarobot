import asyncio
import logging
from datetime import datetime, time, timedelta, timezone
from random import choice

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select

from .config import settings
from .db import AsyncSessionLocal, init_db
from .models import Reading, User
from .locales.ru import (
    ARCANA,
    Arcana,
    BUTTON_TEXTS,
    DEFAULT_NAMES,
    GENDER_LABELS,
    GenderLiteral,
    MESSAGES,
    get_prediction,
)

log_level = logging.DEBUG if settings.debug else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

router = Dispatcher()


GENDER_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_TEXTS["male"], callback_data="gender:male")],
        [InlineKeyboardButton(text=BUTTON_TEXTS["female"], callback_data="gender:female")],
    ]
)

READING_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS["reading"], callback_data="reading"
            )
        ]
    ]
)


def _today_bounds() -> tuple[datetime, datetime]:
    today = datetime.now(timezone.utc).date()
    start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    logger.debug("Today bounds calculated: %s - %s", start, end)
    return start, end


def _display_name(user: User, telegram_user: types.User) -> str:
    if telegram_user.full_name:
        return telegram_user.full_name
    if telegram_user.username:
        return telegram_user.username
    if user.gender == "female":
        return DEFAULT_NAMES["female"]
    return DEFAULT_NAMES["male"]


async def _delete_message_after(message: types.Message, delay: int = 20) -> None:
    try:
        await asyncio.sleep(delay)
        await message.delete()
        logger.debug("Deleted service message %s", message.message_id)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to delete message %s: %s", message.message_id, exc)


async def _send_ephemeral(
    target: types.Message, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    sent = await target.answer(text, reply_markup=reply_markup)
    asyncio.create_task(_delete_message_after(sent))


async def _get_or_create_user(session, telegram_user: types.User) -> tuple[User, bool]:
    stmt = select(User).where(User.telegram_id == telegram_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    username = telegram_user.full_name or telegram_user.username

    if user is None:
        user = User(telegram_id=telegram_user.id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("Created user %s (%s)", telegram_user.id, username)
        return user, True

    updated = False
    if username and user.username != username:
        user.username = username
        updated = True
    if updated:
        await session.commit()
        await session.refresh(user)
        logger.debug("Updated username for user %s to %s", telegram_user.id, username)
    return user, False


async def _send_reading_prompt(message: types.Message) -> None:
    await message.answer(MESSAGES["reading_cta"], reply_markup=READING_KEYBOARD)


async def _count_today_readings(session, user_id: int) -> int:
    start, end = _today_bounds()
    stmt = (
        select(func.count(Reading.id))
        .where(Reading.user_id == user_id)
        .where(Reading.is_spontaneous.is_(False))
        .where(Reading.created_at >= start)
        .where(Reading.created_at < end)
    )
    result = await session.execute(stmt)
    count = int(result.scalar_one())
    logger.debug("User %s has %s readings today", user_id, count)
    return count


async def _record_reading(
    session, user: User, arcana: Arcana, prediction: str, is_spontaneous: bool = False
) -> None:
    reading = Reading(
        user_id=user.id,
        arcana=arcana.name,
        prediction=prediction,
        is_spontaneous=is_spontaneous,
    )
    session.add(reading)
    await session.commit()
    logger.info(
        "Recorded %s reading for user %s with arcana %s",
        "spontaneous" if is_spontaneous else "regular",
        user.id,
        arcana.name,
    )


async def _tarot_reading(user: User, gender: GenderLiteral) -> tuple[Arcana, str]:
    arcana = choice(ARCANA)
    prediction = get_prediction(arcana, gender)
    logger.info("Selected arcana %s for user %s", arcana.name, user.id)
    logger.debug(
        "Prediction for user %s (gender=%s): %s", user.id, gender, prediction
    )
    return arcana, prediction


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    async with AsyncSessionLocal() as session:
        user, created = await _get_or_create_user(session, message.from_user)
        logger.info("/start from user %s", message.from_user.id)

        if created:
            await message.answer(MESSAGES["greeting"], reply_markup=GENDER_KEYBOARD)
            return

        name = _display_name(user, message.from_user)
        if user.gender in {"male", "female"}:
            await message.answer(MESSAGES["welcome_back"].format(name=name))
            await _send_reading_prompt(message)
        else:
            await message.answer(
                MESSAGES["welcome_back_no_gender"].format(name=name),
                reply_markup=GENDER_KEYBOARD,
            )


@router.callback_query(F.data.startswith("gender:"))
async def set_gender(callback: types.CallbackQuery) -> None:
    gender = callback.data.split(":", maxsplit=1)[1]
    if gender not in {"male", "female"}:
        await callback.answer(MESSAGES["unknown_choice"])
        return

    async with AsyncSessionLocal() as session:
        user, _ = await _get_or_create_user(session, callback.from_user)
        user.gender = gender
        await session.commit()
        logger.info(
            "User %s set gender to %s", callback.from_user.id, gender
        )
        name = _display_name(user, callback.from_user)
        await _send_ephemeral(
            callback.message,
            MESSAGES["gender_saved"].format(
                name=name, gender=GENDER_LABELS[gender]
            ),
        )
        await callback.answer()
        await _send_reading_prompt(callback.message)


async def _ensure_gender_set(message: types.Message, user: User) -> bool:
    if user.gender in {"male", "female"}:
        return True
    logger.info("User %s requested reading without gender", user.id)
    await _send_ephemeral(message, MESSAGES["ask_gender"], reply_markup=GENDER_KEYBOARD)
    return False


async def _send_tarot(message: types.Message, actor: types.User | None = None) -> None:
    actor = actor or message.from_user
    if actor is None:
        logger.warning("Cannot send reading without user information for message %s", message.message_id)
        return

    async with AsyncSessionLocal() as session:
        user, _ = await _get_or_create_user(session, actor)
        logger.info("Sending reading to user %s", user.id)
        if not await _ensure_gender_set(message, user):
            return

        used = await _count_today_readings(session, user.id)
        if used >= 10:
            logger.info("User %s reached daily reading limit", user.id)
            await _send_ephemeral(message, MESSAGES["limit_reached"])
            return

        arcana, prediction = await _tarot_reading(user, user.gender)  # type: ignore[arg-type]
        await _record_reading(session, user, arcana, prediction)

        name = _display_name(user, actor)
        intro = MESSAGES["regular_intro"].format(name=name)
        text = (
            f"{intro}\n\n"
            f"{MESSAGES['arcana_label'].format(arcana=arcana.name)}\n"
            f"{MESSAGES['arcana_meaning'].format(description=arcana.description)}\n\n"
            f"{MESSAGES['prediction_label'].format(prediction=prediction)}"
        )
        await message.answer(text)


@router.callback_query(F.data == "reading")
async def reading(callback: types.CallbackQuery) -> None:
    logger.info("Reading request from user %s via inline button", callback.from_user.id)
    await _send_tarot(callback.message, actor=callback.from_user)
    await callback.answer()


async def main() -> None:
    logger.info("Starting bot (debug=%s)", settings.debug)
    await init_db()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    await router.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
