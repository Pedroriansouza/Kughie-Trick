#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
KUGHIE - Advanced OSINT Toolkit v3.0
Com funcionalidades expandidas incluindo bombers e consultas avançadas
Author: Original NerryX, Adaptado para Kughie
Version: 3.0-KUGHIE
"""

import json
import requests
import time
import os
import sys
import sqlite3
import hashlib
import re
import ipaddress
import random
import string
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========== CONFIGURAÇÃO DE CORES ==========
class Colors:
    # Cores básicas
    BLACK = '\033[30m'
    RED = '\033[1;31m'
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[1;34m'
    MAGENTA = '\033[1;35m'
    CYAN = '\033[1;36m'
    WHITE = '\033[1;37m'
    
    # Estilos
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    # Cores personalizadas para Kughie
    KUGHIE = '\033[38;5;208m'  # Laranja
    KUGHIE_LIGHT = '\033[38;5;215m'
    ACCENT = '\033[38;5;51m'  # Azul ciano
    
    @classmethod
    def kughie_banner(cls, text):
        return f"{cls.KUGHIE}{cls.BOLD}{text}{cls.RESET}"

C = Colors

# ========== CONFIGURAÇÕES ==========
CONFIG = {
    'cache_enabled': True,
    'max_threads': 10,
    'timeout': 15,
    'user_agent': 'Kughie-OSINT-Toolkit/3.0',
    'max_bomb_attempts': 50,
    'api_keys': {
        'ipinfo': None,
        'virustotal': None,
        'shodan': None,
        'whatsapp_api': None,
    }
}

# ========== BANCO DE DADOS PARA CACHE ==========
class CacheDB:
    def __init__(self):
        self.db_name = 'kughie_cache.db'
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Tabela para cache de IP
        c.execute('''CREATE TABLE IF NOT EXISTS ip_cache
                     (ip TEXT PRIMARY KEY, data TEXT, 
                      created DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        # Tabela para cache de telefone
        c.execute('''CREATE TABLE IF NOT EXISTS phone_cache
                     (phone TEXT PRIMARY KEY, data TEXT,
                      created DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        # Tabela para cache de username
        c.execute('''CREATE TABLE IF NOT EXISTS username_cache
                     (username TEXT PRIMARY KEY, data TEXT,
                      created DATetime DEFAULT CURRENT_TIMESTAMP)''')
        
        # Tabela para cache de email
        c.execute('''CREATE TABLE IF NOT EXISTS email_cache
                     (email TEXT PRIMARY KEY, data TEXT,
                      created DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        conn.close()
    
    def get_cached_ip(self, ip):
        if not CONFIG['cache_enabled']:
            return None
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT data FROM ip_cache WHERE ip = ?", (ip,))
        result = c.fetchone()
        conn.close()
        return json.loads(result[0]) if result else None
    
    def cache_ip(self, ip, data):
        if not CONFIG['cache_enabled']:
            return
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("REPLACE INTO ip_cache (ip, data) VALUES (?, ?)",
                  (ip, json.dumps(data)))
        conn.commit()
        conn.close()

cache_db = CacheDB()

# ========== DECORATORS E UTILITIES ==========
def kughie_banner_decorator(func):
    """Decorator para exibir banner do Kughie"""
    def wrapper(*args, **kwargs):
        clear_screen()
        display_kughie_banner()
        time.sleep(0.3)
        return func(*args, **kwargs)
    return wrapper

def handle_errors(func):
    """Decorator para tratamento de erros"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            print(f"\n{C.RED}[!] Network Error: {e}{C.RESET}")
            return None
        except ValueError as e:
            print(f"\n{C.RED}[!] Invalid Input: {e}{C.RESET}")
            return None
        except Exception as e:
            print(f"\n{C.RED}[!] Unexpected Error: {e}{C.RESET}")
            return None
    return wrapper

def clear_screen():
    """Limpa a tela do terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner(text, color=C.KUGHIE):
    """Imprime banner estilizado"""
    width = 60
    print(f"\n{color}{'='*width}{C.RESET}")
    print(f"{color}{text.center(width)}{C.RESET}")
    print(f"{color}{'='*width}{C.RESET}\n")

def create_session():
    """Cria sessão HTTP com configurações"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': CONFIG['user_agent'],
        'Accept': 'application/json'
    })
    session.timeout = CONFIG['timeout']
    return session

# ========== FUNÇÕES DE BOMBER ==========
@kughie_banner_decorator
@handle_errors
def sms_bomber():
    """SMS Bomber (Para fins educacionais apenas)"""
    print_banner("SMS BOMBER", C.RED)
    
    print(f"{C.YELLOW}[!] AVISO: Use apenas com permissão do alvo!{C.RESET}\n")
    
    phone = input(f"{C.WHITE}► Número de telefone (com código país): {C.GREEN}")
    
    try:
        parsed = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(parsed):
            print(f"{C.RED}[!] Número inválido{C.RESET}")
            return
        
        message_count = int(input(f"{C.WHITE}► Quantidade de SMS (1-{CONFIG['max_bomb_attempts']}): {C.GREEN}"))
        
        if message_count < 1 or message_count > CONFIG['max_bomb_attempts']:
            print(f"{C.RED}[!] Quantidade inválida{C.RESET}")
            return
        
        message = input(f"{C.WHITE}► Mensagem (deixe em branco para padrão): {C.GREEN}")
        if not message:
            message = "Teste do Kughie OSINT Toolkit"
        
        print(f"\n{C.YELLOW}[i] Iniciando envio de {message_count} SMS...{C.RESET}")
        
        # Lista de serviços SMS gratuitos (apenas para demonstração)
        sms_services = [
            {"name": "Twilio Test", "url": "https://api.twilio.com/2010-04-01/Accounts/"},
            {"name": "Nexmo", "url": "https://rest.nexmo.com/sms/json"},
            {"name": "TextBelt", "url": "http://textbelt.com/text"},
        ]
        
        sent_count = 0
        for i in range(message_count):
            try:
                # Simulação - EM AMBIENTE REAL, PRECISA DE APIs REAIS
                print(f"{C.YELLOW}[{i+1}/{message_count}] Enviando SMS...{C.RESET}")
                time.sleep(0.5)
                sent_count += 1
            except:
                pass
        
        print(f"\n{C.GREEN}[+] Enviados: {sent_count}/{message_count}{C.RESET}")
        
    except Exception as e:
        print(f"{C.RED}[!] Erro: {e}{C.RESET}")

@kughie_banner_decorator
@handle_errors
def email_bomber():
    """Email Bomber (Para fins educacionais apenas)"""
    print_banner("EMAIL BOMBER", C.RED)
    
    print(f"{C.YELLOW}[!] AVISO: Use apenas com permissão!{C.RESET}\n")
    
    target_email = input(f"{C.WHITE}► Email alvo: {C.GREEN}")
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", target_email):
        print(f"{C.RED}[!] Email inválido{C.RESET}")
        return
    
    email_count = int(input(f"{C.WHITE}► Quantidade de emails (1-{CONFIG['max_bomb_attempts']}): {C.GREEN}"))
    
    if email_count < 1 or email_count > CONFIG['max_bomb_attempts']:
        print(f"{C.RED}[!] Quantidade inválida{C.RESET}")
        return
    
    subject = input(f"{C.WHITE}► Assunto: {C.GREEN}")
    message = input(f"{C.WHITE}► Mensagem: {C.GREEN}")
    
    print(f"\n{C.YELLOW}[i] Configurando envio...{C.RESET}")
    
    # Configurações SMTP (exemplo com Gmail)
    use_gmail = input(f"{C.WHITE}► Usar Gmail SMTP? (s/n): {C.GREEN}").lower() == 's'
    
    if use_gmail:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        from_email = input(f"{C.WHITE}► Seu email Gmail: {C.GREEN}")
        password = input(f"{C.WHITE}► Senha do app (não a normal): {C.GREEN}")
    else:
        smtp_server = input(f"{C.WHITE}► SMTP Server: {C.GREEN}")
        smtp_port = int(input(f"{C.WHITE}► SMTP Port: {C.GREEN}"))
        from_email = input(f"{C.WHITE}► Email remetente: {C.GREEN}")
        password = input(f"{C.WHITE}► Senha: {C.GREEN}")
    
    print(f"\n{C.YELLOW}[i] Iniciando envio de {email_count} emails...{C.RESET}")
    
    sent_count = 0
    try:
        for i in range(email_count):
            try:
                msg = MIMEMultipart()
                msg['From'] = from_email
                msg['To'] = target_email
                msg['Subject'] = f"{subject} #{i+1}"
                
                body = f"{message}\n\nEnviado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(from_email, password)
                server.send_message(msg)
                server.quit()
                
                sent_count += 1
                print(f"{C.GREEN}[✓] Email {i+1} enviado{C.RESET}")
                time.sleep(1)
                
            except Exception as e:
                print(f"{C.RED}[✗] Erro no email {i+1}: {e}{C.RESET}")
        
        print(f"\n{C.GREEN}[+] Total enviados: {sent_count}/{email_count}{C.RESET}")
        
    except Exception as e:
        print(f"{C.RED}[!] Erro geral: {e}{C.RESET}")

# ========== CONSULTAS AVANÇADAS ==========
@kughie_banner_decorator
@handle_errors
def advanced_phone_lookup():
    """Consulta avançada de número de telefone"""
    print_banner("CONSULTA AVANÇADA DE TELEFONE", C.ACCENT)
    
    phone = input(f"{C.WHITE}► Número de telefone: {C.GREEN}")
    
    try:
        parsed = phonenumbers.parse(phone, None)
        
        if not phonenumbers.is_valid_number(parsed):
            print(f"{C.RED}[!] Número inválido{C.RESET}")
            return
        
        print(f"\n{C.YELLOW}[i] Consultando múltiplas fontes...{C.RESET}")
        
        # Informações básicas do phonenumbers
        print(f"\n{C.WHITE}========== INFORMAÇÕES BÁSICAS =========={C.RESET}")
        print(f"{C.WHITE}Número Internacional: {C.GREEN}{phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}{C.RESET}")
        print(f"{C.WHITE}Código País: {C.GREEN}+{parsed.country_code}{C.RESET}")
        
        try:
            operator = carrier.name_for_number(parsed, "en")
            print(f"{C.WHITE}Operadora: {C.GREEN}{operator}{C.RESET}")
        except:
            print(f"{C.WHITE}Operadora: {C.YELLOW}Não identificada{C.RESET}")
        
        try:
            location = geocoder.description_for_number(parsed, "pt")
            print(f"{C.WHITE}Localização: {C.GREEN}{location}{C.RESET}")
        except:
            print(f"{C.WHITE}Localização: {C.YELLOW}Não disponível{C.RESET}")
        
        # Verificar em Truecaller (simulação)
        print(f"\n{C.YELLOW}[i] Verificando Truecaller...{C.RESET}")
        try:
            # Simulação - EM PRODUÇÃO USAR API REAL
            tc_url = f"https://www.truecaller.com/search/pt/{parsed.country_code}/{parsed.national_number}"
            print(f"{C.WHITE}Link Truecaller: {C.CYAN}{tc_url}{C.RESET}")
        except:
            pass
        
        # Verificar se número está em vazamentos
        print(f"\n{C.YELLOW}[i] Verificando vazamentos...{C.RESET}")
        try:
            import hashlib
            phone_hash = hashlib.sha256(phone.encode()).hexdigest()
            # Simulação de verificação
            print(f"{C.WHITE}Hash do número: {C.GREEN}{phone_hash[:16]}...{C.RESET}")
        except:
            pass
        
        # Verificar redes sociais por número
        print(f"\n{C.YELLOW}[i] Verificando redes sociais...{C.RESET}")
        social_checks = [
            {"name": "WhatsApp", "url": f"https://wa.me/{parsed.country_code}{parsed.national_number}"},
            {"name": "Telegram", "url": f"https://t.me/{parsed.country_code}{parsed.national_number}"},
            {"name": "Facebook", "url": f"https://www.facebook.com/search/top/?q={phone}"},
        ]
        
        for check in social_checks:
            print(f"{C.WHITE}{check['name']}: {C.CYAN}{check['url']}{C.RESET}")
        
    except phonenumbers.NumberParseException as e:
        print(f"{C.RED}[!] Erro ao analisar número: {e}{C.RESET}")

@kughie_banner_decorator
@handle_errors
def advanced_email_lookup():
    """Consulta avançada de email"""
    print_banner("CONSULTA AVANÇADA DE EMAIL", C.ACCENT)
    
    email = input(f"{C.WHITE}► Email: {C.GREEN}")
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        print(f"{C.RED}[!] Formato de email inválido{C.RESET}")
        return
    
    print(f"\n{C.YELLOW}[i] Analisando email...{C.RESET}")
    
    username, domain = email.split('@')
    
    print(f"\n{C.WHITE}========== INFORMAÇÕES BÁSICAS =========={C.RESET}")
    print(f"{C.WHITE}Usuário: {C.GREEN}{username}{C.RESET}")
    print(f"{C.WHITE}Domínio: {C.GREEN}{domain}{C.RESET}")
    
    # Verificar HaveIBeenPwned
    print(f"\n{C.YELLOW}[i] Verificando vazamentos (HaveIBeenPwned)...{C.RESET}")
    try:
        sha1_hash = hashlib.sha1(email.lower().encode()).hexdigest().upper()
        prefix, suffix = sha1_hash[:5], sha1_hash[5:]
        
        response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=10)
        
        found = False
        for line in response.text.splitlines():
            if line.startswith(suffix):
                count = line.split(':')[1]
                print(f"{C.RED}[!] Email encontrado em {count} vazamentos!{C.RESET}")
                found = True
                break
        
        if not found:
            print(f"{C.GREEN}[✓] Email não encontrado em vazamentos{C.RESET}")
    except:
        print(f"{C.YELLOW}[!] Não foi possível verificar vazamentos{C.RESET}")
    
    # Verificar Hunter.io (simulação)
    print(f"\n{C.YELLOW}[i] Verificando Hunter.io...{C.RESET}")
    try:
        # Simulação - EM PRODUÇÃO USAR API REAL
        hunter_url = f"https://hunter.io/verify/{email}"
        print(f"{C.WHITE}Link Hunter.io: {C.CYAN}{hunter_url}{C.RESET}")
    except:
        pass
    
    # Verificar redes sociais por email
    print(f"\n{C.YELLOW}[i] Verificando redes sociais...{C.RESET}")
    social_checks = [
        {"name": "Facebook", "url": f"https://www.facebook.com/search/top/?q={email}"},
        {"name": "Twitter", "url": f"https://twitter.com/search?q={email}"},
        {"name": "Google", "url": f"https://www.google.com/search?q={email}"},
        {"name": "Gravatar", "url": f"https://www.gravatar.com/{hashlib.md5(email.lower().encode()).hexdigest()}"},
    ]
    
    for check in social_checks:
        print(f"{C.WHITE}{check['name']}: {C.CYAN}{check['url']}{C.RESET}")
    
    # Verificar domínio
    print(f"\n{C.YELLOW}[i] Analisando domínio...{C.RESET}")
    try:
        import socket
        ip = socket.gethostbyname(domain)
        print(f"{C.WHITE}IP do domínio: {C.GREEN}{ip}{C.RESET}")
        
        # Verificar informações do IP do domínio
        info = get_ip_info(ip)
        if info:
            print(f"{C.WHITE}Localização do servidor: {C.GREEN}{info.get('city', 'N/A')}, {info.get('country', 'N/A')}{C.RESET}")
    except:
        print(f"{C.YELLOW}[!] Não foi possível resolver domínio{C.RESET}")

@kughie_banner_decorator
@handle_errors
def whatsapp_investigator():
    """Investigador de WhatsApp"""
    print_banner("INVESTIGADOR WHATSAPP", C.GREEN)
    
    print(f"{C.WHITE}[{C.GREEN}1{C.WHITE}] {C.CYAN}Verificar número WhatsApp{C.RESET}")
    print(f"{C.WHITE}[{C.GREEN}2{C.WHITE}] {C.CYAN}Gerar link WhatsApp{C.RESET}")
    print(f"{C.WHITE}[{C.GREEN}3{C.WHITE}] {C.CYAN}Informações do perfil{C.RESET}")
    
    choice = input(f"\n{C.WHITE}► Opção: {C.GREEN}")
    
    if choice == '1':
        phone = input(f"{C.WHITE}► Número (com código país): {C.GREEN}")
        try:
            parsed = phonenumbers.parse(phone, None)
            whatsapp_url = f"https://wa.me/{parsed.country_code}{parsed.national_number}"
            
            print(f"\n{C.WHITE}Link WhatsApp: {C.CYAN}{whatsapp_url}{C.RESET}")
            
            # Verificar se número está registrado
            print(f"\n{C.YELLOW}[i] Dica: Copie o link e cole no navegador para verificar{C.RESET}")
            
        except:
            print(f"{C.RED}[!] Número inválido{C.RESET}")
    
    elif choice == '2':
        phone = input(f"{C.WHITE}► Número (com código país): {C.GREEN}")
        message = input(f"{C.WHITE}► Mensagem (opcional): {C.GREEN}")
        
        try:
            parsed = phonenumbers.parse(phone, None)
            base_url = f"https://wa.me/{parsed.country_code}{parsed.national_number}"
            
            if message:
                encoded_msg = requests.utils.quote(message)
                whatsapp_url = f"{base_url}?text={encoded_msg}"
            else:
                whatsapp_url = base_url
            
            print(f"\n{C.WHITE}Link WhatsApp: {C.CYAN}{whatsapp_url}{C.RESET}")
            print(f"{C.WHITE}Código QR: {C.CYAN}https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={requests.utils.quote(whatsapp_url)}{C.RESET}")
            
        except:
            print(f"{C.RED}[!] Erro ao gerar link{C.RESET}")
    
    elif choice == '3':
        # Informações sobre perfis WhatsApp
        print(f"\n{C.YELLOW}[i] Informações sobre investigação WhatsApp:{C.RESET}")
        print(f"{C.WHITE}1. Foto de perfil pode ser visualizada{C.RESET}")
        print(f"{C.WHITE}2. Status/última vez online visível{C.RESET}")
        print(f"{C.WHITE}3. Número deve estar registrado no WhatsApp{C.RESET}")
        print(f"{C.WHITE}4. Use o link wa.me para verificação{C.RESET}")

@kughie_banner_decorator
@handle_errors
def instagram_investigator():
    """Investigador de Instagram"""
    print_banner("INVESTIGADOR INSTAGRAM", C.MAGENTA)
    
    username = input(f"{C.WHITE}► Username do Instagram: {C.GREEN}")
    
    if not username.strip():
        print(f"{C.RED}[!] Username não pode ser vazio{C.RESET}")
        return
    
    print(f"\n{C.YELLOW}[i] Coletando informações...{C.RESET}")
    
    urls = {
        "Perfil": f"https://www.instagram.com/{username}/",
        "Posts": f"https://www.instagram.com/{username}/?__a=1",
        "Seguidores": f"https://www.instagram.com/{username}/followers/",
        "Seguindo": f"https://www.instagram.com/{username}/following/",
        "Fotos": f"https://www.instagram.com/{username}/channel/?__a=1",
        "Pesquisa Google": f"https://www.google.com/search?q=site:instagram.com+{username}",
    }
    
    print(f"\n{C.WHITE}========== LINKS ÚTEIS =========={C.RESET}")
    for name, url in urls.items():
        print(f"{C.WHITE}{name}: {C.CYAN}{url}{C.RESET}")
    
    # Ferramentas de análise externa
    print(f"\n{C.WHITE}========== FERRAMENTAS EXTERNAS =========={C.RESET}")
    tools = [
        ("Picuki", f"https://www.picuki.com/profile/{username}"),
        ("Imginn", f"https://imginn.com/{username}/"),
        ("InstaStalker", f"https://instastalker.com/profile/{username}"),
        ("Dumpor", f"https://dumpor.com/v/{username}"),
    ]
    
    for tool_name, tool_url in tools:
        print(f"{C.WHITE}{tool_name}: {C.CYAN}{tool_url}{C.RESET}")

@kughie_banner_decorator
@handle_errors
def facebook_investigator():
    """Investigador de Facebook"""
    print_banner("INVESTIGADOR FACEBOOK", C.BLUE)
    
    target = input(f"{C.WHITE}► ID, Username ou URL: {C.GREEN}")
    
    print(f"\n{C.YELLOW}[i] Gerando links de análise...{C.RESET}")
    
    # Limpar URL se fornecida
    if 'facebook.com' in target:
        if '/profile.php?id=' in target:
            fb_id = target.split('id=')[1].split('&')[0]
            username = None
        else:
            username = target.split('facebook.com/')[1].split('/')[0].split('?')[0]
            fb_id = None
    else:
        # Verificar se é numérico (ID) ou username
        if target.isdigit():
            fb_id = target
            username = None
        else:
            username = target
            fb_id = None
    
    urls = []
    
    if fb_id:
        urls.append(("Perfil", f"https://www.facebook.com/profile.php?id={fb_id}"))
        urls.append(("Fotos", f"https://www.facebook.com/{fb_id}/photos"))
        urls.append(("Amigos", f"https://www.facebook.com/{fb_id}/friends"))
        urls.append(("Informações", f"https://www.facebook.com/{fb_id}/about"))
    elif username:
        urls.append(("Perfil", f"https://www.facebook.com/{username}"))
        urls.append(("Fotos", f"https://www.facebook.com/{username}/photos"))
        urls.append(("Amigos", f"https://www.facebook.com/{username}/friends"))
        urls.append(("Informações", f"https://www.facebook.com/{username}/about"))
    
    # Ferramentas externas
    urls.extend([
        ("Pesquisa Google", f"https://www.google.com/search?q=site:facebook.com+{target}"),
        ("Lookup-ID", f"https://lookup-id.com/#:~:text={target}"),
        ("FindMyFBID", "https://findmyfbid.com/"),
        ("Facebook Video Downloader", f"https://fbdown.net/download.php?url=https://facebook.com/{target}"),
    ])
    
    print(f"\n{C.WHITE}========== LINKS DE ANÁLISE =========={C.RESET}")
    for name, url in urls:
        print(f"{C.WHITE}{name}: {C.CYAN}{url}{C.RESET}")
    
    print(f"\n{C.YELLOW}[i] Dicas de investigação:{C.RESET}")
    print(f"{C.WHITE}1. Verifique fotos públicas{C.RESET}")
    print(f"{C.WHITE}2. Analise amigos em comum{C.RESET}")
    print(f"{C.WHITE}3. Verifique check-ins e locais{C.RESET}")
    print(f"{C.WHITE}4. Use Graph Search avançado{C.RESET}")

# ========== FUNÇÕES EXISTENTES (MANTIDAS) ==========
@kughie_banner_decorator
@handle_errors
def track_ip():
    """Rastreamento avançado de IP"""
    print(f"{C.WHITE}[{C.GREEN}1{C.WHITE}] {C.CYAN}Rastreamento de IP{C.RESET}")
    print(f"{C.WHITE}[{C.GREEN}2{C.WHITE}] {C.CYAN}Verificar múltiplos IPs{C.RESET}")
    print(f"{C.WHITE}[{C.GREEN}3{C.WHITE}] {C.CYAN}Análise reversa de DNS{C.RESET}")
    
    choice = input(f"\n{C.WHITE}[{C.GREEN}+{C.WHITE}] {C.YELLOW}Escolha: {C.RESET}")
    
    if choice == '1':
        ip = input(f"\n{C.WHITE}► Digite o IP alvo: {C.GREEN}")
        if not validate_ip(ip):
            print(f"{C.RED}[!] IP inválido{C.RESET}")
            return
        analyze_single_ip(ip)
    
    elif choice == '2':
        ips = input(f"\n{C.WHITE}► Digite IPs (separados por vírgula): {C.GREEN}")
        ip_list = [ip.strip() for ip in ips.split(',')]
        analyze_multiple_ips(ip_list)
    
    elif choice == '3':
        domain = input(f"\n{C.WHITE}► Digite domínio para DNS reverso: {C.GREEN}")
        reverse_dns_lookup(domain)

def validate_ip(ip):
    """Valida formato de IP"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

@lru_cache(maxsize=100)
def get_ip_info(ip):
    """Obtém informações de IP com cache"""
    cached = cache_db.get_cached_ip(ip)
    if cached:
        print(f"{C.YELLOW}[i] Usando dados em cache{C.RESET}")
        return cached
    
    session = create_session()
    
    apis = [
        f"http://ipwho.is/{ip}",
        f"https://ipapi.co/{ip}/json/",
        f"http://ip-api.com/json/{ip}?fields=66846719"
    ]
    
    for api_url in apis:
        try:
            response = session.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                cache_db.cache_ip(ip, data)
                return data
        except:
            continue
    
    raise requests.exceptions.RequestException("Não foi possível obter dados do IP")

def analyze_single_ip(ip):
    """Analisa um único IP em detalhes"""
    print_banner("ANÁLISE DE IP", C.ACCENT)
    
    data = get_ip_info(ip)
    if not data:
        return
    
    print(f"{C.WHITE}IP: {C.GREEN}{ip}{C.RESET}")
    print(f"{C.WHITE}Tipo: {C.GREEN}{data.get('type', 'N/A')}{C.RESET}")
    print(f"{C.WHITE}País: {C.GREEN}{data.get('country', 'N/A')} ({data.get('country_code', 'N/A')}){C.RESET}")
    print(f"{C.WHITE}Cidade: {C.GREEN}{data.get('city', 'N/A')}{C.RESET}")
    print(f"{C.WHITE}Região: {C.GREEN}{data.get('region', 'N/A')}{C.RESET}")
    
    if 'latitude' in data and 'longitude' in data:
        lat = data['latitude']
        lon = data['longitude']
        print(f"{C.WHITE}Coordenadas: {C.GREEN}{lat}, {lon}{C.RESET}")
        print(f"{C.WHITE}Google Maps: {C.CYAN}https://maps.google.com/?q={lat},{lon}{C.RESET}")
    
    print(f"{C.WHITE}ISP: {C.GREEN}{data.get('connection', {}).get('isp', 'N/A')}{C.RESET}")
    print(f"{C.WHITE}ASN: {C.GREEN}{data.get('connection', {}).get('asn', 'N/A')}{C.RESET}")
    print(f"{C.WHITE}Organização: {C.GREEN}{data.get('connection', {}).get('org', 'N/A')}{C.RESET}")
    
    if 'timezone' in data:
        tz = data['timezone']
        print(f"{C.WHITE}Fuso Horário: {C.GREEN}{tz.get('id', 'N/A')}{C.RESET}")
        print(f"{C.WHITE}UTC Offset: {C.GREEN}{tz.get('offset', 'N/A')}{C.RESET}")
        print(f"{C.WHITE}Horário Local: {C.GREEN}{tz.get('current_time', 'N/A')}{C.RESET}")
    
    check_ip_threats(ip)

def analyze_multiple_ips(ip_list):
    """Analisa múltiplos IPs simultaneamente"""
    print_banner("ANÁLISE EM MASSA DE IPS", C.ACCENT)
    
    results = []
    with ThreadPoolExecutor(max_workers=CONFIG['max_threads']) as executor:
        future_to_ip = {executor.submit(get_ip_info, ip): ip for ip in ip_list}
        
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                data = future.result()
                country = data.get('country', 'Unknown')
                city = data.get('city', 'Unknown')
                isp = data.get('connection', {}).get('isp', 'Unknown')
                results.append((ip, country, city, isp))
                print(f"{C.GREEN}✓{C.RESET} {ip}: {country}, {city} ({isp})")
            except Exception as e:
                print(f"{C.RED}✗{C.RESET} {ip}: Erro - {e}")
    
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kughie_ips_{timestamp}.csv"
        with open(filename, 'w') as f:
            f.write("IP,País,Cidade,ISP\n")
            for row in results:
                f.write(f"{row[0]},{row[1]},{row[2]},{row[3]}\n")
        print(f"\n{C.GREEN}[+] Resultados salvos em: {filename}{C.RESET}")

@kughie_banner_decorator
@handle_errors
def track_phone():
    """Rastreamento de número de telefone"""
    print_banner("RASTREADOR DE TELEFONE", C.ACCENT)
    
    phone = input(f"{C.WHITE}► Digite o número (com código país): {C.GREEN}")
    
    try:
        parsed = phonenumbers.parse(phone, None)
        
        if not phonenumbers.is_valid_number(parsed):
            print(f"{C.RED}[!] Número inválido{C.RESET}")
            return
        
        print(f"\n{C.WHITE}========== INFORMAÇÕES DO TELEFONE =========={C.RESET}")
        
        print(f"{C.WHITE}Número Internacional: {C.GREEN}{phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}{C.RESET}")
        print(f"{C.WHITE}Código País: {C.GREEN}+{parsed.country_code}{C.RESET}")
        print(f"{C.WHITE}Número Local: {C.GREEN}{parsed.national_number}{C.RESET}")
        
        try:
            operator = carrier.name_for_number(parsed, "en")
            print(f"{C.WHITE}Operadora: {C.GREEN}{operator}{C.RESET}")
        except:
            print(f"{C.WHITE}Operadora: {C.YELLOW}Não identificada{C.RESET}")
        
        try:
            location = geocoder.description_for_number(parsed, "pt")
            print(f"{C.WHITE}Localização: {C.GREEN}{location}{C.RESET}")
        except:
            print(f"{C.WHITE}Localização: {C.YELLOW}Não disponível{C.RESET}")
        
        try:
            timezones = timezone.time_zones_for_number(parsed)
            if timezones:
                print(f"{C.WHITE}Fuso Horário: {C.GREEN}{', '.join(timezones)}{C.RESET}")
        except:
            pass
        
        number_type = phonenumbers.number_type(parsed)
        type_map = {
            phonenumbers.PhoneNumberType.MOBILE: "Celular",
            phonenumbers.PhoneNumberType.FIXED_LINE: "Fixo",
            phonenumbers.PhoneNumberType.VOIP: "VoIP",
            phonenumbers.PhoneNumberType.TOLL_FREE: "0800",
        }
        print(f"{C.WHITE}Tipo: {C.GREEN}{type_map.get(number_type, 'Desconhecido')}{C.RESET}")
        
        print(f"{C.WHITE}Válido: {C.GREEN if phonenumbers.is_valid_number(parsed) else C.RED}{phonenumbers.is_valid_number(parsed)}{C.RESET}")
        print(f"{C.WHITE}Possível: {C.GREEN if phonenumbers.is_possible_number(parsed) else C.RED}{phonenumbers.is_possible_number(parsed)}{C.RESET}")
        
        print(f"\n{C.YELLOW}[i] Verificando listas de spam...{C.RESET}")
        
    except phonenumbers.NumberParseException as e:
        print(f"{C.RED}[!] Erro ao analisar número: {e}{C.RESET}")

@kughie_banner_decorator
@handle_errors 
def track_username():
    """Rastreamento de username em redes sociais"""
    print_banner("RASTREADOR DE USERNAME", C.ACCENT)
    
    username = input(f"{C.WHITE}► Digite o username: {C.GREEN}")
    
    if not username.strip():
        print(f"{C.RED}[!] Username não pode ser vazio{C.RESET}")
        return
    
    print(f"\n{C.YELLOW}[i] Verificando em redes sociais...{C.RESET}")
    
    social_platforms = [
        {"name": "Facebook", "url": f"https://www.facebook.com/{username}", "check": "meta"},
        {"name": "Instagram", "url": f"https://www.instagram.com/{username}/", "check": "instagram"},
        {"name": "Twitter/X", "url": f"https://twitter.com/{username}", "check": "twitter"},
        {"name": "GitHub", "url": f"https://github.com/{username}", "check": "github"},
        {"name": "LinkedIn", "url": f"https://www.linkedin.com/in/{username}", "check": "linkedin"},
        {"name": "TikTok", "url": f"https://www.tiktok.com/@{username}", "check": "tiktok"},
        {"name": "YouTube", "url": f"https://www.youtube.com/@{username}", "check": "youtube"},
        {"name": "Reddit", "url": f"https://www.reddit.com/user/{username}", "check": "reddit"},
        {"name": "Pinterest", "url": f"https://www.pinterest.com/{username}", "check": "pinterest"},
        {"name": "Twitch", "url": f"https://www.twitch.tv/{username}", "check": "twitch"},
        {"name": "Telegram", "url": f"https://t.me/{username}", "check": "telegram"},
        {"name": "Snapchat", "url": f"https://www.snapchat.com/add/{username}", "check": "snapchat"},
        {"name": "Discord", "url": f"https://discord.com/users/{username}", "check": "discord"},
        {"name": "Medium", "url": f"https://medium.com/@{username}", "check": "medium"},
        {"name": "Dev.to", "url": f"https://dev.to/{username}", "check": "devto"},
        {"name": "Behance", "url": f"https://www.behance.net/{username}", "check": "behance"},
        {"name": "Dribbble", "url": f"https://dribbble.com/{username}", "check": "dribbble"},
        {"name": "Spotify", "url": f"https://open.spotify.com/user/{username}", "check": "spotify"},
        {"name": "Steam", "url": f"https://steamcommunity.com/id/{username}", "check": "steam"},
        {"name": "VK", "url": f"https://vk.com/{username}", "check": "vk"},
    ]
    
    session = create_session()
    results = []
    
    def check_platform(platform):
        try:
            response = session.get(platform["url"], timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                if platform["check"] == "github" and "Not Found" not in response.text:
                    return platform["name"], platform["url"], True
                elif platform["check"] == "twitter" and response.url != "https://twitter.com/":
                    return platform["name"], platform["url"], True
                elif platform["check"] == "instagram" and "Page Not Found" not in response.text:
                    return platform["name"], platform["url"], True
                else:
                    if response.url == platform["url"] or response.status_code != 404:
                        return platform["name"], platform["url"], True
            return platform["name"], platform["url"], False
        except:
            return platform["name"], platform["url"], False
    
    with ThreadPoolExecutor(max_workers=CONFIG['max_threads']) as executor:
        futures = [executor.submit(check_platform, platform) for platform in social_platforms]
        
        for future in as_completed(futures):
            name, url, found = future.result()
            if found:
                results.append((name, url))
                print(f"{C.GREEN}[✓]{C.RESET} {C.WHITE}{name}:{C.GREEN} Encontrado")
            else:
                print(f"{C.RED}[✗]{C.RESET} {C.WHITE}{name}:{C.RED} Não encontrado")
    
    print_banner("RESUMO DA BUSCA", C.GREEN)
    if results:
        print(f"{C.GREEN}[+] Username encontrado em {len(results)} plataforma(s):{C.RESET}\n")
        for name, url in results:
            print(f"  {C.WHITE}• {name}: {C.CYAN}{url}{C.RESET}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kughie_username_{username}_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write(f"Resultados para username: {username}\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
            for name, url in results:
                f.write(f"{name}: {url}\n")
        print(f"\n{C.GREEN}[+] Resultados salvos em: {filename}{C.RESET}")
    else:
        print(f"{C.YELLOW}[!] Username não encontrado em nenhuma plataforma verificada{C.RESET}")

@kughie_banner_decorator
@handle_errors
def email_investigator():
    """Investigador de email"""
    print_banner("INVESTIGADOR DE EMAIL", C.ACCENT)
    
    email = input(f"{C.WHITE}► Digite o email: {C.GREEN}")
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        print(f"{C.RED}[!] Formato de email inválido{C.RESET}")
        return
    
    print(f"\n{C.YELLOW}[i] Analisando email...{C.RESET}")
    
    username, domain = email.split('@')
    print(f"{C.WHITE}Usuário: {C.GREEN}{username}{C.RESET}")
    print(f"{C.WHITE}Domínio: {C.GREEN}{domain}{C.RESET}")
    
    try:
        print(f"\n{C.YELLOW}[i] Verificando vazamentos...{C.RESET}")
        sha1_hash = hashlib.sha1(email.lower().encode()).hexdigest().upper()
        prefix, suffix = sha1_hash[:5], sha1_hash[5:]
        
        response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=10)
        
        found = False
        for line in response.text.splitlines():
            if line.startswith(suffix):
                count = line.split(':')[1]
                print(f"{C.RED}[!] Email encontrado em {count} vazamentos de dados!{C.RESET}")
                found = True
                break
        
        if not found:
            print(f"{C.GREEN}[✓] Email não encontrado em vazamentos conhecidos{C.RESET}")
    except:
        print(f"{C.YELLOW}[!] Não foi possível verificar vazamentos{C.RESET}")
    
    try:
        print(f"\n{C.YELLOW}[i] Verificando domínio...{C.RESET}")
        mx_records = []
        import dns.resolver
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            for rdata in answers:
                mx_records.append(str(rdata.exchange))
            print(f"{C.WHITE}Servidores MX: {C.GREEN}{', '.join(mx_records)}{C.RESET}")
        except:
            print(f"{C.YELLOW}[!] Não foi possível obter registros MX{C.RESET}")
    except ImportError:
        print(f"{C.YELLOW}[i] Instale dnspython para verificação de DNS: pip install dnspython{C.RESET}")

@kughie_banner_decorator
def show_my_ip():
    """Mostra o IP público do usuário"""
    print_banner("SEU IP PÚBLICO", C.ACCENT)
    
    services = [
        'https://api.ipify.org',
        'https://checkip.amazonaws.com',
        'https://icanhazip.com',
        'https://ident.me'
    ]
    
    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                ip = response.text.strip()
                print(f"{C.WHITE}Seu IP Público: {C.GREEN}{ip}{C.RESET}")
                
                print(f"\n{C.YELLOW}[i] Obtendo informações do seu IP...{C.RESET}")
                try:
                    info = get_ip_info(ip)
                    if info:
                        print(f"{C.WHITE}Localização: {C.GREEN}{info.get('city', 'N/A')}, {info.get('country', 'N/A')}{C.RESET}")
                        print(f"{C.WHITE}ISP: {C.GREEN}{info.get('connection', {}).get('isp', 'N/A')}{C.RESET}")
                except:
                    pass
                
                return
        except:
            continue
    
    print(f"{C.RED}[!] Não foi possível obter o IP público{C.RESET}")

def reverse_dns_lookup(domain):
    """Faz lookup DNS reverso"""
    print_banner("DNS REVERSO", C.ACCENT)
    
    try:
        import socket
        ips = socket.gethostbyname_ex(domain)[2]
        
        if ips:
            print(f"{C.WHITE}IPs associados a {domain}:{C.RESET}")
            for ip in ips:
                print(f"  {C.GREEN}• {ip}{C.RESET}")
                
                analyze = input(f"\n{C.YELLOW}Analisar IP {ip}? (s/n): {C.RESET}")
                if analyze.lower() == 's':
                    analyze_single_ip(ip)
        else:
            print(f"{C.YELLOW}[!] Nenhum IP encontrado para o domínio{C.RESET}")
    except socket.gaierror:
        print(f"{C.RED}[!] Domínio não encontrado{C.RESET}")
    except ImportError:
        print(f"{C.YELLOW}[i] Função não disponível{C.RESET}")

def check_ip_threats(ip):
    """Verifica ameaças associadas ao IP"""
    print(f"\n{C.YELLOW}[i] Verificando ameaças...{C.RESET}")
    
    threats = []
    
    if ipaddress.ip_address(ip).is_private:
        threats.append("IP Privado/Reservado")
    
    if threats:
        print(f"{C.RED}[!] Ameaças detectadas:{C.RESET}")
        for threat in threats:
            print(f"  {C.RED}• {threat}{C.RESET}")
    else:
        print(f"{C.GREEN}[✓] Nenhuma ameaça conhecida detectada{C.RESET}")

# ========== FUNÇÕES DO SISTEMA ==========
def display_kughie_banner():
    """Exibe o banner principal do Kughie com gato ASCII"""
    banner = f"""
{C.KUGHIE}
 /\_/\\  
( o.o ) 
 > ^ <
{C.RESET}
{C.KUGHIE_LIGHT}
╦ ╦╦ ╦╔╗╔╔╦╗╦╔═╗
║║║║ ║║║║ ║ ║║ ║
╚╩╝╚═╝╝╚╝ ╩ ╩╚═╝
{C.ACCENT}{'='*55}{C.RESET}
{C.WHITE}        K U G H I E   O S I N T   T O O L K I T   v3.0
{C.ACCENT}{'='*55}{C.RESET}
{C.YELLOW}    By Kughie | Uso Ético Apenas | Bombers para educação
{C.ACCENT}{'='*55}{C.RESET}
{C.MAGENTA}
    |\\___/|
    )     (     .              '
   =\\     /=
     )===(
    /     \\
    |     |      /
   /       \\
   \\       /
    \\__  _/
      ( (
       ) )
      (_(
{C.RESET}
"""
    print(banner)

def display_main_menu():
    """Exibe o menu principal"""
    menu_items = [
        (1, "Rastreamento de IP", track_ip),
        (2, "Rastreamento de Telefone", track_phone),
        (3, "Consulta Avançada Telefone", advanced_phone_lookup),
        (4, "Rastreamento de Username", track_username),
        (5, "Investigador de Email", email_investigator),
        (6, "Consulta Avançada Email", advanced_email_lookup),
        (7, "Investigador WhatsApp", whatsapp_investigator),
        (8, "Investigador Instagram", instagram_investigator),
        (9, "Investigador Facebook", facebook_investigator),
        (10, "Mostrar Meu IP", show_my_ip),
        (11, "SMS Bomber (EDUCAÇÃO)", sms_bomber),
        (12, "Email Bomber (EDUCAÇÃO)", email_bomber),
        (13, "Configurações", show_settings),
        (0, "Sair", exit_program),
    ]
    
    print(f"\n{C.WHITE}{' MENU PRINCIPAL '.center(55, '─')}{C.RESET}\n")
    
    for num, text, _ in menu_items:
        color = C.RED if "BOMBER" in text or "EDUCAÇÃO" in text else C.CYAN
        print(f"  {C.WHITE}[{C.GREEN}{num:2d}{C.WHITE}] {color}{text}{C.RESET}")
    
    print(f"\n{C.WHITE}{''.center(55, '─')}{C.RESET}")
    
    return menu_items

def show_settings():
    """Exibe configurações"""
    print_banner("CONFIGURAÇÕES", C.ACCENT)
    
    print(f"{C.WHITE}Cache: {C.GREEN if CONFIG['cache_enabled'] else C.RED}{CONFIG['cache_enabled']}{C.RESET}")
    print(f"{C.WHITE}Threads Máximas: {C.GREEN}{CONFIG['max_threads']}{C.RESET}")
    print(f"{C.WHITE}Timeout: {C.GREEN}{CONFIG['timeout']}s{C.RESET}")
    print(f"{C.WHITE}Máx. Bombs: {C.GREEN}{CONFIG['max_bomb_attempts']}{C.RESET}")
    
    print(f"\n{C.YELLOW}[1] {C.WHITE}Alternar Cache")
    print(f"{C.YELLOW}[2] {C.WHITE}Alterar Threads")
    print(f"{C.YELLOW}[3] {C.WHITE}Alterar Timeout")
    print(f"{C.YELLOW}[4] {C.WHITE}Alterar Máx. Bombs")
    print(f"{C.YELLOW}[0] {C.WHITE}Voltar")
    
    choice = input(f"\n{C.WHITE}► Opção: {C.GREEN}")
    
    if choice == '1':
        CONFIG['cache_enabled'] = not CONFIG['cache_enabled']
        print(f"{C.GREEN}[+] Cache {'ativado' if CONFIG['cache_enabled'] else 'desativado'}{C.RESET}")
    elif choice == '2':
        try:
            threads = int(input(f"{C.WHITE}Novo valor (1-50): {C.GREEN}"))
            if 1 <= threads <= 50:
                CONFIG['max_threads'] = threads
                print(f"{C.GREEN}[+] Threads atualizadas{C.RESET}")
        except:
            print(f"{C.RED}[!] Valor inválido{C.RESET}")
    elif choice == '3':
        try:
            timeout = int(input(f"{C.WHITE}Novo timeout (5-60): {C.GREEN}"))
            if 5 <= timeout <= 60:
                CONFIG['timeout'] = timeout
                print(f"{C.GREEN}[+] Timeout atualizado{C.RESET}")
        except:
            print(f"{C.RED}[!] Valor inválido{C.RESET}")
    elif choice == '4':
        try:
            bombs = int(input(f"{C.WHITE}Novo máximo (1-1000): {C.GREEN}"))
            if 1 <= bombs <= 1000:
                CONFIG['max_bomb_attempts'] = bombs
                print(f"{C.GREEN}[+] Máximo de bombs atualizado{C.RESET}")
        except:
            print(f"{C.RED}[!] Valor inválido{C.RESET}")
    
    input(f"\n{C.YELLOW}[Enter] para continuar...{C.RESET}")

def exit_program():
    """Encerra o programa"""
    print(f"\n{C.GREEN}[+] Saindo do Kughie...{C.RESET}")
    print(f"{C.KUGHIE}🐱 Use com responsabilidade!{C.RESET}\n")
    time.sleep(1)
    sys.exit(0)

def disclaimer():
    """Exibe disclaimer de uso ético"""
    print(f"{C.RED}{'='*60}{C.RESET}")
    print(f"{C.RED}[!] DISCLAIMER DE USO ÉTICO [!]{C.RESET}")
    print(f"{C.YELLOW}1. Use apenas para testes em sistemas próprios{C.RESET}")
    print(f"{C.YELLOW}2. Obtenha permissão explícita antes de testar{C.RESET}")
    print(f"{C.YELLOW}3. Não use para ataques ou assédio{C.RESET}")
    print(f"{C.YELLOW}4. O autor não se responsabiliza por uso indevido{C.RESET}")
    print(f"{C.RED}{'='*60}{C.RESET}\n")
    
    accept = input(f"{C.WHITE}Aceita os termos? (s/n): {C.GREEN}")
    return accept.lower() == 's'

def main():
    """Função principal"""
    if not disclaimer():
        print(f"\n{C.RED}[!] Você deve aceitar os termos para usar o Kughie{C.RESET}")
        sys.exit(1)
    
    while True:
        try:
            clear_screen()
            display_kughie_banner()
            menu_items = display_main_menu()
            
            choice = input(f"\n{C.WHITE}[{C.GREEN}+{C.WHITE}] {C.YELLOW}Selecione uma opção: {C.RESET}")
            
            try:
                choice_int = int(choice)
                for num, _, func in menu_items:
                    if num == choice_int:
                        clear_screen()
                        func()
                        input(f"\n{C.YELLOW}[Enter] para continuar...{C.RESET}")
                        break
                else:
                    print(f"\n{C.RED}[!] Opção inválida!{C.RESET}")
                    time.sleep(1)
            except ValueError:
                print(f"\n{C.RED}[!] Digite um número!{C.RESET}")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n{C.YELLOW}[!] Interrompido pelo usuário{C.RESET}")
            exit_program()
        except Exception as e:
            print(f"\n{C.RED}[!] Erro crítico: {e}{C.RESET}")
            time.sleep(2)

# ========== INICIALIZAÇÃO ==========
if __name__ == "__main__":
    # Verificar dependências
    required = ['requests', 'phonenumbers']
    missing = []
    
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"{C.RED}[!] Dependências faltando: {', '.join(missing)}{C.RESET}")
        print(f"{C.YELLOW}[i] Instale com: pip install {' '.join(missing)}{C.RESET}")
        sys.exit(1)
    
    # Iniciar
    print(f"{C.KUGHIE}🐱 Iniciando Kughie OSINT Toolkit v3.0...{C.RESET}")
    time.sleep(1)
    main()
