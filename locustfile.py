"""
Pratica 2 - Teste de carga, estresse e elasticidade com Locust.

Como usar:
    pip install locust
    locust -f locustfile.py

Depois abra http://localhost:8089 (ou a porta 8089 encaminhada no Codespaces) e:
  Fase 1 (baseline local): 50 usuarios | spawn rate 5  | Host http://localhost:5000  | 3 min
  Fase 2 (estresse nuvem): 200 usuarios | spawn rate 10 | Host https://SUA-API.onrender.com | 5 min

Proporcao de tarefas 1:3 -> ~25% de requisicoes leves (GET /) e ~75% pesadas (POST /predict),
simulando um trafego realista onde a sonda de disponibilidade convive com o processamento.
"""

import json

from locust import HttpUser, between, task


class APIStressTestUser(HttpUser):
    # Tempo de espera aleatorio (1 a 3 s) entre requisicoes de cada usuario virtual
    wait_time = between(1, 3)

    @task(1)
    def test_healthcheck(self):
        """Acesso leve a raiz da API (sonda de disponibilidade)."""
        self.client.get("/", name="GET /")

    @task(3)
    def test_predict_endpoint(self):
        """Requisicoes simultaneas de processamento no endpoint /predict."""
        headers = {"Content-Type": "application/json"}

        # ===================================================
        # SELECAO DE PAYLOAD DA SUA TRILHA (ative apenas uma)
        # ===================================================

        # --- TRILHA INTEGRADA (Agente de IA / RAG) ---
        payload_ia = {
            "prompt": "Explique o Teorema CAP de Eric Brewer e o modelo BASE de forma simples."
        }

        # --- TRILHA PADRAO (API utilitaria / Calculadora) ---
        payload_padrao = {"num1": 150, "num2": 35, "operacao": "multiplicacao"}

        payload = payload_padrao  # troque para payload_ia se for da Trilha Integrada

        self.client.post(
            "/predict",
            data=json.dumps(payload),
            headers=headers,
            name="POST /predict",
        )
