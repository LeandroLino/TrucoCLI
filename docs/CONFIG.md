# ⚙️ Guia de Configuração - TrucoCLI

> **Configurações rápidas para personalizar seu jogo**

---

## 🎯 Configurações Essenciais

### 🌐 Jogar em Rede Local (LAN)

**1. No servidor** (quem hospeda)
```bash
# Descubra seu IP local
ifconfig        # Linux/macOS
ipconfig        # Windows

# Exemplo: 192.168.1.100
python3 servidor.py
```

**2. Nos clientes** (quem conecta)
```python
# Edite: config.py
CLIENT_HOST = '192.168.1.100'  # IP do servidor
```

### 🚪 Mudar Porta do Servidor

```python
# Edite: config.py
SERVER_PORT = 5555  # Troque para 5556, 5557, etc
```
💡 **Use portas diferentes para múltiplas salas simultâneas**

### 📊 Ligar/Desligar Estatísticas

```python
# Edite: config.py
ENABLE_STATS = True   # Salva estatísticas em truco_stats.json
ENABLE_STATS = False  # Desabilita estatísticas
```

### 🐛 Modo Debug

```bash
python3 debug.py on     # Ver logs detalhados
python3 debug.py off    # Desligar logs
python3 debug.py        # Alternar on/off
```

---

## ⚡ Ajustar Velocidade do Jogo

Edite `config.py` para tornar o jogo mais rápido ou lento:

```python
# VALORES PADRÃO (recomendado)
CARTA_VENCEDORA_DELAY = 2.0       # Tempo para ver quem ganhou
RESULT_PROCESSING_DELAY = 2.5     # Tempo entre quedas
SCORE_DISPLAY_DELAY = 1.5         # Tempo mostrando placar

# JOGO RÁPIDO (para experts)
CARTA_VENCEDORA_DELAY = 1.0
RESULT_PROCESSING_DELAY = 1.0
SCORE_DISPLAY_DELAY = 0.5

# JOGO LENTO (para aprender)
CARTA_VENCEDORA_DELAY = 3.5
RESULT_PROCESSING_DELAY = 4.0
SCORE_DISPLAY_DELAY = 2.5
```

---

## 🎨 Personalizar Interface

### Cores dos Times

```python
# Edite: config.py
COR_TIME_A = "cyan"      # Opções: cyan, blue, green
COR_TIME_B = "magenta"   # Opções: magenta, red, yellow
```

### Modo de Seleção de Cartas

```python
USE_INTERACTIVE_SELECT = True   # Setas ↑/↓ (recomendado)
USE_INTERACTIVE_SELECT = False  # Digitar números (fallback)
```

---

## 🔧 Solução de Problemas Comuns

### ❌ "Porta já em uso"
```python
# Mude a porta em config.py
SERVER_PORT = 5556  # ou 5557, 5558...
```

### ❌ "Não consigo conectar"
**Verifique:**
1. Servidor está rodando? (`python3 servidor.py`)
2. IP correto? (use `127.0.0.1` para local)
3. Firewall bloqueando? Libere a porta 5555

### ❌ "Jogo muito lento/rápido"
Ajuste os delays (veja seção "Velocidade" acima)

---

## 🌍 Jogar pela Internet (Avançado)

**⚠️ Atenção**: Pickle não é seguro para internet pública!

**Passos:**
1. Servidor precisa ter IP público ou fazer port forwarding
2. Configure roteador: encaminhar porta 5555 para o PC do servidor
3. Clientes editam `config.py`:
   ```python
   CLIENT_HOST = '200.100.50.25'  # IP público do servidor
   ```

---

## 📝 Referência Rápida

| O que você quer | Arquivo | Variável |
|-----------------|---------|----------|
| Mudar IP do servidor | `config.py` | `CLIENT_HOST` |
| Mudar porta | `config.py` | `SERVER_PORT` |
| Acelerar jogo | `config.py` | `*_DELAY` (diminuir valores) |
| Ver logs técnicos | Terminal | `python3 debug.py on` |
| Desligar stats | `config.py` | `ENABLE_STATS = False` |
| Resetar stats | Terminal | `rm truco_stats.json` |

---

## 💡 Dicas

- 🔥 **Primeira vez?** Use configurações padrão!
- 🏠 **LAN?** Só mude `CLIENT_HOST` para IP do servidor
- 🐌 **Aprendendo?** Aumente os delays para 3-4 segundos
- ⚡ **Expert?** Diminua delays para 1 segundo
- 📊 **Quer estatísticas?** Deixe `ENABLE_STATS = True`

---

**📖 Veja também**: `REGRAS.md` para aprender a jogar
