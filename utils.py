"""
Funções utilitárias compartilhadas
"""
from datetime import datetime
import sys
import platform
from config import DEBUG_MODE

def log(msg, nivel="INFO"):
    """Log com timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{nivel}] {msg}")

def debug_log(msg):
    """Log apenas se DEBUG_MODE estiver ativo"""
    if DEBUG_MODE:
        log(msg, "DEBUG")

def get_key_multiplataforma():
    """
    Captura uma tecla do teclado de forma multiplataforma
    Funciona em Windows, Linux e macOS
    """
    sistema = platform.system()
    
    if sistema == "Windows":
        # Windows: usa msvcrt
        import msvcrt
        
        # Espera por uma tecla
        while not msvcrt.kbhit():
            pass
        
        ch = msvcrt.getch()
        
        # Detecta teclas especiais (setas, etc)
        if ch in (b'\x00', b'\xe0'):  # Prefixo de tecla especial
            ch2 = msvcrt.getch()
            # Retorna o código da tecla especial como caractere
            return chr(224) if ch == b'\xe0' else chr(0)
        
        # Decodifica byte normal
        try:
            decoded = ch.decode('utf-8', errors='ignore')
            return decoded if decoded else chr(ch[0])
        except:
            return chr(ch[0]) if len(ch) > 0 else ''
    
    else:
        # Unix/Linux/macOS: usa tty e termios
        import tty
        import termios
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def get_time_jogador(jogador_id):
    """Retorna o time (A ou B) baseado no ID do jogador"""
    return "A" if jogador_id % 2 == 0 else "B"

def get_adversarios(time):
    """Retorna lista de IDs dos adversários"""
    from config import TIME_A_JOGADORES, TIME_B_JOGADORES
    return TIME_B_JOGADORES if time == "A" else TIME_A_JOGADORES

def get_parceiro(jogador_id):
    """Retorna o ID do parceiro"""
    return (jogador_id + 2) % 4

def get_emoji_time(time):
    """Retorna emoji do time"""
    return "🔵" if time == "A" else "🔴"

def calcular_forca_carta(carta, manilha):
    """Calcula a força de uma carta"""
    from config import ORDEM_CARTAS, NAIPES
    valor, naipe = carta
    if valor == manilha:
        return 100 + NAIPES[naipe]
    return ORDEM_CARTAS.index(valor)

def e_carta_vermelha(naipe):
    """Verifica se o naipe é vermelho"""
    from config import NAIPES_VERMELHOS
    return naipe in NAIPES_VERMELHOS

def formatar_carta(carta, usar_simbolo=True):
    """Formata carta para exibição"""
    from config import NAIPE_SIMBOLOS
    valor, naipe = carta
    if usar_simbolo:
        return f"{valor}{NAIPE_SIMBOLOS.get(naipe, naipe[0])}"
    return f"{valor} de {naipe}"

def criar_barra_progresso(atual, maximo, largura=20):
    """Cria barra de progresso visual"""
    preenchido = int((atual / maximo) * largura)
    vazio = largura - preenchido
    return f"[{'█' * preenchido}{'░' * vazio}] {atual}/{maximo}"

def get_emoji_posicao(posicao):
    """Retorna emoji da posição"""
    from config import POSICOES_EMOJI
    return POSICOES_EMOJI.get(posicao, "")

def e_manilha(carta, manilha):
    """Verifica se a carta é manilha"""
    return carta[0] == manilha

def get_nome_manilha(manilha):
    """Retorna o nome descritivo da manilha"""
    nomes = {
        "4": "Quatro", "5": "Cinco", "6": "Seis", "7": "Sete",
        "Q": "Dama", "J": "Valete", "K": "Rei", "A": "Ás",
        "2": "Dois", "3": "Três"
    }
    return nomes.get(manilha, manilha)

def animar_texto(texto, delay=0.05):
    """Retorna texto com efeito de animação (para simulação)"""
    import time
    # Simulação simples - em produção pode usar rich.live
    return texto

def formatar_carta_para_select(carta, index, manilha=None):
    """Formata carta para exibição no menu de seleção"""
    from config import NAIPE_SIMBOLOS
    valor, naipe = carta
    naipe_simbolo = NAIPE_SIMBOLOS.get(naipe, naipe[0])
    
    # Adiciona indicador se for manilha
    if manilha and e_manilha(carta, manilha):
        return f"[{index}] {valor}{naipe_simbolo} 💎"
    
    return f"[{index}] {valor}{naipe_simbolo}"
