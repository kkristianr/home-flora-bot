import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from .charting import chart_png, chart_window
from .media import collect_images
from .mqtt_ingest import MqttIngestor
from .openplantbook import OpenPlantbookClient
from .plants import PlantRegistry
from .settings import Settings, load_settings
from .status import plant_card_lines
from .storage import Storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class PlantBot:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.storage = Storage(settings.db_path)
        self.registry = PlantRegistry(settings.plants_config)
        self.openplantbook = OpenPlantbookClient(
            settings.openplantbook_base_url,
            settings.openplantbook_api_key,
            self.storage,
        )

    def run(self) -> None:
        self.storage.init()
        MqttIngestor(self.settings, self.storage).start()
        app = Application.builder().token(self.settings.telegram_bot_token).build()
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("plants", self.plants_command))
        app.add_handler(CallbackQueryHandler(self.button_callback))
        logger.info("Plant bot started")
        app.run_polling()

    def allowed(self, update: Update) -> bool:
        return not self.settings.telegram_chat_id or str(update.effective_chat.id) == str(
            self.settings.telegram_chat_id
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.allowed(update):
            return
        await update.message.reply_text("Use /plants to list plants.")

    async def plants_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.allowed(update):
            return
        keyboard = [
            [InlineKeyboardButton(plant.name, callback_data=f"plant:{plant.slug}")] for plant in self.registry.all()
        ]
        await update.message.reply_text("Plants", reply_markup=InlineKeyboardMarkup(keyboard))

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.allowed(update):
            return
        query = update.callback_query
        await query.answer()
        parts = query.data.split(":")
        action = parts[0]
        if action == "plant":
            slug = parts[1]
            await self.send_plant_detail(query, slug)
        elif action == "chart":
            window_key, slug = parts[1], parts[2]
            await self.send_chart(query, slug, window_key)

    async def send_plant_detail(self, query, slug: str) -> None:
        plant = self.registry.get(slug)
        detail = self.openplantbook.detail(plant.plant_id)
        for image_url in collect_images(detail)[:5]:
            try:
                await query.message.reply_photo(image_url)
            except Exception as exc:
                logger.warning("Could not send image %s: %s", image_url, exc)

        latest = self.storage.latest_reading(slug)
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("1h", callback_data=f"chart:1h:{slug}"),
                    InlineKeyboardButton("24h", callback_data=f"chart:24h:{slug}"),
                    InlineKeyboardButton("7d", callback_data=f"chart:7d:{slug}"),
                ]
            ]
        )
        await query.message.reply_text(
            "\n".join(plant_card_lines(plant, detail, latest)),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    async def send_chart(self, query, slug: str, window_key: str) -> None:
        plant = self.registry.get(slug)
        detail = self.openplantbook.detail(plant.plant_id)
        window = chart_window(window_key)
        image = chart_png(self.storage, slug, detail, window)
        if image is None:
            await query.message.reply_text(f"No readings for the last {window.label} yet.")
            return
        await query.message.reply_photo(
            InputFile(image, filename=f"{slug}-{window.key}.png"),
            caption=f"Last {window.label}",
        )


def main() -> None:
    PlantBot(load_settings()).run()
