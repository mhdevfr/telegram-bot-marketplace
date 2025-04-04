#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import secrets
import hashlib
from dotenv import load_dotenv
from web3 import Web3
from cryptography.fernet import Fernet

load_dotenv()
BLOCKCHAIN_API_KEY = os.getenv('BLOCKCHAIN_API_KEY')

class Wallet:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_key = Fernet.generate_key() if not os.getenv('ENCRYPTION_KEY') else os.getenv('ENCRYPTION_KEY').encode()
        self.cipher_suite = Fernet(self.encryption_key)
        
        self.w3 = None
        try:
            if BLOCKCHAIN_API_KEY:
                self.w3 = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{BLOCKCHAIN_API_KEY}"))
                self.logger.info("Connexion u00e0 la blockchain u00e9tablie")
        except Exception as e:
            self.logger.warning(f"Impossible de se connecter u00e0 la blockchain: {str(e)}")
            self.logger.info("Fonctionnement en mode simulation")
        
        self.db = None
    
    def set_db(self, db):
        self.db = db
    
    def create_wallet(self, user_id):
        try:
            private_key = self._generate_private_key()
            address = self._generate_address_from_private_key(private_key)
            
            encrypted_private_key = self._encrypt_private_key(private_key)
            
            if self.db:
                success = self.db.create_wallet(user_id, address, encrypted_private_key.decode())
                if success:
                    self.logger.info(f"Wallet cru00e9u00e9 pour l'utilisateur {user_id}")
                    return address
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la cru00e9ation du wallet: {str(e)}")
            return None
    
    def get_wallet_address(self, user_id):
        try:
            if self.db:
                wallet_info = self.db.get_wallet(user_id)
                if wallet_info:
                    return wallet_info['address']
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la ru00e9cupu00e9ration de l'adresse du wallet: {str(e)}")
            return None
    
    def get_balance(self, user_id):
        try:
            if self.db:
                wallet_info = self.db.get_wallet(user_id)
                if wallet_info:
                    return wallet_info['balance']
            return 0.0
        except Exception as e:
            self.logger.error(f"Erreur lors de la ru00e9cupu00e9ration du solde: {str(e)}")
            return 0.0
    
    def deposit(self, user_id, amount, tx_hash=None):
        try:
            if self.db:
                current_balance = self.get_balance(user_id)
                new_balance = current_balance + amount
                success = self.db.update_balance(user_id, new_balance)
                
                if success:
                    self.db.record_transaction(
                        sender_id=0,  
                        receiver_id=user_id,
                        amount=amount,
                        transaction_type='deposit',
                        status='completed',
                        tx_hash=tx_hash
                    )
                    self.logger.info(f"Du00e9pu00f4t de {amount} effectuu00e9 pour l'utilisateur {user_id}")
                    return f"Du00e9pu00f4t de {amount} CRYPTO effectuu00e9 avec succu00e8s. Nouveau solde: {new_balance} CRYPTO"
            return "Erreur lors du du00e9pu00f4t. Veuillez ru00e9essayer."
        except Exception as e:
            self.logger.error(f"Erreur lors du du00e9pu00f4t: {str(e)}")
            return f"Erreur lors du du00e9pu00f4t: {str(e)}"
    
    def withdraw(self, user_id, to_address, amount):
        try:
            if self.db:
                current_balance = self.get_balance(user_id)
                
                if current_balance < amount:
                    return "Solde insuffisant pour effectuer ce retrait"
                
                new_balance = current_balance - amount
                success = self.db.update_balance(user_id, new_balance)
                
                if success:
                    tx_hash = self._generate_tx_hash()  
                    self.db.record_transaction(
                        sender_id=user_id,
                        receiver_id=0,  
                        amount=amount,
                        transaction_type='withdrawal',
                        status='completed',
                        tx_hash=tx_hash
                    )
                    self.logger.info(f"Retrait de {amount} effectuu00e9 par l'utilisateur {user_id}")
                    return f"Retrait de {amount} CRYPTO effectuu00e9 avec succu00e8s vers {to_address}. Nouveau solde: {new_balance} CRYPTO"
            return "Erreur lors du retrait. Veuillez ru00e9essayer."
        except Exception as e:
            self.logger.error(f"Erreur lors du retrait: {str(e)}")
            return f"Erreur lors du retrait: {str(e)}"
    
    def transfer(self, from_user_id, to_user_id, amount):
        try:
            if self.db:
                sender_balance = self.get_balance(from_user_id)
                
                if sender_balance < amount:
                    return False, "Solde insuffisant pour effectuer ce transfert"
                
                new_sender_balance = sender_balance - amount
                self.db.update_balance(from_user_id, new_sender_balance)
                
                receiver_balance = self.get_balance(to_user_id)
                new_receiver_balance = receiver_balance + amount
                self.db.update_balance(to_user_id, new_receiver_balance)
                tx_hash = self._generate_tx_hash()  
                self.db.record_transaction(
                    sender_id=from_user_id,
                    receiver_id=to_user_id,
                    amount=amount,
                    transaction_type='transfer',
                    status='completed',
                    tx_hash=tx_hash
                )
                
                self.logger.info(f"Transfert de {amount} de {from_user_id} vers {to_user_id}")
                return True, f"Transfert de {amount} CRYPTO effectuu00e9 avec succu00e8s. Nouveau solde: {new_sender_balance} CRYPTO"
            return False, "Erreur lors du transfert. Veuillez ru00e9essayer."
        except Exception as e:
            self.logger.error(f"Erreur lors du transfert: {str(e)}")
            return False, f"Erreur lors du transfert: {str(e)}"
    
    def _generate_private_key(self):
        return secrets.token_hex(32)
    
    def _generate_address_from_private_key(self, private_key):
        h = hashlib.sha256(private_key.encode()).hexdigest()
        return f"0x{h[-40:]}"
    
    def _encrypt_private_key(self, private_key):
        return self.cipher_suite.encrypt(private_key.encode())
    
    def _decrypt_private_key(self, encrypted_private_key):
        if isinstance(encrypted_private_key, str):
            encrypted_private_key = encrypted_private_key.encode()
        return self.cipher_suite.decrypt(encrypted_private_key).decode()
    
    def _generate_tx_hash(self):
        return f"0x{secrets.token_hex(32)}"
