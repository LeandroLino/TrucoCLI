import socket, pickle, random, time
from datetime import datetime

# Configuração de Cores para o Log do Servidor
G, Y, B, R, N = "\033[32m", "\033[33m", "\033[34m", "\033[31m", "\033[0m"

def log(mensagem, nivel="INFO"):
    cores = {"INFO": B, "GAME": G, "WAIT": Y, "ERROR": R}
    print(f"{cores.get(nivel, N)}[{datetime.now().strftime('%H:%M:%S')}] [{nivel}] {mensagem}{N}")

ORDEM = ["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"]
NAIPES = {"Ouros": 1, "Espadas": 2, "Copas": 3, "Paus": 4}

class TrucoServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', 5555))
        self.server.listen(4)
        self.clients = []
        self.pontos_geral = {"A": 0, "B": 0}
        self.valor_mao = 1 

    def broadcast(self, data):
        for c in self.clients:
            try:
                c.sendall(pickle.dumps(data))
            except: pass
        time.sleep(0.1)

    def gerenciar_truco(self, quem_pediu):
        """Interrompe o jogo para validar o pedido de Truco."""
        time_pediu = "A" if quem_pediu % 2 == 0 else "B"
        time_adv = "B" if time_pediu == "A" else "A"
        adv_indices = [1, 3] if time_pediu == "A" else [0, 2]
        
        log(f"Jogador {quem_pediu} (Time {time_pediu}) TRUCOU!", "GAME")
        self.broadcast({"tipo": "UPDATE", "msg": f"🔥 TIME {time_pediu} GRITOU TRUCO!"})
        
        # Pergunta ao primeiro jogador disponível do time adversário
        alvo = adv_indices[0]
        try:
            self.clients[alvo].sendall(pickle.dumps({
                "tipo": "ASK_TRUCO", 
                "msg": f"O Time {time_pediu} trucou! Aceita? (S)im / (N)ão / (A)umentar"
            }))
            
            resp = pickle.loads(self.clients[alvo].recv(4096)).upper()
            
            if resp == "S":
                self.valor_mao = 3
                log("Truco aceito. A mão agora vale 3 pontos.", "GAME")
                self.broadcast({"tipo": "UPDATE", "msg": "TRUCO ACEITO! Agora vale 3 tentos."})
                return True # Continua a rodada
            else:
                log(f"Time {time_adv} correu. Time {time_pediu} ganha a mão.", "GAME")
                self.broadcast({"tipo": "UPDATE", "msg": f"Time {time_adv} correu! Time {time_pediu} fatura os pontos."})
                return False # Encerra a mão imediatamente
        except:
            return False

    def processar_mao(self):
        self.valor_mao = 1
        cartas = [(v, n) for v in ORDEM for n in NAIPES]
        random.shuffle(cartas)
        vira = cartas.pop()
        manilha = ORDEM[(ORDEM.index(vira[0]) + 1) % len(ORDEM)]
        maos = [[cartas.pop() for _ in range(3)] for _ in range(4)]

        log(f"Nova Mão | Vira: {vira} | Manilha: {manilha}", "GAME")

        for i in range(4):
            self.clients[i].sendall(pickle.dumps({
                "tipo": "START", "mao": maos[i], "vira": vira, "id": i, "time": "A" if i % 2 == 0 else "B"
            }))
        
        vitorias_queda = []
        primeiro_a_jogar = 0 
        correu = False

        for queda in range(1, 4):
            mesa = []
            for i in range(4):
                idx_jogador = (primeiro_a_jogar + i) % 4
                self.broadcast({"tipo": "TURN", "player": idx_jogador, "n_queda": queda})
                
                try:
                    resp = pickle.loads(self.clients[idx_jogador].recv(4096))
                    
                    if resp == "TRUCO":
                        aceitou = self.gerenciar_truco(idx_jogador)
                        if not aceitou:
                            # Se correu, retorna quem ganhou e sinaliza que houve desistência
                            vencedor_por_corrida = "A" if idx_jogador % 2 == 0 else "B"
                            return vencedor_por_corrida, True
                        
                        # Se aceitou, pede a carta novamente para o mesmo jogador
                        self.clients[idx_jogador].sendall(pickle.dumps({"tipo": "TURN", "player": idx_jogador, "n_queda": queda}))
                        resp = pickle.loads(self.clients[idx_jogador].recv(4096))

                    forca = (100 + NAIPES[resp[1]]) if resp[0] == manilha else ORDEM.index(resp[0])
                    mesa.append({"id": idx_jogador, "forca": forca, "carta": resp})
                    self.broadcast({"tipo": "UPDATE", "msg": f"J{idx_jogador} jogou {resp[0]} de {resp[1]}"})
                except: return "ERRO", False

            venc_q = max(mesa, key=lambda x: x["forca"])
            primeiro_a_jogar = venc_q["id"]
            vitorias_queda.append("A" if primeiro_a_jogar % 2 == 0 else "B")
            self.broadcast({"tipo": "RESULT", "msg": f"Time {vitorias_queda[-1]} venceu a queda {queda}!"})
            
            if vitorias_queda.count("A") == 2: return "A", False
            if vitorias_queda.count("B") == 2: return "B", False
            time.sleep(1)

    def start(self):
        log("Aguardando 4 jogadores...", "INFO")
        while len(self.clients) < 4:
            conn, _ = self.server.accept()
            self.clients.append(conn)
        
        while max(self.pontos_geral.values()) < 12:
            venc, foi_corrida = self.processar_mao()
            if venc == "ERRO": break
            
            # Se alguém correu do truco, ganha 1 ponto (ou o valor anterior ao aumento)
            pontos_ganhos = self.valor_mao if not foi_corrida else (1 if self.valor_mao == 1 else 1)
            self.pontos_geral[venc] += pontos_ganhos
            
            log(f"Fim da mão. Time {venc} ganhou {pontos_ganhos} pontos.", "GAME")
            self.broadcast({"tipo": "SCORE", "placar": self.pontos_geral})

if __name__ == "__main__":
    TrucoServer().start()