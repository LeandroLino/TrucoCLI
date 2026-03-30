"""
Configurações centralizadas do TrucoCLI
"""

# ===== REDE =====
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5555
CLIENT_HOST = '127.0.0.1'
BUFFER_SIZE = 4096
MAX_PLAYERS = 4

# ===== GAME RULES =====
ORDEM_CARTAS = ["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"]
NAIPES = {"Ouros": 1, "Espadas": 2, "Copas": 3, "Paus": 4}
NAIPE_SIMBOLOS = {"Ouros": "♦", "Espadas": "♠", "Copas": "♥", "Paus": "♣"}
CARTAS_POR_JOGADOR = 3
QUEDAS_POR_MAO = 3
PONTOS_VITORIA = 12

# ===== TRUCO VALUES =====
VALOR_INICIAL = 1
VALORES_TRUCO = {1: 3, 3: 6, 6: 9, 9: 12}
VALOR_MAXIMO = 12

# ===== POSIÇÕES =====
POSICOES = ["Mão", "Contra-Pé", "Par Mão", "Pé"]
POSICOES_EMOJI = {
    "Mão": "👑",
    "Contra-Pé": "⚔️",
    "Par Mão": "🤝",
    "Pé": "🎯"
}

# ===== TIMES =====
TIMES = ["A", "B"]
TIME_A_JOGADORES = [0, 2]
TIME_B_JOGADORES = [1, 3]

# ===== TIMING (segundos) =====
BROADCAST_DELAY = 0.05
CARTA_VENCEDORA_DELAY = 2.0
RESULT_PROCESSING_DELAY = 2.5
CLEAR_LOGS_DELAY = 0.3
ONZE_DISPLAY_DELAY = 3.0
SCORE_DISPLAY_DELAY = 1.5
ANIMACAO_VENCEDOR_DELAY = 0.15
BARRA_PROGRESSO_DELAY = 0.05

# ===== DEBUG =====
DEBUG_MODE = False  # Mude para True para ativar logs de debug

# ===== UI COLORS =====
NAIPES_VERMELHOS = ["Ouros", "Copas"]
COR_TIME_A = "cyan"
COR_TIME_B = "magenta"
COR_VENCEDOR = "bold green"
COR_PERDEDOR = "dim white"
COR_ALERTA = "bold yellow"
COR_ERRO = "bold red"
COR_SUCESSO = "bold green"
COR_INFO = "bold blue"

# ===== UI ICONS =====
ICON_TRUCO = "🔥"
ICON_VITORIA = "🏆"
ICON_DERROTA = "😢"
ICON_EMPATE = "🤝"
ICON_CARTA_ALTA = "⭐"
ICON_MANILHA = "💎"
ICON_STATS = "📊"
ICON_AJUDA = "❓"
ICON_PONTOS = "🎯"

# ===== PROTOCOL MESSAGE TYPES =====
class MsgType:
    """Tipos de mensagens do protocolo"""
    NICKS = "NICKS"
    START = "START"
    ONZE = "ONZE"
    TURN = "TURN"
    WAIT_TURN = "WAIT_TURN"
    ASK_TRUCO = "ASK_TRUCO"
    UPDATE = "UPDATE"
    UPDATE_POS = "UPDATE_POS"
    CLEAR_LOGS = "CLEAR_LOGS"
    RESULT = "RESULT"
    SCORE = "SCORE"

# ===== TRUCO RESPONSES =====
class TrucoResponse:
    """Respostas possíveis para pedido de truco"""
    ACEITO = "ACEITO"
    CORREU = "CORREU"
    BLOQUEADO = "BLOQUEADO"

# ===== PLAYER ACTIONS =====
ACAO_TRUCO = "TRUCO"
RESPOSTA_SIM = "S"
RESPOSTA_NAO = "N"
RESPOSTA_AUMENTAR = "A"
RESPOSTAS_VALIDAS = [RESPOSTA_SIM, RESPOSTA_NAO, RESPOSTA_AUMENTAR]

# ===== COMANDOS ESPECIAIS =====
CMD_AJUDA = "/AJUDA"
CMD_STATS = "/STATS"
CMD_SAIR = "/SAIR"
COMANDOS_ESPECIAIS = [CMD_AJUDA, CMD_STATS, CMD_SAIR]

# ===== MENSAGENS =====
MSG_AJUDA = """
╔══════════════════════════════════════════════════════════╗
║                    🎴 COMO JOGAR TRUCO                   ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  JOGAR CARTAS:                                           ║
║    0, 1, 2  → Jogar carta pelo índice                    ║
║    V0, V1   → Virar carta (a partir da 2ª queda)         ║
║                                                          ║
║  TRUCO:                                                  ║
║    T        → Pedir Truco/Aumentar                       ║
║    S        → Aceitar truco                              ║
║    N        → Correr (desistir)                          ║
║    A        → Aumentar aposta                            ║
║                                                          ║
║  COMANDOS:                                               ║
║    /ajuda   → Mostrar esta ajuda                         ║
║    /stats   → Ver estatísticas                           ║
║    /sair    → Sair do jogo                               ║
║                                                          ║
║  OBJETIVO:                                               ║
║    Primeiro time a fazer 12 pontos vence!                ║
║                                                          ║
║  MANILHAS (em ordem):                                    ║
║    💎 Paus > Copas > Espadas > Ouros                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

# ===== STATS =====
ENABLE_STATS = True  # Ativar sistema de estatísticas
