import boto3
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION     = os.getenv('AWS_REGION', 'us-east-1')
GMAIL_USER     = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
EMAIL_DESTINO  = os.getenv('EMAIL_DESTINO')
LIMITE_ALERTA  = float(os.getenv('LIMITE_ALERTA', 5.00))


def get_custo_aws():
    client = boto3.client(
        'ce',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    hoje = datetime.today()
    inicio_mes = hoje.replace(day=1).strftime('%Y-%m-%d')
    hoje_str = hoje.strftime('%Y-%m-%d')
    ontem_str = (hoje - timedelta(days=1)).strftime('%Y-%m-%d')

    custo_mes = client.get_cost_and_usage(
        TimePeriod={'Start': inicio_mes, 'End': hoje_str},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    custo_dia = client.get_cost_and_usage(
        TimePeriod={'Start': ontem_str, 'End': hoje_str},
        Granularity='DAILY',
        Metrics=['UnblendedCost']
    )

    custo_servico = client.get_cost_and_usage(
        TimePeriod={'Start': inicio_mes, 'End': hoje_str},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )

    valor_mes = float(custo_mes['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
    valor_dia = float(custo_dia['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

    servicos = []
    for item in custo_servico['ResultsByTime'][0]['Groups']:
        servico = item['Keys'][0]
        valor = float(item['Metrics']['UnblendedCost']['Amount'])
        if valor > 0:
            servicos.append((servico, valor))

    servicos.sort(key=lambda x: x[1], reverse=True)
    return valor_mes, valor_dia, servicos


def gerar_json(valor_mes, valor_dia, servicos, limite):
    client = boto3.client(
        'ce',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    hoje = datetime.today()

    historico_raw = client.get_cost_and_usage(
        TimePeriod={
            'Start': (hoje - timedelta(days=180)).strftime('%Y-%m-%d'),
            'End': hoje.strftime('%Y-%m-%d')
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    historico = []
    for item in historico_raw['ResultsByTime']:
        mes = item['TimePeriod']['Start'][:7]
        valor = float(item['Total']['UnblendedCost']['Amount'])
        historico.append({'mes': mes, 'valor': valor})

    data = {
        'valor_mes': valor_mes,
        'valor_dia': valor_dia,
        'limite': limite,
        'atualizado': datetime.today().strftime('%d/%m/%Y %H:%M'),
        'servicos': [{'nome': s[0], 'valor': s[1]} for s in servicos],
        'historico': historico
    }

    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("data.json atualizado!")


def enviar_email(assunto, corpo):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = EMAIL_DESTINO
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, EMAIL_DESTINO, msg.as_string())
        print(f"Email enviado: {assunto}")


def monitorar():
    valor_mes, valor_dia, servicos = get_custo_aws()

    gerar_json(valor_mes, valor_dia, servicos, LIMITE_ALERTA)

    hoje = datetime.today().strftime('%d/%m/%Y')
    dia_semana = datetime.today().weekday()

    tabela = ""
    for servico, valor in servicos:
        tabela += f"<tr><td>{servico}</td><td>US$ {valor:.4f}</td></tr>"

    if not tabela:
        tabela = '<tr><td colspan="2" style="text-align:center;color:#999">Nenhum custo registrado ainda</td></tr>'

    status_class = 'alerta' if valor_mes > LIMITE_ALERTA else 'ok'
    status_texto = 'Acima do limite' if valor_mes > LIMITE_ALERTA else 'Dentro do limite'

    corpo_diario = (
        "<!DOCTYPE html>"
        "<html><head><meta charset='UTF-8'><style>"
        "body{font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:20px}"
        ".container{max-width:600px;margin:0 auto;background:white;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.1)}"
        ".header{background:#232F3E;padding:30px;text-align:center}"
        ".header h1{color:#FF9900;margin:0;font-size:24px}"
        ".header p{color:#aaa;margin:5px 0 0}"
        ".body{padding:30px}"
        ".cards{display:flex;gap:15px;margin-bottom:25px}"
        ".card{flex:1;background:#f8f9fa;border-radius:8px;padding:15px;text-align:center;border-left:4px solid #FF9900}"
        ".card .valor{font-size:28px;font-weight:bold;color:#232F3E}"
        ".card .label{font-size:12px;color:#666;margin-top:5px}"
        ".status{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:bold}"
        ".status.ok{background:#d4edda;color:#155724}"
        ".status.alerta{background:#f8d7da;color:#721c24}"
        "table{width:100%;border-collapse:collapse;margin-top:15px}"
        "th{background:#232F3E;color:#FF9900;padding:10px;text-align:left}"
        "td{padding:10px;border-bottom:1px solid #eee}"
        ".footer{background:#f8f9fa;padding:15px;text-align:center;color:#999;font-size:12px}"
        "</style></head><body>"
        "<div class='container'>"
        "<div class='header'>"
        "<h1>AWS Cost Monitor</h1>"
        f"<p>{hoje}</p>"
        "</div>"
        "<div class='body'>"
        "<div class='cards'>"
        "<div class='card'>"
        f"<div class='valor'>US$ {valor_mes:.4f}</div>"
        "<div class='label'>Custo do Mes</div>"
        "</div>"
        "<div class='card'>"
        f"<div class='valor'>US$ {valor_dia:.4f}</div>"
        "<div class='label'>Custo de Ontem</div>"
        "</div>"
        "<div class='card'>"
        f"<div class='valor'>US$ {LIMITE_ALERTA:.2f}</div>"
        "<div class='label'>Limite de Alerta</div>"
        "</div>"
        "</div>"
        f"<p>Status: <span class='status {status_class}'>{status_texto}</span></p>"
        "<h3>Custo por Servico</h3>"
        "<table>"
        "<tr><th>Servico</th><th>Custo</th></tr>"
        f"{tabela}"
        "</table>"
        "</div>"
        "<div class='footer'>"
        "AWS Cost Monitor - Bruno Consani Fernandes<br>"
        f"Gerado automaticamente em {hoje}"
        "</div>"
        "</div>"
        "</body></html>"
    )

    enviar_email(f"Resumo Diario AWS - {hoje}", corpo_diario)

    if valor_mes > LIMITE_ALERTA:
        enviar_email(f"ALERTA AWS - Custo US$ {valor_mes:.2f} ultrapassou US$ {LIMITE_ALERTA:.2f}", corpo_diario)

    if dia_semana == 6:
        enviar_email(f"Relatorio Semanal AWS - {hoje}", corpo_diario)


if __name__ == "__main__":
    monitorar()