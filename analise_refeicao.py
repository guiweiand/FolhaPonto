import json

with open('timesheet_webapp_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Análise de Intervalos de Refeição:')
print('=' * 50)

violacoes = 0
conformes = 0

for entry in data['timesheet_data']:
    if entry['tipo'] == 'Trabalho':
        refeicao = entry['total_refeicao']
        data_entry = entry['data']
        
        # Verificar se o intervalo é menor que 1:00 ou vazio
        if refeicao == '':
            print(f'{data_entry}: SEM REGISTRO (❌ Não conforme)')
            violacoes += 1
        elif refeicao and ':' in refeicao:
            horas, minutos = map(int, refeicao.split(':'))
            total_minutos = horas * 60 + minutos
            if total_minutos < 60:
                print(f'{data_entry}: {refeicao} (❌ Não conforme - menor que 1h)')
                violacoes += 1
            else:
                print(f'{data_entry}: {refeicao} (✅ Conforme)')
                conformes += 1

print(f'\nResumo:')
print(f'Violações: {violacoes}')
print(f'Conformes: {conformes}')
