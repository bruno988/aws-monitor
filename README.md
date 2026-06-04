# ☁️ AWS Cost Monitor

Monitoramento automático de custos da AWS com alertas por email.

---

## 📋 O que faz

- Envia **resumo diário** de custos todo dia às 8h
- Envia **alerta imediato** se ultrapassar o limite configurado
- Envia **relatório semanal** todo domingo
- Mostra custo por serviço AWS

---

## 🏗️ Arquitetura

GitHub Actions (todo dia às 8h)
↓
Script Python
↓
AWS Cost Explorer API
↓
Email via Gmail

---

## ⚙️ Configuração

### GitHub Secrets necessários

| Secret | Descrição |
|---|---|
| `AWS_ACCESS_KEY` | Access Key da AWS |
| `AWS_SECRET_KEY` | Secret Key da AWS |
| `AWS_REGION` | Região AWS (ex: us-east-1) |
| `GMAIL_USER` | Email Gmail |
| `GMAIL_PASSWORD` | Senha de app do Gmail |
| `EMAIL_DESTINO` | Email que receberá os alertas |
| `LIMITE_ALERTA` | Valor limite em dólares (ex: 5.00) |

### Como criar senha de app Gmail

myaccount.google.com/apppasswords
Nome: GitHub Actions
Copiar senha de 16 caracteres (sem espaços)

---

## 🚀 Como usar

### Rodar manualmente

GitHub → Actions → AWS Cost Monitor → Run workflow

### Agendamento automático

Todo dia às 8h (horário de Brasília)
Não precisa do PC ligado

---

## 📧 Exemplo de email

- Header escuro com nome e data
- 3 cards: Custo do Mês, Custo de Ontem, Limite de Alerta
- Status: Dentro do limite ou Acima do limite
- Tabela com custo por serviço AWS

---

## 🔐 Segurança

- Credenciais via GitHub Secrets
- Nunca expostas no código
- Arquivo `.env` no `.gitignore`

---

## 📁 Estrutura

aws-monitor/
├── monitor.py          # Script principal
├── .env                # Credenciais locais (não vai pro GitHub)
├── .gitignore
├── .github/
│   └── workflows/
│       └── monitor.yml # Pipeline GitHub Actions
└── README.md

---

Desenvolvido por **Bruno Consani Fernandes** 🚀