# 🎴 TrucoCLI

Jogo de Truco Paulista para 4 jogadores via terminal.

## 🚀 Como Jogar

### Windows
```bash
# 1. Instalar dependências
pip install rich

# 2. Iniciar servidor (1 terminal/CMD)
python servidor.py

# 3. Conectar jogadores (4 terminais/CMD)
python cliente.py
```

### Linux/macOS
```bash
# 1. Instalar
pip install rich

# 2. Iniciar servidor (1 terminal)
python3 servidor.py

# 3. Conectar jogadores (4 terminais)
python3 cliente.py
```

**⚠️ IMPORTANTE (Windows):**
- Use o **Windows Terminal** ou **CMD** (não Git Bash)
- Para melhor experiência, habilite suporte ANSI no terminal
- As setas direcionais (↑/↓) funcionam para navegação

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
python3 debug.py        # Alternar (Linux/macOS)
python debug.py         # Alternar (Windows)
python3 debug.py on     # Ativar
python3 debug.py off    # Desativar

# Editar config.py para ajustar portas, delays, etc
```

## 🪟 Windows

O jogo funciona **nativamente** no Windows!

**Instalação rápida:**
```cmd
# Duplo clique em:
instalar_windows.bat

# Depois execute:
iniciar_servidor.bat    # 1 janela
iniciar_cliente.bat     # 4 janelas
```

**Recomendações:**
- ✅ Use **Windows Terminal** (melhor experiência)
- ✅ CMD ou PowerShell também funcionam
- ❌ Não use Git Bash

Veja `WINDOWS.md` para detalhes completos.

## 📁 Arquivos

```
TrucoCLI/
├── servidor.py              # Servidor do jogo
├── cliente.py               # Cliente (jogador)
├── config.py                # Configurações
├── utils.py                 # Funções auxiliares (multiplataforma!)
├── stats.py                 # Sistema de estatísticas
├── debug.py                 # Controle de debug
├── test_compat.py           # Teste de compatibilidade
├── WINDOWS.md               # Guia completo Windows
├── instalar_windows.bat     # Instalador Windows
├── iniciar_servidor.bat     # Atalho servidor (Windows)
├── iniciar_cliente.bat      # Atalho cliente (Windows)
└── docs/                    # Documentação detalhada
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
