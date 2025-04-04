#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime

class Marketplace:
    def __init__(self, db, wallet):
        self.db = db
        self.wallet = wallet
        self.logger = logging.getLogger(__name__)
    
    def create_item(self, user_id, name, description, price):
        try:
            if price <= 0:
                return "Le prix doit u00eatre supu00e9rieur u00e0 zu00e9ro"
            
            if not name or len(name) < 3:
                return "Le nom de l'objet doit contenir au moins 3 caractu00e8res"
            
            if not description or len(description) < 5:
                return "La description doit contenir au moins 5 caractu00e8res"
            item_id = self.db.create_item(name, description, price, user_id)
            
            if item_id:
                self.logger.info(f"Objet {item_id} cru00e9u00e9 par l'utilisateur {user_id}")
                return f"Objet '{name}' cru00e9u00e9 avec succu00e8s et mis en vente u00e0 {price} CRYPTO"
            else:
                return "Erreur lors de la cru00e9ation de l'objet. Veuillez ru00e9essayer."
        except Exception as e:
            self.logger.error(f"Erreur lors de la cru00e9ation de l'objet: {str(e)}")
            return f"Erreur lors de la cru00e9ation de l'objet: {str(e)}"
    
    def get_available_items(self):
        try:
            items = self.db.get_available_items()
            return items
        except Exception as e:
            self.logger.error(f"Erreur lors de la ru00e9cupu00e9ration des objets: {str(e)}")
            return []
    
    def get_user_items(self, user_id):
        try:
            items = self.db.get_user_items(user_id)
            return items
        except Exception as e:
            self.logger.error(f"Erreur lors de la ru00e9cupu00e9ration des objets de l'utilisateur: {str(e)}")
            return []
    
    def buy_item(self, buyer_id, item_id):
        try:
            item = self.db.get_item(item_id)
            
            if not item:
                return "Objet non trouvé"
            
            if not item['for_sale']:
                return "Cet objet n'est plus disponible à la vente"
            
            if item['seller_id'] == buyer_id:
                return "Vous ne pouvez pas acheter votre propre objet"
            
            buyer_balance = self.wallet.get_balance(buyer_id)
            
            if buyer_balance < item['price']:
                return f"Solde insuffisant. Vous avez {buyer_balance} CRYPTO, mais l'objet coûte {item['price']} CRYPTO"
            success, message = self.db.buy_item(item_id, buyer_id)
            
            if success:
                self.logger.info(f"Objet {item_id} acheté par l'utilisateur {buyer_id}")
                return f"Félicitations! Vous avez acheté '{item['name']}' pour {item['price']} CRYPTO"
            else:
                return message
        except Exception as e:
            self.logger.error(f"Erreur lors de l'achat: {str(e)}")
            return f"Erreur lors de l'achat: {str(e)}"
    
    def cancel_sale(self, user_id, item_id):
        try:
            item = self.db.get_item(item_id)
            
            if not item:
                return "Objet non trouvé"
            
            if item['seller_id'] != user_id:
                return "Vous n'êtes pas le propriétaire de cet objet"
            
            if not item['for_sale']:
                return "Cet objet n'est pas en vente"
            
            self.db.cursor.execute(
                "UPDATE items SET for_sale = 0 WHERE id = ?",
                (item_id,)
            )
            self.db.conn.commit()
            
            self.logger.info(f"Vente de l'objet {item_id} annulée par l'utilisateur {user_id}")
            return f"La mise en vente de '{item['name']}' a été annulée"
        except Exception as e:
            self.logger.error(f"Erreur lors de l'annulation de la vente: {str(e)}")
            return f"Erreur lors de l'annulation de la vente: {str(e)}"
    
    def relist_item(self, user_id, item_id, price=None):
        try:
            item = self.db.get_item(item_id)
            
            if not item:
                return "Objet non trouvé"
            
            if item['seller_id'] != user_id:
                return "Vous n'êtes pas le propriétaire de cet objet"
            
            if item['for_sale']:
                return "Cet objet est déjà en vente"
            
            new_price = price if price is not None else item['price']
            
            if new_price <= 0:
                return "Le prix doit être supérieur à zéro"
            
            self.db.cursor.execute(
                "UPDATE items SET for_sale = 1, price = ? WHERE id = ?",
                (new_price, item_id)
            )
            self.db.conn.commit()
            
            self.logger.info(f"Objet {item_id} remis en vente par l'utilisateur {user_id}")
            return f"'{item['name']}' a été remis en vente à {new_price} CRYPTO"
        except Exception as e:
            self.logger.error(f"Erreur lors de la remise en vente: {str(e)}")
            return f"Erreur lors de la remise en vente: {str(e)}"
    
    def search_items(self, query):
        try:
            self.db.cursor.execute(
                "SELECT id, name, description, price, seller_id, for_sale "
                "FROM items WHERE (name LIKE ? OR description LIKE ?) AND for_sale = 1",
                (f"%{query}%", f"%{query}%")
            )
            results = self.db.cursor.fetchall()
            
            items = []
            for result in results:
                items.append({
                    'id': result[0],
                    'name': result[1],
                    'description': result[2],
                    'price': result[3],
                    'seller_id': result[4],
                    'for_sale': bool(result[5])
                })
            return items
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche d'objets: {str(e)}")
            return []
