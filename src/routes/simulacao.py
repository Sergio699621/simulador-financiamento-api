from flask import Blueprint, request, jsonify
import math

simulacao_bp = Blueprint('simulacao', __name__)

def calcular_sac(valor_financiado, taxa_juros_mensal, prazo_meses):
    """Calcula financiamento usando Sistema de Amortização Constante (SAC)"""
    amortizacao_mensal = valor_financiado / prazo_meses
    tabela = []
    saldo_devedor = valor_financiado
    total_juros = 0
    
    for mes in range(1, prazo_meses + 1):
        juros_mes = saldo_devedor * taxa_juros_mensal
        parcela = amortizacao_mensal + juros_mes
        saldo_devedor -= amortizacao_mensal
        total_juros += juros_mes
        
        tabela.append({
            'mes': mes,
            'parcela': round(parcela, 2),
            'juros': round(juros_mes, 2),
            'amortizacao': round(amortizacao_mensal, 2),
            'saldoDevedor': round(max(0, saldo_devedor), 2)
        })
    
    return {
        'tabela': tabela,
        'totalJuros': round(total_juros, 2),
        'primeiraParcela': round(tabela[0]['parcela'], 2),
        'ultimaParcela': round(tabela[-1]['parcela'], 2)
    }

def calcular_price(valor_financiado, taxa_juros_mensal, prazo_meses):
    """Calcula financiamento usando Sistema Price (Francês)"""
    if taxa_juros_mensal == 0:
        parcela_fixa = valor_financiado / prazo_meses
    else:
        parcela_fixa = valor_financiado * (taxa_juros_mensal * (1 + taxa_juros_mensal) ** prazo_meses) / ((1 + taxa_juros_mensal) ** prazo_meses - 1)
    
    tabela = []
    saldo_devedor = valor_financiado
    total_juros = 0
    
    for mes in range(1, prazo_meses + 1):
        juros_mes = saldo_devedor * taxa_juros_mensal
        amortizacao_mes = parcela_fixa - juros_mes
        saldo_devedor -= amortizacao_mes
        total_juros += juros_mes
        
        tabela.append({
            'mes': mes,
            'parcela': round(parcela_fixa, 2),
            'juros': round(juros_mes, 2),
            'amortizacao': round(amortizacao_mes, 2),
            'saldoDevedor': round(max(0, saldo_devedor), 2)
        })
    
    return {
        'tabela': tabela,
        'totalJuros': round(total_juros, 2),
        'primeiraParcela': round(parcela_fixa, 2),
        'ultimaParcela': round(parcela_fixa, 2)
    }

@simulacao_bp.route('/simular', methods=['POST'])
def simular_financiamento():
    try:
        dados = request.get_json()
        
        # Validação dos dados de entrada
        valor_imovel = dados.get('valorImovel', 0)
        valor_entrada = dados.get('valorEntrada', 0)
        prazo_anos = dados.get('prazoAnos', 0)
        taxa_juros_anual = dados.get('taxaJuros', 0)
        sistema_amortizacao = dados.get('sistemaAmortizacao', 'sac')
        
        if valor_imovel <= 0 or prazo_anos <= 0 or taxa_juros_anual <= 0:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        if valor_entrada >= valor_imovel:
            return jsonify({'error': 'Valor da entrada deve ser menor que o valor do imóvel'}), 400
        
        # Cálculos
        valor_financiado = valor_imovel - valor_entrada
        taxa_juros_mensal = taxa_juros_anual / 100 / 12
        prazo_meses = prazo_anos * 12
        
        # Escolher sistema de amortização
        if sistema_amortizacao.lower() == 'sac':
            resultado = calcular_sac(valor_financiado, taxa_juros_mensal, prazo_meses)
        else:  # price
            resultado = calcular_price(valor_financiado, taxa_juros_mensal, prazo_meses)
        
        # Preparar resposta
        resposta = {
            'valorImovel': valor_imovel,
            'valorEntrada': valor_entrada,
            'valorFinanciado': valor_financiado,
            'prazoAnos': prazo_anos,
            'prazoMeses': prazo_meses,
            'taxaJuros': taxa_juros_anual,
            'sistemaAmortizacao': sistema_amortizacao.lower(),
            'primeiraParcela': resultado['primeiraParcela'],
            'ultimaParcela': resultado['ultimaParcela'],
            'totalJuros': resultado['totalJuros'],
            'custoTotal': valor_financiado + resultado['totalJuros'],
            'tabela': resultado['tabela']
        }
        
        return jsonify(resposta)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@simulacao_bp.route('/comparar', methods=['POST'])
def comparar_sistemas():
    """Compara os sistemas SAC e Price para os mesmos parâmetros"""
    try:
        dados = request.get_json()
        
        valor_imovel = dados.get('valorImovel', 0)
        valor_entrada = dados.get('valorEntrada', 0)
        prazo_anos = dados.get('prazoAnos', 0)
        taxa_juros_anual = dados.get('taxaJuros', 0)
        
        if valor_imovel <= 0 or prazo_anos <= 0 or taxa_juros_anual <= 0:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        valor_financiado = valor_imovel - valor_entrada
        taxa_juros_mensal = taxa_juros_anual / 100 / 12
        prazo_meses = prazo_anos * 12
        
        # Calcular ambos os sistemas
        resultado_sac = calcular_sac(valor_financiado, taxa_juros_mensal, prazo_meses)
        resultado_price = calcular_price(valor_financiado, taxa_juros_mensal, prazo_meses)
        
        resposta = {
            'valorFinanciado': valor_financiado,
            'sac': {
                'primeiraParcela': resultado_sac['primeiraParcela'],
                'ultimaParcela': resultado_sac['ultimaParcela'],
                'totalJuros': resultado_sac['totalJuros'],
                'custoTotal': valor_financiado + resultado_sac['totalJuros']
            },
            'price': {
                'parcelaFixa': resultado_price['primeiraParcela'],
                'totalJuros': resultado_price['totalJuros'],
                'custoTotal': valor_financiado + resultado_price['totalJuros']
            },
            'diferenca': {
                'juros': resultado_price['totalJuros'] - resultado_sac['totalJuros'],
                'custoTotal': (valor_financiado + resultado_price['totalJuros']) - (valor_financiado + resultado_sac['totalJuros'])
            }
        }
        
        return jsonify(resposta)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

