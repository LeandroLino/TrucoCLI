"""
Sistema de estatísticas do jogo
"""
import json
import os
from datetime import datetime
from config import ENABLE_STATS

class GameStats:
    """Gerenciador de estatísticas de jogo"""
    
    def __init__(self, filename="truco_stats.json"):
        self.filename = filename
        self.stats = self._load_stats()
        self.sessao_atual = {
            "inicio": datetime.now().isoformat(),
            "maos_jogadas": 0,
            "vitorias_por_time": {"A": 0, "B": 0},
            "trucos_pedidos": 0,
            "trucos_aceitos": 0,
            "trucos_corridos": 0,
            "cartas_jogadas": {},
            "manilhas_jogadas": 0,
            "cartas_viradas": 0
        }
    
    def _load_stats(self):
        """Carrega estatísticas do arquivo"""
        if not ENABLE_STATS:
            return {}
        
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                return self._criar_stats_vazias()
        return self._criar_stats_vazias()
    
    def _criar_stats_vazias(self):
        """Cria estrutura de stats vazia"""
        return {
            "total_partidas": 0,
            "total_maos": 0,
            "vitorias_time_a": 0,
            "vitorias_time_b": 0,
            "trucos_pedidos": 0,
            "trucos_aceitos": 0,
            "trucos_corridos": 0,
            "cartas_mais_jogadas": {},
            "historico_partidas": []
        }
    
    def salvar(self):
        """Salva estatísticas no arquivo"""
        if not ENABLE_STATS:
            return
        
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar stats: {e}")
    
    def registrar_mao(self, vencedor):
        """Registra uma mão jogada"""
        self.sessao_atual["maos_jogadas"] += 1
        if vencedor != "EMPATE":
            self.sessao_atual["vitorias_por_time"][vencedor] += 1
        self.stats["total_maos"] += 1
    
    def registrar_truco(self, aceito=False, corrido=False):
        """Registra pedido de truco"""
        self.sessao_atual["trucos_pedidos"] += 1
        self.stats["trucos_pedidos"] += 1
        
        if aceito:
            self.sessao_atual["trucos_aceitos"] += 1
            self.stats["trucos_aceitos"] += 1
        elif corrido:
            self.sessao_atual["trucos_corridos"] += 1
            self.stats["trucos_corridos"] += 1
    
    def registrar_carta(self, carta, e_manilha=False, virada=False):
        """Registra carta jogada"""
        carta_str = f"{carta[0]}{carta[1]}"
        
        if carta_str not in self.sessao_atual["cartas_jogadas"]:
            self.sessao_atual["cartas_jogadas"][carta_str] = 0
        self.sessao_atual["cartas_jogadas"][carta_str] += 1
        
        if carta_str not in self.stats["cartas_mais_jogadas"]:
            self.stats["cartas_mais_jogadas"][carta_str] = 0
        self.stats["cartas_mais_jogadas"][carta_str] += 1
        
        if e_manilha:
            self.sessao_atual["manilhas_jogadas"] += 1
        
        if virada:
            self.sessao_atual["cartas_viradas"] += 1
    
    def registrar_partida(self, vencedor):
        """Registra fim de partida"""
        self.stats["total_partidas"] += 1
        
        if vencedor == "A":
            self.stats["vitorias_time_a"] += 1
        elif vencedor == "B":
            self.stats["vitorias_time_b"] += 1
        
        # Adiciona ao histórico
        partida_info = {
            "data": datetime.now().isoformat(),
            "vencedor": vencedor,
            "maos": self.sessao_atual["maos_jogadas"],
            "trucos": self.sessao_atual["trucos_pedidos"]
        }
        
        if "historico_partidas" not in self.stats:
            self.stats["historico_partidas"] = []
        
        self.stats["historico_partidas"].append(partida_info)
        
        # Mantém apenas últimas 50 partidas
        if len(self.stats["historico_partidas"]) > 50:
            self.stats["historico_partidas"] = self.stats["historico_partidas"][-50:]
        
        self.salvar()
    
    def get_stats_formatadas(self):
        """Retorna estatísticas formatadas para exibição"""
        if not ENABLE_STATS:
            return "Estatísticas desabilitadas"
        
        taxa_vitoria_a = 0
        taxa_vitoria_b = 0
        
        if self.stats["total_partidas"] > 0:
            taxa_vitoria_a = (self.stats["vitorias_time_a"] / self.stats["total_partidas"]) * 100
            taxa_vitoria_b = (self.stats["vitorias_time_b"] / self.stats["total_partidas"]) * 100
        
        taxa_truco_aceito = 0
        if self.stats["trucos_pedidos"] > 0:
            taxa_truco_aceito = (self.stats["trucos_aceitos"] / self.stats["trucos_pedidos"]) * 100
        
        # Top 5 cartas mais jogadas
        top_cartas = sorted(
            self.stats["cartas_mais_jogadas"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return f"""
╔══════════════════════════════════════════════════════════╗
║                  📊 ESTATÍSTICAS GERAIS                  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  PARTIDAS:                                               ║
║    Total jogadas: {self.stats['total_partidas']:<42} ║
║    Vitórias Time A: {self.stats['vitorias_time_a']:<38} ║
║    Vitórias Time B: {self.stats['vitorias_time_b']:<38} ║
║    Taxa Time A: {taxa_vitoria_a:>5.1f}%                              ║
║    Taxa Time B: {taxa_vitoria_b:>5.1f}%                              ║
║                                                          ║
║  TRUCOS:                                                 ║
║    Pedidos: {self.stats['trucos_pedidos']:<45} ║
║    Aceitos: {self.stats['trucos_aceitos']:<45} ║
║    Corridos: {self.stats['trucos_corridos']:<44} ║
║    Taxa de aceitação: {taxa_truco_aceito:>5.1f}%                     ║
║                                                          ║
║  CARTAS MAIS JOGADAS:                                    ║
{"".join([f"║    {i+1}. {carta:<51} ({qtd}x) ║\n" for i, (carta, qtd) in enumerate(top_cartas)])}║                                                          ║
║  TOTAL DE MÃOS: {self.stats['total_maos']:<42} ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    
    def get_stats_sessao(self):
        """Retorna estatísticas da sessão atual"""
        return f"""
╔══════════════════════════════════════════════════════════╗
║                  📊 ESTATÍSTICAS DA SESSÃO               ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Mãos jogadas: {self.sessao_atual['maos_jogadas']:<43} ║
║  Vitórias Time A: {self.sessao_atual['vitorias_por_time']['A']:<40} ║
║  Vitórias Time B: {self.sessao_atual['vitorias_por_time']['B']:<40} ║
║  Trucos pedidos: {self.sessao_atual['trucos_pedidos']:<41} ║
║  Trucos aceitos: {self.sessao_atual['trucos_aceitos']:<41} ║
║  Manilhas jogadas: {self.sessao_atual['manilhas_jogadas']:<39} ║
║  Cartas viradas: {self.sessao_atual['cartas_viradas']:<41} ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
