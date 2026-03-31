# 🎴 TrucoCLI

Jogo de Truco Paulista para 4 jogadores via terminal.

## 🚀 Como Jogar

```bash
# 1. Instalar
pip install rich

# 2. Iniciar servidor (1 terminal)
python3 servidor.py

# 3. Conectar jogadores (4 terminais)
python3 cliente.py
```

## 🎮 Comandos

### Lobby (escolha de times)
- `A` - Entrar no Time A (🔵)
- `B` - Entrar no Time B (🔴)
- `S` - Sair do time
- `R` - Marcar pronto

### Durante o jogo
- `0`, `1`, `2` - Jogar carta
- `T` - Pedir Truco
- `V0`, `V1`, `V2` - Jogar carta virada

### Responder Truco
- `S` - Aceitar
- `N` - Correr
- `A` - Aumentar (6/9/12)

### Comandos especiais
- `/ajuda` - Mostrar ajuda
- `/stats` - Ver estatísticas
- `/sair` - Sair do jogo

## ⚙️ Configuração

```bash
# Debug
python3 debug.py        # Alternar
python3 debug.py on     # Ativar
python3 debug.py off    # Desativar

# Editar config.py para ajustar portas, delays, etc
```

## 📁 Arquivos

```
TrucoCLI/
├── servidor.py        # Servidor do jogo
├── cliente.py         # Cliente (jogador)
├── config.py          # Configurações
├── utils.py           # Funções auxiliares
├── stats.py           # Sistema de estatísticas
├── debug.py           # Controle de debug
└── docs/              # Documentação detalhada
```

## ✨ Features

- ✅ Lobby com escolha de times
- ✅ Truco Paulista completo (1/3/6/9/12)
- ✅ Mão de 11
- ✅ Carta virada
- ✅ Interface colorida
- ✅ Estatísticas persistentes

## 📖 Mais Info

Veja a pasta `docs/` para documentação detalhada.

---

**Python 3.7+ • Rich library • MIT License**
