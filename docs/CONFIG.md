# ⚙️ Configuração

## Debug

```bash
# Alternar debug on/off
python3 debug.py

# Comandos específicos
python3 debug.py on       # Ativar
python3 debug.py off      # Desativar
python3 debug.py status   # Ver status atual
```

Com debug ativado, você verá logs detalhados no servidor:
```
[20:01:18] [DEBUG] → Enviando TURN para João (ID 0)
[20:01:18] [DEBUG] → TURN enviado para João
[20:01:18] [DEBUG] → Aguardando resposta...
```

## Arquivo config.py

### Rede
```python
SERVER_HOST = '0.0.0.0'      # Aceita conexões de qualquer IP
SERVER_PORT = 5555           # Porta do servidor
CLIENT_HOST = '127.0.0.1'    # IP para conectar (localhost)
```

### Regras do Jogo
```python
PONTOS_VITORIA = 12          # Pontos para vencer
CARTAS_POR_JOGADOR = 3       # Cartas na mão
QUEDAS_POR_MAO = 3           # Quedas por mão (melhor de 3)
```

### Timing (em segundos)
```python
BROADCAST_DELAY = 0.05              # Delay entre mensagens
CARTA_VENCEDORA_DELAY = 2.0         # Mostrar carta vencedora
RESULT_PROCESSING_DELAY = 2.5       # Processar resultado
SCORE_DISPLAY_DELAY = 1.5           # Mostrar placar
LOBBY_UPDATE_INTERVAL = 0.5         # Atualização do lobby
```

### Estatísticas
```python
ENABLE_STATS = True          # Ativar sistema de estatísticas
```

Arquivo de estatísticas: `truco_stats.json` (criado automaticamente)

### Cores da Interface
```python
COR_TIME_A = "cyan"          # Cor do Time A
COR_TIME_B = "magenta"       # Cor do Time B
COR_VENCEDOR = "bold green"  # Destaque vencedor
COR_ERRO = "bold red"        # Mensagens de erro
```

## Jogar em Rede Local

### Servidor
```bash
# No computador que vai hospedar
python3 servidor.py
```

### Clientes
```bash
# Descubra o IP do servidor
# Linux/Mac: ifconfig
# Windows: ipconfig

# Edite config.py nos clientes:
CLIENT_HOST = '192.168.1.100'  # IP do servidor

# Conecte
python3 cliente.py
```

## Múltiplas Salas

Para ter várias salas simultâneas, rode servidores em portas diferentes:

```bash
# Sala 1
python3 servidor.py --port 5555

# Sala 2
python3 servidor.py --port 5556

# Sala 3
python3 servidor.py --port 5557
```

Clientes especificam a porta ao conectar.

## Troubleshooting

### Porta em uso
```
Erro: Address already in use
```
**Solução:** Mude `SERVER_PORT` em `config.py`

### Timeout no lobby
```
Erro de conexão: timed out
```
**Solução:** Aumente `LOBBY_UPDATE_INTERVAL` para 1.0

### Firewall bloqueando
```
Erro: Connection refused
```
**Solução:** 
- Libere porta 5555 no firewall
- Linux: `sudo ufw allow 5555`
- Windows: Adicione regra no Windows Firewall
