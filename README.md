# 🎴 TrucoCLI

Jogo de Truco para 4 jogadores via terminal usando Python e Rich.

## 🚀 Quick Start

```bash
# Instalar dependências
pip install rich

# Terminal 1 - Servidor
python3 servidor_truco_refatorado.py

# Terminais 2, 3, 4, 5 - Clientes (4 jogadores)
python3 cliente_truco_refatorado.py
```

## 📋 Requisitos

- Python 3.7+
- rich (`pip install rich`)

## 🎮 Como Jogar

### **Times:**
- **Time A** (🔵): Jogadores 0 e 2
- **Time B** (🔴): Jogadores 1 e 3

### **Comandos no Jogo:**
- `0`, `1`, `2` - Jogar carta (índice da mão)
- `T` - Pedir Truco
- `V0`, `V1`, `V2` - Jogar carta virada (a partir da 2ª queda)

### **Responder Truco:**
- `S` - Aceitar
- `N` - Correr
- `A` - Aumentar (6, 9, 12)

## 🔧 Configuração

### **Ativar/Desativar Debug:**
```bash
python3 toggle_debug.py status  # Ver status
python3 toggle_debug.py on      # Ativar
python3 toggle_debug.py off     # Desativar
python3 toggle_debug.py         # Alternar
```

### **Editar Configurações:**
Edite `config.py` para ajustar:
- Portas e hosts
- Tempos de delay
- Pontos para vitória
- etc.

## 📁 Estrutura do Projeto

```
TrucoCLI/
├── config.py                      # Configurações
├── utils.py                       # Funções utilitárias
├── servidor_truco_refatorado.py   # Servidor (USE ESTE)
├── cliente_truco_refatorado.py    # Cliente (USE ESTE)
├── toggle_debug.py                # Controle de debug
├── servidor_truco_4p.py           # [Versão antiga]
├── cliente_truco_4p.py            # [Versão antiga]
└── README.md                      # Este arquivo
```

## 📖 Documentação

- [REFATORACAO_COMPLETA.md](REFATORACAO_COMPLETA.md) - Detalhes da refatoração
- [REFATORACAO.md](REFATORACAO.md) - Histórico de melhorias

## 🎯 Features

- ✅ Jogo completo de Truco Paulista (4 jogadores)
- ✅ Sistema de Truco/6/9/12
- ✅ Mão de 11
- ✅ Carta virada
- ✅ Interface colorida (Rich)
- ✅ Debug configurável
- ✅ Tratamento robusto de erros
- ✅ Código refatorado e documentado

## 🐛 Debug

Com debug ativado, você verá logs detalhados:
```
[20:01:18] [DEBUG] → Enviando TURN para Jogador1 (ID 0)
[20:01:18] [DEBUG] → TURN enviado para Jogador1
[20:01:18] [DEBUG] → Aguardando resposta de Jogador1...
```

## 📝 Regras do Truco

- **Objetivo:** Primeiro time a fazer 12 pontos vence
- **Quedas:** Melhor de 3 por mão
- **Valores:** 1 ponto (normal), 3 (truco), 6, 9, 12
- **Mão de 11:** Times com 11 pontos veem mão do parceiro
- **Manilha:** Carta imediatamente superior ao vira

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'feat: Minha feature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📜 Licença

MIT License - veja LICENSE para detalhes

## 👨‍💻 Autor

Desenvolvido com ❤️ usando Python e Rich
