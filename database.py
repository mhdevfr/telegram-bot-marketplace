#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os
import logging
from datetime import datetime

class Database:
    def __init__(self, db_name='marketplace.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger(__name__)
    
    def init_db(self):
        """Initialiser la base de données avec les tables nécessaires"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            
            # Création de la table des utilisateurs
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    joined_date TEXT NOT NULL,
                    last_active TEXT NOT NULL
                )
            ''')
            
            # Création de la table des wallets
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallets (
                    user_id INTEGER PRIMARY KEY,
                    address TEXT NOT NULL,
                    private_key TEXT NOT NULL,
                    balance REAL DEFAULT 0.0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Création de la table des objets
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price REAL NOT NULL,
                    seller_id INTEGER NOT NULL,
                    buyer_id INTEGER,
                    for_sale BOOLEAN DEFAULT 1,
                    created_date TEXT NOT NULL,
                    sold_date TEXT,
                    FOREIGN KEY (seller_id) REFERENCES users (id),
                    FOREIGN KEY (buyer_id) REFERENCES users (id)
                )
            ''')
            
            # Création de la table des transactions
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    transaction_type TEXT NOT NULL,
                    item_id INTEGER,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tx_hash TEXT,
                    FOREIGN KEY (sender_id) REFERENCES users (id),
                    FOREIGN KEY (receiver_id) REFERENCES users (id),
                    FOREIGN KEY (item_id) REFERENCES items (id)
                )
            ''')
            
            self.conn.commit()
            self.logger.info("Base de données initialisée avec succès")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
            if self.conn:
                self.conn.rollback()
            raise
    
    def close(self):
        """Fermer la connexion à la base de données"""
        if self.conn:
            self.conn.close()
    
    def user_exists(self, user_id):
        """Vérifier si un utilisateur existe dans la base de données"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            self.cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
            return bool(self.cursor.fetchone())
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de l'existence de l'utilisateur: {str(e)}")
            return False
    
    def create_user(self, user_id, username):
        """Créer un nouvel utilisateur"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            now = datetime.now().isoformat()
            self.cursor.execute(
                "INSERT INTO users (id, username, joined_date, last_active) VALUES (?, ?, ?, ?)",
                (user_id, username, now, now)
            )
            self.conn.commit()
            self.logger.info(f"Utilisateur {user_id} créé avec succès")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def update_user_activity(self, user_id):
        """Mettre à jour la dernière activité de l'utilisateur"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            now = datetime.now().isoformat()
            self.cursor.execute(
                "UPDATE users SET last_active = ? WHERE id = ?",
                (now, user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour de l'activité de l'utilisateur: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def create_wallet(self, user_id, address, private_key):
        """Créer un nouveau wallet pour un utilisateur"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            self.cursor.execute(
                "INSERT INTO wallets (user_id, address, private_key, balance) VALUES (?, ?, ?, ?)",
                (user_id, address, private_key, 0.0)
            )
            self.conn.commit()
            self.logger.info(f"Wallet créé pour l'utilisateur {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la création du wallet: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_wallet(self, user_id):
        """Obtenir les informations du wallet d'un utilisateur"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            self.cursor.execute(
                "SELECT address, private_key, balance FROM wallets WHERE user_id = ?",
                (user_id,)
            )
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'address': result[0],
                    'private_key': result[1],
                    'balance': result[2]
                }
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du wallet: {str(e)}")
            return None
    
    def update_balance(self, user_id, new_balance):
        """Mettre à jour le solde du wallet d'un utilisateur"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            self.cursor.execute(
                "UPDATE wallets SET balance = ? WHERE user_id = ?",
                (new_balance, user_id)
            )
            self.conn.commit()
            self.logger.info(f"Solde mis à jour pour l'utilisateur {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour du solde: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def create_item(self, name, description, price, seller_id):
        """Créer un nouvel objet à vendre"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            now = datetime.now().isoformat()
            self.cursor.execute(
                "INSERT INTO items (name, description, price, seller_id, for_sale, created_date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, description, price, seller_id, True, now)
            )
            self.conn.commit()
            item_id = self.cursor.lastrowid
            self.logger.info(f"Objet {item_id} créé avec succès")
            return item_id
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'objet: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return None
    
    def get_item(self, item_id):
        """Obtenir les informations d'un objet"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            self.cursor.execute(
                "SELECT id, name, description, price, seller_id, buyer_id, for_sale "
                "FROM items WHERE id = ?",
                (item_id,)
            )
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'description': result[2],
                    'price': result[3],
                    'seller_id': result[4],
                    'buyer_id': result[5],
                    'for_sale': bool(result[6])
                }
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de l'objet: {str(e)}")
            return None
    
    def get_available_items(self):
        """Obtenir tous les objets disponibles à la vente"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            self.cursor.execute(
                "SELECT id, name, description, price, seller_id "
                "FROM items WHERE for_sale = 1"
            )
            results = self.cursor.fetchall()
            
            items = []
            for result in results:
                items.append({
                    'id': result[0],
                    'name': result[1],
                    'description': result[2],
                    'price': result[3],
                    'seller_id': result[4]
                })
            return items
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des objets disponibles: {str(e)}")
            return []
    
    def get_user_items(self, user_id):
        """Obtenir tous les objets d'un utilisateur"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            self.cursor.execute(
                "SELECT id, name, description, price, for_sale "
                "FROM items WHERE seller_id = ? OR buyer_id = ?",
                (user_id, user_id)
            )
            results = self.cursor.fetchall()
            
            items = []
            for result in results:
                items.append({
                    'id': result[0],
                    'name': result[1],
                    'description': result[2],
                    'price': result[3],
                    'for_sale': bool(result[4])
                })
            return items
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des objets de l'utilisateur: {str(e)}")
            return []
    
    def buy_item(self, item_id, buyer_id):
        """Acheter un objet"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            # Vérifier si l'objet est disponible
            self.cursor.execute(
                "SELECT id, price, seller_id, for_sale FROM items WHERE id = ?",
                (item_id,)
            )
            result = self.cursor.fetchone()
            
            if not result:
                return False, "Objet non trouvé"
            
            if not result[3]:
                return False, "Cet objet n'est plus disponible à la vente"
            
            item_price = result[1]
            seller_id = result[2]
            
            # Vérifier le solde de l'acheteur
            self.cursor.execute(
                "SELECT balance FROM wallets WHERE user_id = ?",
                (buyer_id,)
            )
            buyer_balance = self.cursor.fetchone()
            
            if not buyer_balance or buyer_balance[0] < item_price:
                return False, "Solde insuffisant pour acheter cet objet"
            
            # Mettre à jour le solde de l'acheteur
            new_buyer_balance = buyer_balance[0] - item_price
            self.cursor.execute(
                "UPDATE wallets SET balance = ? WHERE user_id = ?",
                (new_buyer_balance, buyer_id)
            )
            
            # Mettre à jour le solde du vendeur
            self.cursor.execute(
                "SELECT balance FROM wallets WHERE user_id = ?",
                (seller_id,)
            )
            seller_balance = self.cursor.fetchone()[0]
            new_seller_balance = seller_balance + item_price
            self.cursor.execute(
                "UPDATE wallets SET balance = ? WHERE user_id = ?",
                (new_seller_balance, seller_id)
            )
            
            # Mettre à jour le statut de l'objet
            now = datetime.now().isoformat()
            self.cursor.execute(
                "UPDATE items SET buyer_id = ?, for_sale = 0, sold_date = ? WHERE id = ?",
                (buyer_id, now, item_id)
            )
            
            # Enregistrer la transaction
            self.cursor.execute(
                "INSERT INTO transactions (sender_id, receiver_id, amount, transaction_type, item_id, timestamp, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (buyer_id, seller_id, item_price, 'purchase', item_id, now, 'completed')
            )
            
            self.conn.commit()
            self.logger.info(f"Objet {item_id} acheté avec succès par l'utilisateur {buyer_id}")
            return True, "Achat réussi"
        except Exception as e:
            self.logger.error(f"Erreur lors de l'achat de l'objet: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False, f"Erreur lors de l'achat: {str(e)}"
    
    def record_transaction(self, sender_id, receiver_id, amount, transaction_type, status, tx_hash=None, item_id=None):
        """Enregistrer une transaction"""
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_name)
                self.cursor = self.conn.cursor()
            
            now = datetime.now().isoformat()
            self.cursor.execute(
                "INSERT INTO transactions (sender_id, receiver_id, amount, transaction_type, item_id, timestamp, status, tx_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (sender_id, receiver_id, amount, transaction_type, item_id, now, status, tx_hash)
            )
            self.conn.commit()
            transaction_id = self.cursor.lastrowid
            self.logger.info(f"Transaction {transaction_id} enregistrée avec succès")
            return transaction_id
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement de la transaction: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return None
