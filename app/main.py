# app.py
from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# --- Configurável: série Selic no SGS (BCB)
BCB_SGS_SERIE = 11
BCB_SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json&limit=1"

def fetch_latest_selic():
    """
    Busca o último valor disponível da série SELIC no BCB.
    Retorna um dict: { 'date': 'YYYY-MM-DD', 'value': float } ou None em caso de erro.
    """
    try:
        resp = requests.get(BCB_SGS_URL.format(serie=BCB_SGS_SERIE), timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        item = data[-1]
        date = item.get('data')
        d = datetime.strptime(date, "%d/%m/%Y").date().isoformat()
        value = float(item.get('valor', '0').replace(',', '.'))
        return {'date': d, 'value': value}
    except Exception as e:
        print("Erro ao buscar Selic:", e)
        return None

def simulate_compound(amount, annual_rate_percent, years, compounds_per_year=12, periodic_contribution=0):
    """
    Simulação de juros compostos com aportes periódicos.
    """
    r = annual_rate_percent / 100.0
    m = compounds_per_year
    rate_per_period = (1 + r) ** (1/m) - 1
    total_periods = int(years * m)
    balances = []
    balance = float(amount)
    
    for p in range(1, total_periods + 1):
        balance = balance * (1 + rate_per_period) + periodic_contribution
        balances.append({
            "period": p,
            "balance": round(balance, 2)
        })
    
    return balances

# --- Rotas
@app.route('/')
def index():
    selic = fetch_latest_selic()
    return render_template('index.html', selic=selic)

@app.route('/api/selic')
def api_selic():
    selic = fetch_latest_selic()
    if not selic:
        return jsonify({'error': 'Não foi possível obter a Selic no momento'}), 503
    return jsonify(selic)

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    data = request.get_json() or request.form
    try:
        amount = float(data.get('amount', 0))
        years = float(data.get('years', 1))
        compounds = int(data.get('compounds_per_year', 12))
        contribution = float(data.get('periodic_contribution', 0))
        rate = data.get('annual_rate_percent', None)
        
        if rate is None or str(rate).strip() == '':
            selic = fetch_latest_selic()
            if not selic:
                return jsonify({'error': 'Não foi possível obter Selic para simulação'}), 503
            rate = selic['value']
        else:
            rate = float(rate)

        balances = simulate_compound(amount, rate, years, compounds_per_year=compounds, periodic_contribution=contribution)
        final = balances[-1]['balance'] if balances else round(amount * ((1+rate/100)**years),2)
        return jsonify({
            'amount': amount,
            'years': years,
            'annual_rate_percent': rate,
            'compounds_per_year': compounds,
            'periodic_contribution': contribution,
            'series': balances,
            'final_balance': final
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
