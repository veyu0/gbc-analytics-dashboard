import asyncio
import os
import logging
from typing import List, Optional

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotApp:
    """Telegram bot app using aiogram v3 that notifies about large orders from Supabase.

    Behavior:
    - Periodically queries `orders` table for orders with total_sum > threshold
    - Sends a message to configured chat IDs for each matching order
    """

    def __init__(self):
        # configuration
        self.telegram_token = os.environ.get("TELEGRAM_TOKEN")
        if not self.telegram_token:
            raise RuntimeError("Please set TELEGRAM_TOKEN environment variable")

        raw_targets = os.environ.get("TARGET_CHAT_IDS", "312311017")
        self.target_chat_ids: List[int] = []
        if raw_targets:
            for part in raw_targets.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    self.target_chat_ids.append(int(part))
                except ValueError:
                    logger.warning("Ignoring invalid TARGET_CHAT_ID: %s", part)

        admin_raw = os.environ.get("ADMIN_CHAT_ID")
        if admin_raw and not self.target_chat_ids:
            try:
                self.target_chat_ids = [int(admin_raw)]
            except ValueError:
                logger.warning("Invalid ADMIN_CHAT_ID: %s", admin_raw)

        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        if not (self.supabase_url and self.supabase_key):
            logger.warning("SUPABASE_URL or SUPABASE_KEY not set - Supabase access will fail")

        self.check_interval = int(os.environ.get("CHECK_INTERVAL_SECONDS", "300"))
        self.threshold = float(os.environ.get("ORDER_SUM_THRESHOLD", "50000"))

        # clients
        self.bot = Bot(token=self.telegram_token)
        self.dp = Dispatcher()

        # Supabase client (synchronous). We'll call it via to_thread when used in async code.
        if self.supabase_url and self.supabase_key:
            self.supabase: Optional[Client] = create_client(self.supabase_url, self.supabase_key)
        else:
            self.supabase = None

        # register handlers
        self.dp.message.register(self.cmd_start, Command(commands=["start"]))
        self.dp.message.register(self.cmd_check, Command(commands=["check"]))

    # --- data access ---
    async def fetch_large_orders(self) -> List[dict]:
        if not self.supabase:
            logger.warning("Supabase client not configured; fetch_large_orders will return empty list")
            return []

        try:
            resp = await asyncio.to_thread(
                self.supabase.table("orders").select("*").gt("total_sum", int(self.threshold)).execute
            )
        except Exception as e:
            logger.exception("Supabase query failed: %s", e)
            return []

        data = getattr(resp, "data", None)
        if not data:
            return []

        results: List[dict] = []
        for row in data:
            try:
                total = float(row.get("total_sum") or 0)
            except Exception:
                total = 0
            if total >= self.threshold:
                results.append(row)
        return results

    # --- formatting ---
    def format_order_message(self, order: dict) -> str:
        order_id = order.get("order_id") or order.get("id")
        number = order.get("number")
        customer = order.get("customer") or {}
        first_name = (
            order.get("first_name") or order.get("firstName") or customer.get("firstName") or ""
        )
        last_name = order.get("last_name") or order.get("lastName") or customer.get("lastName") or ""
        phone = order.get("phone") or (customer.get("phones") or "")
        email = order.get("email") or customer.get("email") or ""
        total = order.get("total_sum") or order.get("summ") or 0
        status = order.get("status") or ""
        created = order.get("created_at") or order.get("createdAt") or ""

        parts = [f"🚨 Большой заказ: {total}"]
        if number:
            parts.append(f"Номер: {number}")
        if order_id:
            parts.append(f"ID: {order_id}")
        if first_name or last_name:
            parts.append(f"Клиент: {first_name} {last_name}")
        if phone:
            parts.append(f"Телефон: {phone}")
        if email:
            parts.append(f"Email: {email}")
        if status:
            parts.append(f"Статус: {status}")
        if created:
            parts.append(f"Создан: {created}")

        site = order.get("site")
        slug = order.get("slug") or order.get("id")
        if site and slug:
            try:
                parts.append(f"Ссылка: https://{site}.retailcrm.ru/orders/{slug}")
            except Exception:
                pass

        return "\n".join(parts)

    # --- core logic ---
    async def check_and_notify(self, send_once: bool = False) -> Optional[int]:
        orders = await self.fetch_large_orders()
        sent = 0

        if not self.target_chat_ids:
            logger.warning("No target chat IDs configured; skipping send")
            if send_once:
                return 0
            return

        for order in orders:
            text = self.format_order_message(order)
            for target_id in self.target_chat_ids:
                try:
                    await self.bot.send_message(chat_id=target_id, text=text)
                    sent += 1
                except Exception as e:
                    logger.exception("Failed to send message to %s: %s", t, e)

        if send_once:
            return len(orders)

    # --- handlers ---
    async def cmd_start(self, message: Message):
        await message.reply(f"Привет! Я пришлю уведомление про заказы с суммой > {int(self.threshold)}")

    async def cmd_check(self, message: Message):
        await message.reply("Проверяю базу...")
        await self.check_and_notify()

    async def _main(self):
        try:
            # aiogram v3: start polling with bot
            await self.dp.start_polling(self.bot)
        finally:
            await self.bot.session.close()

    def run(self):
        asyncio.run(self._main())


def main():
    app = BotApp()
    app.run()


if __name__ == "__main__":
    main()
