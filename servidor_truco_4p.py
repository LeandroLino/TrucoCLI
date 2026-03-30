import socket, pickle, random, time
from datetime import datetime

def log(msg, nivel="INFO"):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{nivel}] {msg}")

ORDEM = ["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"]
NAIPES = {"Ouros": 1, "Espadas": 2, "Copas": 3, "Paus": 4}
NAIPE_SIMBOLOS = {"Ouros": "♦", "Espadas": "♠", "Copas": "♥", "Paus": "♣"}

class TrucoServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', 5555))
        self.server.listen(4)
        self.clients, self.nicks = [], {}
        self.pontos_geral = {"A": 0, "B": 0}
        self.valor_mao = 1
        self.time_ultimo_aumento = None

    def broadcast(self, data):
        """Envia dados para todos os clientes conectados"""
        for idx, c in enumerate(self.clients):
            try:
                c.sendall(pickle.dumps(data))
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                log(f"Erro ao enviar broadcast para {self.nicks.get(idx, 'Unknown')}: {e}", "ERROR")
        time.sleep(0.05)

    def gerenciar_truco(self, quem_pediu):
        """Gerencia pedido de truco/aumento de aposta"""
        time_p = "A" if quem_pediu % 2 == 0 else "B"
        if self.time_ultimo_aumento == time_p:
            try:
                self.clients[quem_pediu].sendall(pickle.dumps({"tipo": "UPDATE", "msg": "❌ Seu time já aumentou!"}))
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                log(f"Erro ao enviar bloqueio de truco para {self.nicks[quem_pediu]}: {e}", "ERROR")
            return "BLOQUEADO"
        
        prox = {1: 3, 3: 6, 6: 9, 9: 12}.get(self.valor_mao, 12)
        self.broadcast({"tipo": "UPDATE", "msg": f"🔥 {self.nicks[quem_pediu]} PEDIU {prox}!"})
        
        adv = [1, 3] if time_p == "A" else [0, 2]
        try:
            self.clients[adv[0]].sendall(pickle.dumps({"tipo": "ASK_TRUCO", "msg": f"Aceita {prox}? (S)im/(N)ão/(A)umentar"}))
            resp = pickle.loads(self.clients[adv[0]].recv(4096)).upper()
        except (EOFError, ConnectionResetError, BrokenPipeError, OSError) as e:
            log(f"Erro ao receber resposta de truco de {self.nicks[adv[0]]}: {e}", "ERROR")
            return "CORREU"
        
        if resp == "S":
            self.valor_mao, self.time_ultimo_aumento = prox, time_p
            return "ACEITO"
        elif resp == "A" and prox < 12:
            self.valor_mao, self.time_ultimo_aumento = prox, time_p
            return self.gerenciar_truco(adv[0])
        return "CORREU"

    def processar_mao(self, pe_idx=0):
        log(f"🎴 Nova mão iniciada | Placar: A={self.pontos_geral['A']} B={self.pontos_geral['B']}", "GAME")
        self.valor_mao, self.time_ultimo_aumento = 1, None
        mao_ferro = (self.pontos_geral["A"] == 11 and self.pontos_geral["B"] == 11)
        
        cartas = [(v, n) for v in ORDEM for n in NAIPES]
        random.shuffle(cartas)
        vira = cartas.pop()
        manilha = ORDEM[(ORDEM.index(vira[0]) + 1) % 10]
        maos = [[cartas.pop() for _ in range(3)] for _ in range(4)]
        
        # Define posições: Mão (primeiro), Contra-Pé (segundo), Par Mão (terceiro), Pé (quarto/último)
        # Esta definição será usada para atualizar posições durante as quedas
        self.posicoes_nome = ["Mão", "Contra-Pé", "Par Mão", "Pé"]
        ordem_jogadores = [(pe_idx + i) % 4 for i in range(4)]
        pos_map = {ordem_jogadores[i]: self.posicoes_nome[i] for i in range(4)}
        
        log(f"   Vira: {vira[0]} de {vira[1]} | Manilha: {manilha}", "GAME")
        log(f"   Posições: {' | '.join([f'{self.nicks[i]} ({pos_map[i]})' for i in range(4)])}", "GAME")

        # Mão de Onze
        if not mao_ferro:
            for t in ["A", "B"]:
                if self.pontos_geral[t] == 11:
                    log(f"   ⚠️  Mão de 11 para TIME {t}!", "GAME")
                    idx = [0, 2] if t == "A" else [1, 3]
                    for j, p in [(idx[0], idx[1]), (idx[1], idx[0])]:
                        try:
                            self.clients[j].sendall(pickle.dumps({"tipo": "ONZE", "parceiro": maos[p], "nick_p": self.nicks[p]}))
                        except (BrokenPipeError, ConnectionResetError, OSError) as e:
                            log(f"Erro ao enviar ONZE para {self.nicks[j]}: {e}", "ERROR")

        for i in range(4):
            try:
                self.clients[i].sendall(pickle.dumps({
                    "tipo": "START", 
                    "mao": maos[i], 
                    "vira": vira, 
                    "id": i, 
                    "time": "A" if i % 2 == 0 else "B", 
                    "ferro": mao_ferro,
                    "posicao": pos_map[i]
                }))
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                log(f"Erro ao enviar START para {self.nicks[i]}: {e}", "ERROR")
        
        vitorias_queda, primeiro = [], pe_idx
        for queda in range(1, 4):
            log(f"   >>> Queda {queda} | Valor: {self.valor_mao} | Inicia: {self.nicks[primeiro]}", "GAME")
            # Limpa os logs da rodada no início de cada nova queda
            if queda > 1:  # Só limpa após a primeira queda
                log(f"      → Enviando CLEAR_LOGS via broadcast", "DEBUG")
                self.broadcast({"tipo": "CLEAR_LOGS"})
                log(f"      → CLEAR_LOGS enviado", "DEBUG")
                time.sleep(0.3)  # Delay para garantir que todos processem
                log(f"      → Aguardou 0.3s após CLEAR_LOGS", "DEBUG")
            mesa = []
            for i in range(4):
                idx = (primeiro + i) % 4
                log(f"      → Enviando TURN para {self.nicks[idx]} (ID {idx})", "DEBUG")
                
                # Envia TURN apenas para o jogador específico
                try:
                    self.clients[idx].sendall(pickle.dumps({"tipo": "TURN", "player": idx, "n_queda": queda, "valor": self.valor_mao}))
                    log(f"      → TURN enviado para {self.nicks[idx]}", "DEBUG")
                except (BrokenPipeError, ConnectionResetError, OSError) as e:
                    log(f"Erro ao enviar TURN para {self.nicks[idx]}: {e}", "ERROR")
                    return ("B" if idx % 2 == 0 else "A"), True
                
                # Notifica outros jogadores que é a vez desse jogador
                for j in range(4):
                    if j != idx:
                        try:
                            self.clients[j].sendall(pickle.dumps({"tipo": "WAIT_TURN", "player": idx}))
                        except (BrokenPipeError, ConnectionResetError, OSError) as e:
                            log(f"Erro ao enviar WAIT_TURN para {self.nicks[j]}: {e}", "ERROR")
                log(f"      → WAIT_TURN enviado para outros 3 jogadores", "DEBUG")
                
                log(f"      → Aguardando resposta de {self.nicks[idx]}...", "DEBUG")
                try:
                    resp_data = pickle.loads(self.clients[idx].recv(4096))
                    log(f"      → RECEBEU resposta de {self.nicks[idx]}: {type(resp_data)}", "DEBUG")
                    if resp_data == "TRUCO":
                        res = self.gerenciar_truco(idx)
                        if res == "CORREU":
                            return ("A" if idx % 2 == 0 else "B"), True
                        try:
                            self.clients[idx].sendall(pickle.dumps({"tipo": "TURN", "player": idx, "n_queda": queda, "valor": self.valor_mao}))
                            resp_data = pickle.loads(self.clients[idx].recv(4096))
                        except (EOFError, ConnectionResetError, BrokenPipeError, OSError) as e:
                            log(f"Erro ao receber carta após truco de {self.nicks[idx]}: {e}", "ERROR")
                            return ("B" if idx % 2 == 0 else "A"), True

                    carta, virada = resp_data
                    time_jogador = "A" if idx % 2 == 0 else "B"
                    emoji_time = "🔵" if time_jogador == "A" else "🔴"
                    
                    if virada:
                        forca, msg = -1, f"{emoji_time} {self.nicks[idx]} (Time {time_jogador}) jogou CARTA VIRADA"
                        carta_display = "VIRADA"
                    else:
                        forca = (100 + NAIPES[carta[1]]) if carta[0] == manilha else ORDEM.index(carta[0])
                        naipe_simbolo = NAIPE_SIMBOLOS.get(carta[1], carta[1])
                        carta_display = f"{carta[0]}{naipe_simbolo}"
                        msg = f"{emoji_time} {self.nicks[idx]} (Time {time_jogador}) jogou {carta_display}"
                    
                    mesa.append({"id": idx, "forca": forca, "carta": carta_display, "nick": self.nicks[idx], "time": time_jogador})
                    self.broadcast({"tipo": "UPDATE", "msg": msg, "jogador_id": idx, "forca": forca})
                except (EOFError, ConnectionResetError, BrokenPipeError, OSError) as e:
                    log(f"❌ Cliente {self.nicks[idx]} desconectou: {e}", "ERROR")
                    return ("B" if idx % 2 == 0 else "A"), True  # Time adversário ganha por W.O.

            maior = max(m["forca"] for m in mesa)
            vencs = [m for m in mesa if m["forca"] == maior]
            venc_q = "EMPATE" if (len(vencs) > 1 and vencs[0]["id"]%2 != vencs[1]["id"]%2) else ("A" if vencs[0]["id"]%2==0 else "B")
            
            # Aguarda visualizar a carta vencedora antes de processar resultado
            time.sleep(2)
            
            vitorias_queda.append(venc_q)
            if venc_q != "EMPATE":
                vencedores = [m["id"] for m in mesa if m["forca"] == maior]
                primeiro = vencedores[0] if vencedores else primeiro
                vencedor_nome = self.nicks[primeiro]
            else:
                vencedor_nome = "EMPATE"
            
            # Atualiza posições ANTES de enviar RESULT (para evitar race condition)
            if queda < 3 and venc_q != "EMPATE":
                log(f"      → Enviando UPDATE_POS para todos os jogadores", "DEBUG")
                pos_map = {(primeiro + i) % 4: self.posicoes_nome[i] for i in range(4)}
                for i in range(4):
                    try:
                        self.clients[i].sendall(pickle.dumps({"tipo": "UPDATE_POS", "posicao": pos_map[i]}))
                        log(f"         UPDATE_POS enviado para {self.nicks[i]}: {pos_map[i]}", "DEBUG")
                    except (BrokenPipeError, ConnectionResetError, OSError) as e:
                        log(f"Erro ao enviar UPDATE_POS para {self.nicks[i]}: {e}", "ERROR")
            
            log(f"   Resultado Queda {queda}: {venc_q} ({vencedor_nome}) | Próximo: {self.nicks[primeiro]}", "GAME")
            log(f"      → Enviando RESULT via broadcast", "DEBUG")
            self.broadcast({"tipo": "RESULT", "msg": f"Vencedor: {vencedor_nome} (Time {venc_q}) - {self.nicks[primeiro]} abre próxima"})
            
            # Aguarda clientes processarem RESULT antes de continuar
            time.sleep(2.5)

            # Lógica Canga
            if vitorias_queda.count("A") == 2:
                log(f"✅ TIME A venceu a mão! (+{self.valor_mao} pontos)", "GAME")
                return "A", False
            if vitorias_queda.count("B") == 2:
                log(f"✅ TIME B venceu a mão! (+{self.valor_mao} pontos)", "GAME")
                return "B", False
            if len(vitorias_queda) >= 2:
                if vitorias_queda[0] == "EMPATE" and vitorias_queda[-1] != "EMPATE":
                    log(f"✅ TIME {vitorias_queda[-1]} venceu (1º empate, 2º {vitorias_queda[-1]})", "GAME")
                    return vitorias_queda[-1], False
                if vitorias_queda[-1] == "EMPATE" and vitorias_queda[0] != "EMPATE":
                    log(f"✅ TIME {vitorias_queda[0]} venceu (1º {vitorias_queda[0]}, 2º empate)", "GAME")
                    return vitorias_queda[0], False
        log(f"⚖️  Mão empatou!", "GAME")
        return "EMPATE", False

    def start(self):
        """Inicia o servidor e gerencia a partida"""
        log("Servidor Online. Aguardando 4 nicks...", "WAIT")
        while len(self.clients) < 4:
            try:
                c, addr = self.server.accept()
                log(f"   Conexão recebida de {addr}", "INFO")
                nick = pickle.loads(c.recv(4096))
                self.nicks[len(self.clients)] = nick
                self.clients.append(c)
                log(f"   Jogador {len(self.clients)}/4 conectado: {nick}", "WAIT")
            except (EOFError, ConnectionResetError, OSError) as e:
                log(f"Erro ao conectar cliente: {e}", "ERROR")
                continue
        
        log("🎮 Todos conectados! Iniciando partida...", "INFO")
        self.broadcast({"tipo": "NICKS", "lista": self.nicks})
        
        pe_atual = 0
        while max(self.pontos_geral.values()) < 12:
            v, c = self.processar_mao(pe_atual)
            if v != "EMPATE":
                pts = self.valor_mao if not c else 1
                self.pontos_geral[v] += pts
                log(f"📊 Placar atualizado: A={self.pontos_geral['A']} B={self.pontos_geral['B']}", "INFO")
            self.broadcast({"tipo": "SCORE", "placar": self.pontos_geral})
            time.sleep(2)  # Pequeno delay antes de iniciar próxima mão
            pe_atual = (pe_atual + 1) % 4  # Roda o pé
            log("⏳ Aguardando próxima mão...", "WAIT")
        
        log(f"🏆 FIM DE JOGO! Vencedor: TIME {'A' if self.pontos_geral['A'] >= 12 else 'B'}", "INFO")

if __name__ == "__main__": TrucoServer().start()