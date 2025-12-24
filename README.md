# 🐱 Kughie OSINT Toolkit

![Kughie Banner](https://img.shields.io/badge/Kughie-OSINT-orange)
![Python](https://img.shields.io/badge/Python-3.7+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

Uma ferramenta avançada de OSINT (Open Source Intelligence) com múltiplas funcionalidades para investigação digital.

## ✨ Funcionalidades

### 🔍 Rastreamento
- **IP Tracking**: Geolocalização, ISP, ameaças
- **Phone Tracking**: Operadora, localização, tipo de número
- **Username Tracking**: Verificação em 20+ redes sociais
- **Email Investigation**: Vazamentos, domínio, DNS

### 🕵️ Investigadores Específicos
- WhatsApp Investigator
- Instagram Investigator
- Facebook Investigator

### 📊 Consultas Avançadas
- Phone Lookup Avançado
- Email Lookup Avançado
- DNS Reverso
- Análise em massa de IPs

### ⚠️ Ferramentas Educacionais
- SMS Bomber (apenas para testes autorizados)
- Email Bomber (apenas para testes autorizados)

## 🚀 Instalação

### Termux (Android)
```bash
# Atualizar e instalar Python
pkg update && pkg upgrade -y
pkg install python python-pip git -y

# Clonar repositório
git clone https://github.com/Pedroriansouza/Kughie-Trick.git
cd Kughie-Trick

# Instalar dependências
pip install -r requirements.txt

# Executar
python kughie.py
