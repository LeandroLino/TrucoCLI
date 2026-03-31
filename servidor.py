import socket
import pickle
import random
import time
import string
from config import *
from utils import log, debug_log, get_time_jogador, get_adversarios, get_emoji_time, calcular_forca_carta, formatar_carta

class Lobby:
    """Gerencia o lobby de espera antes do jogo começar"""
    def __init__(self, sala_id):
        self.sala_id = sala_id
        self.jogadores = {}  # {socket: {"nick": str, "time": str, "pronto": bool}}
        self.team_a = []
        self.team_b = []
    
    def adicionar_jogador(self, client_socket, nick):
        """Adiciona jogador ao lobby"""
        self.jogadores[client_socket] = {
            "nick": nick,
            "time": None,
            "pronto": False
        }
        log(f"   {nick} entrou no lobby. ({len(self.jogadores)}/4)", "LOBBY")
    
    def sair_time(self, client_socket):
        """Remove jogador do time atual"""
        if client_socket not in self.jogadores:
            return False
        
        old_time = self.jogadores[client_socket]["time"]
        
        # Remove do time
        if old_time == "A" and client_socket in self.team_a:
            self.team_a.remove(client_socket)
        elif old_time == "B" and client_socket in self.team_b:
            self.team_b.remove(client_socket)
        
        # Reseta estado do jogador
        self.jogadores[client_socket]["time"] = None
        self.jogadores[client_socket]["pronto"] = False
        
        return True
    
    def mudar_time(self, client_socket, time):
        """Muda jogador de time"""
        if client_socket not in self.jogadores:
            return False
        
        # Pega o time atual do jogador
        old_time = self.jogadores[client_socket]["time"]
        
        # Se já está no time solicitado, não faz nada
        if old_time == time:
            return True
        
        # Remove do time anterior ANTES de verificar vagas
        if old_time == "A" and client_socket in self.team_a:
            self.team_a.remove(client_socket)
            self.jogadores[client_socket]["time"] = None
        elif old_time == "B" and client_socket in self.team_b:
            self.team_b.remove(client_socket)
            self.jogadores[client_socket]["time"] = None
        
        # Agora verifica vagas no novo time
        if time == "A":
            if len(self.team_a) < 2:
                self.team_a.append(client_socket)
                self.jogadores[client_socket]["time"] = "A"
                # Limpa flag de pronto ao mudar de time
                self.jogadores[client_socket]["pronto"] = False
                return True
            else:
                # Time cheio - volta para o time anterior
                if old_time == "A":
                    self.team_a.append(client_socket)
                    self.jogadores[client_socket]["time"] = "A"
                elif old_time == "B":
                    self.team_b.append(client_socket)
                    self.jogadores[client_socket]["time"] = "B"
                return False
        
        elif time == "B":
            if len(self.team_b) < 2:
                self.team_b.append(client_socket)
                self.jogadores[client_socket]["time"] = "B"
                # Limpa flag de pronto ao mudar de time
                self.jogadores[client_socket]["pronto"] = False
                return True
            else:
                # Time cheio - volta para o time anterior
                if old_time == "A":
                    self.team_a.append(client_socket)
                    self.jogadores[client_socket]["time"] = "A"
                elif old_time == "B":
                    self.team_b.append(client_socket)
                    self.jogadores[client_socket]["time"] = "B"
                return False
        
        return False
    
    def marcar_pronto(self, client_socket):
        """Marca jogador como pronto"""
        if client_socket in self.jogadores:
            self.jogadores[client_socket]["pronto"] = True
            return True
        return False
    
    def todos_prontos(self):
        """Verifica se todos os 4 jogadores estão prontos"""
        if len(self.jogadores) != 4:
            return False
        if len(self.team_a) != 2 or len(self.team_b) != 2:
            return False
        return all(j["pronto"] for j in self.jogadores.values())
    
    def get_estado(self):
        """Retorna estado atual do lobby"""
        jogadores_list = []
        for sock, data in self.jogadores.items():
            jogadores_list.append({
                "nick": data["nick"],
                "time": data["time"],
                "pronto": data["pronto"]
            })
        
        return {
            "sala_id": self.sala_id,
            "jogadores": jogadores_list,
            "team_a_count": len(self.team_a),
            "team_b_count": len(self.team_b),
            "total": len(self.jogadores)
        }
    
    def get_mapeamento_ids(self):
        """Retorna mapeamento de sockets para IDs do jogo"""
        # Time A: IDs 0 e 2
        # Time B: IDs 1 e 3
        mapeamento = {}
        id_a = [0, 2]
        id_b = [1, 3]
        
        for i, sock in enumerate(self.team_a):
            mapeamento[sock] = id_a[i]
        
        for i, sock in enumerate(self.team_b):
            mapeamento[sock] = id_b[i]
        
        return mapeamento

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

    def gerar_sala_id(self):
        """Gera ID único para a sala"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    def broadcast_lobby(self, lobby, sock_mapeamento):
        """Envia estado do lobby para todos os jogadores"""
        estado = lobby.get_estado()
        for sock in lobby.jogadores.keys():
            try:
                sock.sendall(pickle.dumps({"tipo": MsgType.LOBBY_STATE, "estado": estado}))
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
    
    def gerenciar_lobby(self):
        """Gerencia o lobby até todos estarem prontos"""
        sala_id = self.gerar_sala_id()
        lobby = Lobby(sala_id)
        sock_mapeamento = {}  # {socket: client_index}
        
        log(f"🎴 Sala criada: #{sala_id}", "LOBBY")
        log("Aguardando jogadores...", "LOBBY")
        
        # Aceita 4 jogadores no lobby
        while len(lobby.jogadores) < MAX_PLAYERS:
            try:
                c, addr = self.server.accept()
                log(f"   Conexão recebida de {addr}", "INFO")
                
                # Recebe nick
                nick = pickle.loads(c.recv(BUFFER_SIZE))
                lobby.adicionar_jogador(c, nick)
                sock_mapeamento[c] = len(lobby.jogadores) - 1
                
                # Envia confirmação e sala_id
                c.sendall(pickle.dumps({
                    "tipo": "LOBBY_JOINED",
                    "sala_id": sala_id,
                    "msg": f"Bem-vindo ao lobby, {nick}!"
                }))
                
                # Pequeno delay para garantir que o cliente processou a mensagem anterior
                time.sleep(0.1)
                
                # Atualiza todos sobre o estado do lobby
                self.broadcast_lobby(lobby, sock_mapeamento)
                
            except (EOFError, ConnectionResetError, OSError) as e:
                log(f"Erro ao conectar cliente: {e}", "ERROR")
                continue
        
        log("✅ 4 jogadores conectados! Aguardando seleção de times...", "LOBBY")
        
        # Envia estado inicial para todos
        self.broadcast_lobby(lobby, sock_mapeamento)
        
        # Loop do lobby - aguarda escolha de times e prontos
        ultima_atualizacao = time.time()
        while not lobby.todos_prontos():
            # Atualiza estado periodicamente (a cada segundo) mesmo sem mudanças
            tempo_atual = time.time()
            if tempo_atual - ultima_atualizacao > 1.0:
                self.broadcast_lobby(lobby, sock_mapeamento)
                ultima_atualizacao = tempo_atual
            
            # Recebe ações dos jogadores
            for sock in list(lobby.jogadores.keys()):
                try:
                    sock.setblocking(False)
                    try:
                        data = pickle.loads(sock.recv(BUFFER_SIZE))
                        
                        if data["tipo"] == MsgType.LOBBY_JOIN_TEAM:
                            time_escolhido = data["time"]
                            if lobby.mudar_time(sock, time_escolhido):
                                log(f"   {lobby.jogadores[sock]['nick']} entrou no Time {time_escolhido}", "LOBBY")
                                # Atualiza imediatamente após mudança
                                self.broadcast_lobby(lobby, sock_mapeamento)
                            else:
                                sock.sendall(pickle.dumps({
                                    "tipo": "ERROR",
                                    "msg": f"Time {time_escolhido} está cheio!"
                                }))
                        
                        elif data["tipo"] == MsgType.LOBBY_LEAVE_TEAM:
                            if lobby.sair_time(sock):
                                log(f"   {lobby.jogadores[sock]['nick']} saiu do time", "LOBBY")
                                # Atualiza imediatamente após mudança
                                self.broadcast_lobby(lobby, sock_mapeamento)
                            else:
                                sock.sendall(pickle.dumps({
                                    "tipo": "ERROR",
                                    "msg": "Erro ao sair do time!"
                                }))
                        
                        elif data["tipo"] == MsgType.LOBBY_READY:
                            if lobby.jogadores[sock]["time"] is not None:
                                lobby.marcar_pronto(sock)
                                log(f"   {lobby.jogadores[sock]['nick']} está pronto!", "LOBBY")
                                # Atualiza imediatamente após mudança
                                self.broadcast_lobby(lobby, sock_mapeamento)
                            else:
                                sock.sendall(pickle.dumps({
                                    "tipo": "ERROR",
                                    "msg": "Escolha um time primeiro!"
                                }))
                        
                    except BlockingIOError:
                        pass
                    finally:
                        sock.setblocking(True)
                        
                except (EOFError, ConnectionResetError, OSError):
                    pass
            
            time.sleep(LOBBY_UPDATE_INTERVAL)
        
        log("🎮 Todos prontos! Iniciando partida...", "LOBBY")
        
        # Mapeia sockets para IDs de jogo
        id_mapping = lobby.get_mapeamento_ids()
        
        # Cria lista de clients ordenada por ID
        self.clients = [None] * MAX_PLAYERS
        self.nicks = {}
        
        for sock, game_id in id_mapping.items():
            self.clients[game_id] = sock
            self.nicks[game_id] = lobby.jogadores[sock]["nick"]
        
        # Notifica início do jogo
        for sock in lobby.jogadores.keys():
            sock.sendall(pickle.dumps({"tipo": MsgType.LOBBY_START}))
        
        time.sleep(1)
        self.broadcast({"tipo": MsgType.NICKS, "lista": self.nicks})
    
    def start(self):
        """Inicia o servidor e gerencia a partida"""
        # Fase de lobby
        self.gerenciar_lobby()
        
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
