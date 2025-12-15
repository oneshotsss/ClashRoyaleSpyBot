from config import telegram_token
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters
import string
import random

lobbies = {}
players = {}
CARDS = [
    "Meganite", "Peka", "Hog", "Meganite Evolution"
]

async def unknown_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Unknown command")

async def unknown_message(update: Update, context: CallbackContext):
    await update.message.reply_text("Unrecognized message")

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Hello! I am a game bot. Use /help to see available commands."
    )

async def help(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "/start - start the bot\n"
        "/help - show this help message\n"
        "/create - create a new lobby\n"
        "/join - join an existing lobby\n"
        "/end - end the lobby\n"
        "/players - list players in a lobby\n"
        "Please follow the rules and have fun!"
    )

async def create(update: Update, context: CallbackContext):
    user = update.effective_user

    code_length = 4
    chars = string.ascii_letters + string.digits
    chars = chars.upper()
    code = ''.join(random.choice(chars) for _ in range(code_length))

    lobbies[code] = {
        "owner": user.id,
        "players": {
            user.id: user.username or user.first_name
        },
        "active": True,
        "card": None,
        "spy": None
    }

    await update.message.reply_text(
        f"Lobby created!\n"
        f"Code: `{code}`\n"
        f"Share this code with other players: /join {code}",
        parse_mode="Markdown"
    )

async def join(update: Update, context: CallbackContext):
    user = update.effective_user

    if len(context.args) == 0:
        await update.message.reply_text("Please provide a lobby code")
        return

    code = context.args[0].upper()

    if code not in lobbies:
        await update.message.reply_text("Lobby not found")
        return

    lobby = lobbies[code]

    if not lobby["active"]:
        await update.message.reply_text("This lobby is no longer active")
        return

    if user.id not in lobby["players"]:
        lobby["players"][user.id] = user.username or user.first_name

    await update.message.reply_text("You have joined the lobby")
    await players_list(update, context, code)

async def players_list(update: Update, context: CallbackContext, code: str = None):
    if code is None:
        if len(context.args) == 0:
            await update.message.reply_text("Please provide a lobby code: /players CODE")
            return
        code = context.args[0].upper()

    if code not in lobbies:
        await update.message.reply_text("Lobby not found")
        return

    lobby = lobbies[code]

    if not lobby["players"]:
        await update.message.reply_text("No players in the lobby yet")
        return

    text = f"Players in lobby {code}:\n"
    for i, name in enumerate(lobby["players"].values(), start=1):
        text += f"{i}. @{name}\n"

    await update.message.reply_text(text)

async def end(update: Update, context: CallbackContext):
    user = update.effective_user

    if len(context.args) == 0:
        await update.message.reply_text("Please provide a lobby code: /end CODE")
        return

    code = context.args[0].upper()

    if code not in lobbies:
        await update.message.reply_text("Lobby not found")
        return

    lobby = lobbies[code]

    if lobby["owner"] != user.id:
        await update.message.reply_text("You are not the owner of this lobby")
        return

    lobby["active"] = False
    await update.message.reply_text(f"Lobby {code} has been ended")

    lobby["players"].clear()
    del lobbies[code]

def assign_roles(lobby):
    lobby["location"] = random.choice(CARDS)
    lobby["spy"] = random.choice(list(lobby["players"].keys()))

    roles = {}
    for user_id in lobby["players"]:
        if user_id == lobby["spy"]:
            roles[user_id] = "Spy"
        else:
            roles[user_id] = lobby["location"]
    return roles

async def start_game(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a lobby code: /game CODE")
        return

    code = context.args[0].upper()
    if code not in lobbies:
        await update.message.reply_text("Lobby not found")
        return

    lobby = lobbies[code]
    roles = assign_roles(lobby)

    for user_id, role in roles.items():
        await context.bot.send_message(chat_id=user_id, text=f"Your role: {role}")

    await update.message.reply_text("Roles have been assigned!")

app = ApplicationBuilder().token(telegram_token).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("create", create))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("players", players_list))
app.add_handler(CommandHandler("end", end))
app.add_handler(CommandHandler("game", start_game))
app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
app.add_handler(MessageHandler(filters.TEXT, unknown_message))
app.run_polling()
