import socket, pickle, random, time
from datetime import datetime

def log(mensagem, nivel="INFO"):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{nivel}] {mensagem}")

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
        self.time_ultimo_aumento = None

    def broadcast(self, data):
        for c in self.clients:
            try: c.sendall(pickle.dumps(data))
            except: pass
        time.sleep(0.1)

    def gerenciar_truco(self, quem_pediu):
        time_pediu = "A" if quem_pediu % 2 == 0 else "B"
        if self.time_ultimo_aumento == time_pediu: return "BLOQUEADO"
        
        proximo = {1:3, 3:6, 6:9, 9:12}.get(self.valor_mao, 12)
        self.broadcast({"tipo": "UPDATE", "msg": f"🔥 TIME {time_pediu} PEDIU {proximo}!"})
        
        adv = [1, 3] if time_pediu == "A" else [0, 2]
        self.clients[adv[0]].sendall(pickle.dumps({"tipo": "ASK_TRUCO", "msg": f"Aceita {proximo}? (S)im / (N)ão / (A)umentar"}))
        resp = pickle.loads(self.clients[adv[0]].recv(4096)).upper()
        
        if resp == "S":
            self.valor_mao, self.time_ultimo_aumento = proximo, time_pediu
            return "ACEITO"
        elif resp == "A" and proximo < 12:
            self.valor_mao, self.time_ultimo_aumento = proximo, time_pediu
            return self.gerenciar_truco(adv[0])
        return "CORREU"

    def processar_mao(self):
        self.valor_mao, self.time_ultimo_aumento = 1, None
        cartas = [(v, n) for v in ORDEM for n in NAIPES]
        random.shuffle(cartas)
        vira = cartas.pop()
        manilha = ORDEM[(ORDEM.index(vira[0]) + 1) % len(ORDEM)]
        maos = [[cartas.pop() for _ in range(3)] for _ in range(4)]

        # Lógica de Mão de Onze
        for t in ["A", "B"]:
            if self.pontos_geral[t] == 11:
                log(f"Mão de Onze para Time {t}", "GAME")
                idx = [0, 2] if t == "A" else [1, 3]
                # Mostra carta do parceiro
                self.clients[idx[0]].sendall(pickle.dumps({"tipo": "ONZE", "parceiro": maos[idx[1]]}))
                self.clients[idx[1]].sendall(pickle.dumps({"tipo": "ONZE", "parceiro": maos[idx[0]]}))

        for i in range(4):
            self.clients[i].sendall(pickle.dumps({"tipo": "START", "mao": maos[i], "vira": vira, "id": i, "time": "A" if i%2==0 else "B"}))
        
        vitorias_queda = [] # Armazena "A", "B" ou "EMPATE"
        primeiro_a_jogar = 0

        for queda in range(1, 4):
            mesa = []
            for i in range(4):
                idx = (primeiro_a_jogar + i) % 4
                self.broadcast({"tipo": "TURN", "player": idx, "n_queda": queda, "valor": self.valor_mao})
                resp = pickle.loads(self.clients[idx].recv(4096))
                
                while resp == "TRUCO":
                    res = self.gerenciar_truco(idx)
                    if res == "CORREU": return ("A" if idx%2==0 else "B"), True
                    self.clients[idx].sendall(pickle.dumps({"tipo": "TURN", "player": idx, "n_queda": queda, "valor": self.valor_mao}))
                    resp = pickle.loads(self.clients[idx].recv(4096))

                forca = (100 + NAIPES[resp[1]]) if resp[0] == manilha else ORDEM.index(resp[0])
                mesa.append({"id": idx, "forca": forca, "carta": resp})
                self.broadcast({"tipo": "UPDATE", "msg": f"J{idx} jogou {resp[0]} de {resp[1]}"})

            # Cálculo de Vencedor da Queda com Empate
            maior_forca = max(m["forca"] for m in mesa)
            vencedores = [m for m in mesa if m["forca"] == maior_forca]
            
            if len(vencedores) > 1 and vencedores[0]["id"] % 2 != vencedores[1]["id"] % 2:
                venc_queda = "EMPATE"
                self.broadcast({"tipo": "UPDATE", "msg": "🏳️ A queda EMPATOU!"})
            else:
                primeiro_a_jogar = vencedores[0]["id"]
                venc_queda = "A" if primeiro_a_jogar % 2 == 0 else "B"
            
            vitorias_queda.append(venc_queda)
            self.broadcast({"tipo": "RESULT", "msg": f"Resultado: {venc_queda}"})

            # Regras de Empate (Canga)
            if "A" in vitorias_queda and "B" in vitorias_queda:
                if vitorias_queda.count("A") == 2: return "A", False
                if vitorias_queda.count("B") == 2: return "B", False
            elif vitorias_queda[0] == "EMPATE" and len(vitorias_queda) > 1:
                if vitorias_queda[-1] != "EMPATE": return vitorias_queda[-1], False
            elif "A" in vitorias_queda or "B" in vitorias_queda:
                time_ganhou_primeira = next(v for v in vitorias_queda if v != "EMPATE")
                if vitorias_queda[-1] == "EMPATE": return time_ganhou_primeira, False
                if vitorias_queda.count(time_ganhou_primeira) == 2: return time_ganhou_primeira, False
            
            time.sleep(1)
        return "EMPATE", False

    def start(self):
        log("Servidor pronto.", "INFO")
        while len(self.clients) < 4:
            conn, _ = self.server.accept()
            self.clients.append(conn)
        
        while max(self.pontos_geral.values()) < 12:
            venc, correu = self.processar_mao()
            if venc != "EMPATE":
                pts = self.valor_mao if not correu else 1
                self.pontos_geral[venc] += pts
                self.broadcast({"tipo": "SCORE", "placar": self.pontos_geral})

if __name__ == "__main__":
    TrucoServer().start()