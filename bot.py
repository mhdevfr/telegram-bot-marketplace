#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import pytz
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

from database import Database
from wallet import Wallet
from marketplace import Marketplace

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TELEGRAM_BOT_TOKEN = '7639355958:AAG0atADKj_ORIltwrGBt3F556GgtWnzUK4'  # Remplacez par votre nouveau token

db = Database()
wallet = Wallet()
wallet.set_db(db)
marketplace = Marketplace(db, wallet)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    if not db.user_exists(user_id):
        db.create_user(user_id, user.username or "Anonymous")
        wallet.create_wallet(user_id)
        await update.message.reply_text(
            f"Bienvenue {user.first_name}! Votre compte a été créé avec succès."
            f"\nVotre ID unique: {user_id}"
            f"\nUtilisez /help pour voir toutes les commandes disponibles."
        )
    else:
        await update.message.reply_text(
            f"Rebonjour {user.first_name}!"
            f"\nVotre ID unique: {user_id}"
            f"\nUtilisez /help pour voir toutes les commandes disponibles."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de la commande /help"""
    help_text = (
        "Commandes disponibles:\n"
        "/start - Du00e9marrer le bot et cru00e9er un compte\n"
        "/help - Afficher ce message d'aide\n"
        "/wallet - Gu00e9rer votre portefeuille crypto\n"
        "/deposit - Du00e9poser des fonds dans votre portefeuille\n"
        "/withdraw - Retirer des fonds de votre portefeuille\n"
        "/balance - Vu00e9rifier votre solde\n"
        "/market - Accu00e9der u00e0 la marketplace\n"
        "/buy - Acheter un objet\n"
        "/sell - Vendre un objet\n"
        "/myitems - Voir vos objets\n"
    )
    await update.message.reply_text(help_text)

async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de la commande /wallet"""
    user_id = update.effective_user.id
    
    # Vu00e9rifier si l'utilisateur existe
    if not db.user_exists(user_id):
        await update.message.reply_text("Veuillez d'abord utiliser /start pour créer un compte.")
        return
    
    keyboard = [
        [InlineKeyboardButton("Du00e9poser", callback_data="deposit")],
        [InlineKeyboardButton("Retirer", callback_data="withdraw")],
        [InlineKeyboardButton("Voir le solde", callback_data="balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Gestion de votre portefeuille:", reply_markup=reply_markup)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de la commande /balance"""
    user_id = update.effective_user.id
    
    # Vu00e9rifier si l'utilisateur existe
    if not db.user_exists(user_id):
        await update.message.reply_text("Veuillez d'abord utiliser /start pour créer un compte.")
        return
    
    balance = wallet.get_balance(user_id)
    await update.message.reply_text(f"Votre solde actuel est de: {balance} CRYPTO")

async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de la commande /market"""
    user_id = update.effective_user.id
    
    # Vu00e9rifier si l'utilisateur existe
    if not db.user_exists(user_id):
        await update.message.reply_text("Veuillez d'abord utiliser /start pour créer un compte.")
        return
    
    items = marketplace.get_available_items()
    if not items:
        await update.message.reply_text("Aucun objet n'est actuellement disponible sur la marketplace.")
        return
    
    message = "Objets disponibles sur la marketplace:\n\n"
    keyboard = []
    
    for item in items:
        message += f"ID: {item['id']} - {item['name']} - Prix: {item['price']} CRYPTO\n"
        keyboard.append([InlineKeyboardButton(f"Acheter {item['name']}", callback_data=f"buy_{item['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de la commande /buy"""
    user_id = update.effective_user.id
    
    # Vu00e9rifier si l'utilisateur existe
    if not db.user_exists(user_id):
        await update.message.reply_text("Veuillez d'abord utiliser /start pour créer un compte.")
        return
    
    args = context.args
    if not args or len(args) < 1:
        await update.message.reply_text("Veuillez spécifier l'ID de l'objet à acheter. Exemple: /buy 1")
        return
    
    try:
        item_id = int(args[0])
        result = marketplace.buy_item(user_id, item_id)
        await update.message.reply_text(result)
    except ValueError:
        await update.message.reply_text("L'ID de l'objet doit être un nombre.")
    except Exception as e:
        await update.message.reply_text(f"Une erreur s'est produite: {str(e)}")

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de la commande /sell"""
    user_id = update.effective_user.id
    
    # Vu00e9rifier si l'utilisateur existe
    if not db.user_exists(user_id):
        await update.message.reply_text("Veuillez d'abord utiliser /start pour créer un compte.")
        return
    
    await update.message.reply_text(
        "Pour vendre un objet, veuillez fournir les informations suivantes:\n"
        "Nom, description, prix en CRYPTO.\n"
        "Exemple: /sell Epée magique, Une épée aux pouvoirs extraordinaires, 100"
    )
    
    args = context.args
    if not args or len(args) < 3:
        return
    
    # Extraction des informations de l'objet
    item_data = ' '.join(args).split(',')
    if len(item_data) < 3:
        await update.message.reply_text("Format incorrect. Utilisez: Nom, Description, Prix")
        return
    
    name = item_data[0].strip()
    description = item_data[1].strip()
    
    try:
        price = float(item_data[2].strip())
        result = marketplace.create_item(user_id, name, description, price)
        await update.message.reply_text(result)
    except ValueError:
        await update.message.reply_text("Le prix doit être un nombre.")
    except Exception as e:
        await update.message.reply_text(f"Une erreur s'est produite: {str(e)}")

async def myitems_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de la commande /myitems"""
    user_id = update.effective_user.id
    
    # Vu00e9rifier si l'utilisateur existe
    if not db.user_exists(user_id):
        await update.message.reply_text("Veuillez d'abord utiliser /start pour créer un compte.")
        return
    
    items = marketplace.get_user_items(user_id)
    if not items:
        await update.message.reply_text("Vous ne possédez aucun objet.")
        return
    
    message = "Vos objets:\n\n"
    for item in items:
        status = "En vente" if item["for_sale"] else "Non en vente"
        message += f"ID: {item['id']} - {item['name']} - Prix: {item['price']} CRYPTO - Statut: {status}\n"
    
    await update.message.reply_text(message)

async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de la commande /deposit"""
    user_id = update.effective_user.id
    
    # Vu00e9rifier si l'utilisateur existe
    if not db.user_exists(user_id):
        await update.message.reply_text("Veuillez d'abord utiliser /start pour créer un compte.")
        return
    
    wallet_address = wallet.get_wallet_address(user_id)
    await update.message.reply_text(
        f"Pour déposer des fonds, veuillez envoyer vos cryptomonnaies à l'adresse suivante:\n\n"
        f"`{wallet_address}`\n\n"
        f"Les fonds seront crédités sur votre compte après confirmation du réseau (environ 10-30 minutes).",
        parse_mode='Markdown'
    )

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("Veuillez d'abord utiliser /start pour créer un compte.")
        return
    
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "Pour retirer des fonds, utilisez la commande suivante:\n"
            "/withdraw [adresse] [montant]\n"
            "Exemple: /withdraw 0x1234567890abcdef 100"
        )
        return
    
    address = args[0]
    try:
        amount = float(args[1])
        result = wallet.withdraw(user_id, address, amount)
        await update.message.reply_text(result)
    except ValueError:
        await update.message.reply_text("Le montant doit u00eatre un nombre.")
    except Exception as e:
        await update.message.reply_text(f"Une erreur s'est produite: {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "deposit":
        wallet_address = wallet.get_wallet_address(user_id)
        await query.edit_message_text(
            f"Pour du00e9poser des fonds, veuillez envoyer vos cryptomonnaies u00e0 l'adresse suivante:\n\n"
            f"`{wallet_address}`\n\n"
            f"Les fonds seront cru00e9ditu00e9s sur votre compte apru00e8s confirmation du ru00e9seau.",
            parse_mode='Markdown'
        )
    elif data == "withdraw":
        await query.edit_message_text(
            "Pour retirer des fonds, utilisez la commande:\n"
            "/withdraw [adresse] [montant]\n"
            "Exemple: /withdraw 0x1234567890abcdef 100"
        )
    elif data == "balance":
        balance = wallet.get_balance(user_id)
        await query.edit_message_text(f"Votre solde actuel est de: {balance} CRYPTO")
    elif data.startswith("buy_"):
        try:
            item_id = int(data.split("_")[1])
            result = marketplace.buy_item(user_id, item_id)
            await query.edit_message_text(result)
        except Exception as e:
            await query.edit_message_text(f"Une erreur s'est produite: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    error_msg = str(context.error)
    logger.error(f"Erreur détaillée: {error_msg}")
    
    try:
        if "Conflict" in error_msg:
            await update.message.reply_text("Erreur: Une autre instance du bot est en cours d'exécution. Arrêtez les autres instances ou utilisez un nouveau token.")
        else:
            await update.message.reply_text(f"Une erreur s'est produite: {error_msg}. Veuillez réessayer.")
    except Exception as e:
        logger.error(f"Impossible d'envoyer le message d'erreur: {e}")

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN non défini dans le fichier .env")
        return
    
    db.init_db()
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("wallet", wallet_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("market", market_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("sell", sell_command))
    application.add_handler(CommandHandler("myitems", myitems_command))
    application.add_handler(CommandHandler("deposit", deposit_command))
    application.add_handler(CommandHandler("withdraw", withdraw_command))
    
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.add_error_handler(error_handler)
    
    logger.info("Bot démarré")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
