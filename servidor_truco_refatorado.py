import socket
import pickle
import random
import time
from config import *
from utils import log, debug_log, get_time_jogador, get_adversarios, get_emoji_time, calcular_forca_carta, formatar_carta

class TrucoServer:
    def __init__(self, host=SERVER_HOST, port=SERVER_PORT):
        """Inicializa o servidor de Truco"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(MAX_PLAYERS)
        
        self.clients = []
        self.nicks = {}
        self.pontos_geral = {time: 0 for time in TIMES}
        self.valor_mao = VALOR_INICIAL
        self.time_ultimo_aumento = None
        
        log(f"Servidor inicializado em {host}:{port}")

    def broadcast(self, data):
        """Envia dados para todos os clientes conectados"""
        for idx, c in enumerate(self.clients):
            try:
                c.sendall(pickle.dumps(data))
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                log(f"Erro ao enviar broadcast para {self.nicks.get(idx, 'Unknown')}: {e}", "ERROR")
        time.sleep(BROADCAST_DELAY)

    def enviar_para_jogador(self, jogador_id, data):
        """Envia dados para um jogador específico"""
        try:
            self.clients[jogador_id].sendall(pickle.dumps(data))
            return True
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            log(f"Erro ao enviar para {self.nicks[jogador_id]}: {e}", "ERROR")
            return False

    def receber_de_jogador(self, jogador_id):
        """Recebe dados de um jogador específico"""
        try:
            return pickle.loads(self.clients[jogador_id].recv(BUFFER_SIZE))
        except (EOFError, ConnectionResetError, BrokenPipeError, OSError) as e:
            log(f"Erro ao receber de {self.nicks[jogador_id]}: {e}", "ERROR")
            return None

    def notificar_outros_jogadores(self, jogador_atual):
        """Notifica outros jogadores que não é a vez deles"""
        for j in range(MAX_PLAYERS):
            if j != jogador_atual:
                self.enviar_para_jogador(j, {"tipo": MsgType.WAIT_TURN, "player": jogador_atual})

    def get_proximo_valor_truco(self):
        """Retorna o próximo valor de truco"""
        return VALORES_TRUCO.get(self.valor_mao, VALOR_MAXIMO)

    def pode_aumentar_truco(self, time):
        """Verifica se o time pode aumentar o truco"""
        return self.time_ultimo_aumento != time

    def gerenciar_truco(self, quem_pediu):
        """Gerencia pedido de truco/aumento de aposta"""
        time_pediu = get_time_jogador(quem_pediu)
        
        if not self.pode_aumentar_truco(time_pediu):
            self.enviar_para_jogador(quem_pediu, {
                "tipo": MsgType.UPDATE, 
                "msg": "❌ Seu time já aumentou!"
            })
            return TrucoResponse.BLOQUEADO
        
        prox_valor = self.get_proximo_valor_truco()
        self.broadcast({
            "tipo": MsgType.UPDATE, 
            "msg": f"🔥 {self.nicks[quem_pediu]} PEDIU {prox_valor}!"
        })
        
        adversarios = get_adversarios(time_pediu)
        adversario_responde = adversarios[0]
        
        if not self.enviar_para_jogador(adversario_responde, {
            "tipo": MsgType.ASK_TRUCO, 
            "msg": f"Aceita {prox_valor}? (S)im/(N)ão/(A)umentar"
        }):
            return TrucoResponse.CORREU
        
        resp = self.receber_de_jogador(adversario_responde)
        if resp is None:
            return TrucoResponse.CORREU
        
        resp = resp.upper()
        
        if resp == RESPOSTA_SIM:
            self.valor_mao = prox_valor
            self.time_ultimo_aumento = time_pediu
            return TrucoResponse.ACEITO
        elif resp == RESPOSTA_AUMENTAR and prox_valor < VALOR_MAXIMO:
            self.valor_mao = prox_valor
            self.time_ultimo_aumento = time_pediu
            return self.gerenciar_truco(adversario_responde)
        
        return TrucoResponse.CORREU

    def distribuir_cartas(self):
        """Distribui cartas e retorna (maos, vira, manilha)"""
        cartas = [(v, n) for v in ORDEM_CARTAS for n in NAIPES]
        random.shuffle(cartas)
        vira = cartas.pop()
        manilha = ORDEM_CARTAS[(ORDEM_CARTAS.index(vira[0]) + 1) % len(ORDEM_CARTAS)]
        maos = [[cartas.pop() for _ in range(CARTAS_POR_JOGADOR)] for _ in range(MAX_PLAYERS)]
        return maos, vira, manilha

    def calcular_posicoes(self, primeiro_jogador):
        """Calcula mapa de posições baseado em quem começa"""
        ordem = [(primeiro_jogador + i) % MAX_PLAYERS for i in range(MAX_PLAYERS)]
        return {ordem[i]: POSICOES[i] for i in range(MAX_PLAYERS)}

    def atualizar_posicoes_jogadores(self, pos_map):
        """Atualiza posições de todos os jogadores"""
        debug_log("Enviando UPDATE_POS para todos os jogadores")
        for i in range(MAX_PLAYERS):
            self.enviar_para_jogador(i, {
                "tipo": MsgType.UPDATE_POS, 
                "posicao": pos_map[i]
            })
            debug_log(f"UPDATE_POS enviado para {self.nicks[i]}: {pos_map[i]}")

    def enviar_mao_onze(self, time, maos):
        """Envia informação de mão de 11 para o time"""
        log(f"   ⚠️  Mão de 11 para TIME {time}!", "GAME")
        jogadores = TIME_A_JOGADORES if time == "A" else TIME_B_JOGADORES
        
        for j, p in [(jogadores[0], jogadores[1]), (jogadores[1], jogadores[0])]:
            self.enviar_para_jogador(j, {
                "tipo": MsgType.ONZE, 
                "parceiro": maos[p], 
                "nick_p": self.nicks[p]
            })

    def enviar_inicio_mao(self, maos, vira, pos_map, mao_ferro):
        """Envia informações de início de mão para todos os jogadores"""
        for i in range(MAX_PLAYERS):
            self.enviar_para_jogador(i, {
                "tipo": MsgType.START,
                "mao": maos[i],
                "vira": vira,
                "id": i,
                "time": get_time_jogador(i),
                "ferro": mao_ferro,
                "posicao": pos_map[i]
            })

    def processar_jogada(self, idx, queda, manilha):
        """Processa a jogada de um jogador e retorna dados da jogada"""
        debug_log(f"Enviando TURN para {self.nicks[idx]} (ID {idx})")
        
        if not self.enviar_para_jogador(idx, {
            "tipo": MsgType.TURN,
            "player": idx,
            "n_queda": queda,
            "valor": self.valor_mao
        }):
            return None
        
        debug_log(f"TURN enviado para {self.nicks[idx]}")
        self.notificar_outros_jogadores(idx)
        debug_log("WAIT_TURN enviado para outros 3 jogadores")
        
        debug_log(f"Aguardando resposta de {self.nicks[idx]}...")
        resp_data = self.receber_de_jogador(idx)
        
        if resp_data is None:
            return None
        
        debug_log(f"RECEBEU resposta de {self.nicks[idx]}: {type(resp_data)}")
        
        # Verifica se é pedido de truco
        if resp_data == ACAO_TRUCO:
            res = self.gerenciar_truco(idx)
            if res == TrucoResponse.CORREU:
                return {"tipo": "CORREU", "time_ganhou": get_time_jogador(idx)}
            
            # Pede carta novamente após truco
            if not self.enviar_para_jogador(idx, {
                "tipo": MsgType.TURN,
                "player": idx,
                "n_queda": queda,
                "valor": self.valor_mao
            }):
                return None
            
            resp_data = self.receber_de_jogador(idx)
            if resp_data is None:
                return None
        
        # Processa a carta jogada
        carta, virada = resp_data
        time_jogador = get_time_jogador(idx)
        emoji_time = get_emoji_time(time_jogador)
        
        if virada:
            forca = -1
            msg = f"{emoji_time} {self.nicks[idx]} (Time {time_jogador}) jogou CARTA VIRADA"
            carta_display = "VIRADA"
        else:
            forca = calcular_forca_carta(carta, manilha)
            carta_display = formatar_carta(carta)
            msg = f"{emoji_time} {self.nicks[idx]} (Time {time_jogador}) jogou {carta_display}"
        
        self.broadcast({
            "tipo": MsgType.UPDATE,
            "msg": msg,
            "jogador_id": idx,
            "forca": forca
        })
        
        return {
            "tipo": "JOGADA",
            "id": idx,
            "forca": forca,
            "carta": carta_display,
            "nick": self.nicks[idx],
            "time": time_jogador
        }

    def determinar_vencedor_queda(self, mesa):
        """Determina o vencedor de uma queda"""
        maior = max(m["forca"] for m in mesa)
        vencedores = [m for m in mesa if m["forca"] == maior]
        
        # Verifica empate entre times diferentes
        if len(vencedores) > 1 and vencedores[0]["id"] % 2 != vencedores[1]["id"] % 2:
            return "EMPATE", None
        
        time_vencedor = get_time_jogador(vencedores[0]["id"])
        proximo_jogador = vencedores[0]["id"] if vencedores else None
        
        return time_vencedor, proximo_jogador

    def aplicar_logica_canga(self, vitorias_queda):
        """Aplica lógica de vitória (canga)"""
        if vitorias_queda.count("A") == 2:
            log(f"✅ TIME A venceu a mão! (+{self.valor_mao} pontos)", "GAME")
            return "A"
        
        if vitorias_queda.count("B") == 2:
            log(f"✅ TIME B venceu a mão! (+{self.valor_mao} pontos)", "GAME")
            return "B"
        
        if len(vitorias_queda) >= 2:
            # Primeiro empate, segundo vitória
            if vitorias_queda[0] == "EMPATE" and vitorias_queda[-1] != "EMPATE":
                log(f"✅ TIME {vitorias_queda[-1]} venceu (1º empate, 2º {vitorias_queda[-1]})", "GAME")
                return vitorias_queda[-1]
            
            # Primeiro vitória, segundo empate
            if vitorias_queda[-1] == "EMPATE" and vitorias_queda[0] != "EMPATE":
                log(f"✅ TIME {vitorias_queda[0]} venceu (1º {vitorias_queda[0]}, 2º empate)", "GAME")
                return vitorias_queda[0]
        
        return None

    def processar_queda(self, queda, primeiro, manilha):
        """Processa uma queda completa"""
        log(f"   >>> Queda {queda} | Valor: {self.valor_mao} | Inicia: {self.nicks[primeiro]}", "GAME")
        
        # Limpa logs visuais no cliente após primeira queda
        if queda > 1:
            debug_log("Enviando CLEAR_LOGS via broadcast")
            self.broadcast({"tipo": MsgType.CLEAR_LOGS})
            debug_log("CLEAR_LOGS enviado")
            time.sleep(CLEAR_LOGS_DELAY)
            debug_log(f"Aguardou {CLEAR_LOGS_DELAY}s após CLEAR_LOGS")
        
        mesa = []
        
        # Cada jogador joga
        for i in range(MAX_PLAYERS):
            idx = (primeiro + i) % MAX_PLAYERS
            resultado = self.processar_jogada(idx, queda, manilha)
            
            if resultado is None:
                # Desconexão
                time_adversario = "B" if idx % 2 == 0 else "A"
                return {"tipo": "DESCONEXAO", "time_ganhou": time_adversario}
            
            if resultado["tipo"] == "CORREU":
                return resultado
            
            mesa.append(resultado)
        
        # Determina vencedor da queda
        time.sleep(CARTA_VENCEDORA_DELAY)
        
        venc_queda, proximo = self.determinar_vencedor_queda(mesa)
        vencedor_nome = self.nicks[proximo] if proximo is not None else "EMPATE"
        
        # Atualiza posições se não for última queda e não for empate
        if queda < QUEDAS_POR_MAO and venc_queda != "EMPATE":
            pos_map = self.calcular_posicoes(proximo)
            self.atualizar_posicoes_jogadores(pos_map)
        
        log(f"   Resultado Queda {queda}: {venc_queda} ({vencedor_nome}) | Próximo: {self.nicks[proximo] if proximo else 'N/A'}", "GAME")
        debug_log("Enviando RESULT via broadcast")
        self.broadcast({
            "tipo": MsgType.RESULT,
            "msg": f"Vencedor: {vencedor_nome} (Time {venc_queda}) - {self.nicks[proximo] if proximo else 'N/A'} abre próxima"
        })
        
        time.sleep(RESULT_PROCESSING_DELAY)
        
        return {"tipo": "VITORIA_QUEDA", "time": venc_queda, "proximo": proximo}

    def processar_mao(self, pe_idx=0):
        """Processa uma mão completa"""
        log(f"🎴 Nova mão iniciada | Placar: A={self.pontos_geral['A']} B={self.pontos_geral['B']}", "GAME")
        
        self.valor_mao = VALOR_INICIAL
        self.time_ultimo_aumento = None
        
        mao_ferro = (self.pontos_geral["A"] == 11 and self.pontos_geral["B"] == 11)
        
        # Distribui cartas
        maos, vira, manilha = self.distribuir_cartas()
        
        log(f"   Vira: {formatar_carta(vira, usar_simbolo=False)} | Manilha: {manilha}", "GAME")
        
        # Calcula posições iniciais
        pos_map = self.calcular_posicoes(pe_idx)
        log(f"   Posições: {' | '.join([f'{self.nicks[i]} ({pos_map[i]})' for i in range(MAX_PLAYERS)])}", "GAME")
        
        # Mão de Onze (se não for mão de ferro)
        if not mao_ferro:
            for time in TIMES:
                if self.pontos_geral[time] == 11:
                    self.enviar_mao_onze(time, maos)
        
        # Envia início de mão
        self.enviar_inicio_mao(maos, vira, pos_map, mao_ferro)
        
        # Processa as 3 quedas
        vitorias_queda = []
        primeiro = pe_idx
        
        for queda in range(1, QUEDAS_POR_MAO + 1):
            resultado = self.processar_queda(queda, primeiro, manilha)
            
            if resultado["tipo"] == "DESCONEXAO":
                return resultado["time_ganhou"], True
            
            if resultado["tipo"] == "CORREU":
                return resultado["time_ganhou"], True
            
            vitorias_queda.append(resultado["time"])
            if resultado["proximo"] is not None:
                primeiro = resultado["proximo"]
            
            # Verifica vitória antecipada (canga)
            vencedor = self.aplicar_logica_canga(vitorias_queda)
            if vencedor:
                return vencedor, False
        
        log(f"⚖️  Mão empatou!", "GAME")
        return "EMPATE", False

    def start(self):
        """Inicia o servidor e gerencia a partida"""
        log("Servidor Online. Aguardando 4 nicks...", "WAIT")
        
        # Aguarda 4 jogadores
        while len(self.clients) < MAX_PLAYERS:
            try:
                c, addr = self.server.accept()
                log(f"   Conexão recebida de {addr}", "INFO")
                nick = pickle.loads(c.recv(BUFFER_SIZE))
                self.nicks[len(self.clients)] = nick
                self.clients.append(c)
                log(f"   Jogador {len(self.clients)}/{MAX_PLAYERS} conectado: {nick}", "WAIT")
            except (EOFError, ConnectionResetError, OSError) as e:
                log(f"Erro ao conectar cliente: {e}", "ERROR")
                continue
        
        log("🎮 Todos conectados! Iniciando partida...", "INFO")
        self.broadcast({"tipo": MsgType.NICKS, "lista": self.nicks})
        
        # Loop principal da partida
        pe_atual = 0
        while max(self.pontos_geral.values()) < PONTOS_VITORIA:
            vencedor, foi_wo = self.processar_mao(pe_atual)
            
            if vencedor != "EMPATE":
                pontos = self.valor_mao if not foi_wo else 1
                self.pontos_geral[vencedor] += pontos
                log(f"📊 Placar atualizado: A={self.pontos_geral['A']} B={self.pontos_geral['B']}", "INFO")
            
            self.broadcast({"tipo": MsgType.SCORE, "placar": self.pontos_geral})
            time.sleep(SCORE_DISPLAY_DELAY)
            
            pe_atual = (pe_atual + 1) % MAX_PLAYERS
            log("⏳ Aguardando próxima mão...", "WAIT")
        
        vencedor_final = "A" if self.pontos_geral["A"] >= PONTOS_VITORIA else "B"
        log(f"🏆 FIM DE JOGO! Vencedor: TIME {vencedor_final}", "INFO")

if __name__ == "__main__":
    TrucoServer().start()
