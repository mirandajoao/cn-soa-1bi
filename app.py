"""
API da 1a Avaliacao Bimestral - Computacao em Nuvem e SOA (IFPA Ananindeua)
Equipe: Joao Vitor, Ederson e Ilard

A API expoe duas rotas:
  GET  /         -> healthcheck leve (sonda de disponibilidade usada pelo Locust)
  POST /predict  -> rota de processamento, blindada contra payload malformado

Modo de operacao controlado pela variavel de ambiente RAG_ENABLED:
  RAG_ENABLED=false (padrao) -> Trilha Padrao: API utilitaria (calculadora)
  RAG_ENABLED=true           -> Trilha Integrada: responde via Agente de IA com RAG
"""

import os
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

RAG_ENABLED = os.getenv("RAG_ENABLED", "false").strip().lower() in ("1", "true", "yes", "sim")
TRILHA = "INTEGRADA (Agente de IA + RAG)" if RAG_ENABLED else "PADRAO (API utilitaria)"

# Cache do agente: carregado sob demanda (lazy loading) para nao travar o boot
# do container na nuvem e nao estourar o timeout de health check do PaaS.
_agente_cache = None


def _get_agente():
    global _agente_cache
    if _agente_cache is None:
        from rag_agent import build_agent  # import tardio: so acontece se RAG estiver ligado
        _agente_cache = build_agent()
    return _agente_cache


# ---------------------------------------------------------------------------
# Trilha Padrao: logica utilitaria (calculadora)
# ---------------------------------------------------------------------------
OPERACOES = {
    "soma": lambda a, b: a + b,
    "subtracao": lambda a, b: a - b,
    "multiplicacao": lambda a, b: a * b,
    "divisao": lambda a, b: a / b,
}


def _calcular(data):
    """Executa a operacao utilitaria. Levanta ValueError em entrada invalida."""
    operacao = str(data.get("operacao", "soma")).strip().lower()

    if operacao not in OPERACOES:
        raise ValueError(
            "Operacao invalida. Use uma destas: " + ", ".join(sorted(OPERACOES))
        )

    try:
        num1 = float(data.get("num1"))
        num2 = float(data.get("num2"))
    except (TypeError, ValueError):
        raise ValueError("Os campos 'num1' e 'num2' devem ser numericos.")

    if operacao == "divisao" and num2 == 0:
        raise ValueError("Divisao por zero nao e permitida.")

    return {"num1": num1, "num2": num2, "operacao": operacao, "resultado": OPERACOES[operacao](num1, num2)}


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def healthcheck():
    """Sonda de disponibilidade - intencionalmente leve (O(1), sem I/O)."""
    return jsonify(
        {
            "status": "ok",
            "servico": "API 1a BI - Computacao em Nuvem e SOA",
            "equipe": ["Joao Vitor", "Ederson", "Ilard"],
            "trilha": TRILHA,
            "rag_enabled": RAG_ENABLED,
            "rotas": {"healthcheck": "GET /", "processamento": "POST /predict"},
        }
    ), 200


@app.route("/predict", methods=["POST"])
def predict():
    """
    Rota de processamento blindada.

    REGRA DE ENGENHARIA CRITICA (roteiro da Pratica 2):
    usa request.get_json(silent=True) + try/except para que um JSON malformado
    enviado pelo Locust NUNCA derrube o worker com HTTP 500 nao tratado.
    Assim o teste de carga mede a infraestrutura (CPU/RAM/sockets), e nao bug de codigo.
    """
    inicio = time.perf_counter()

    try:
        data = request.get_json(silent=True) or {}

        if not isinstance(data, dict):
            return jsonify({"erro": "Bad Request", "mensagem": "O corpo deve ser um objeto JSON."}), 400

        prompt = data.get("prompt")

        # --- Trilha Integrada: pergunta em linguagem natural para o agente RAG ---
        if prompt is not None:
            prompt = str(prompt).strip()
            if not prompt:
                return jsonify({"erro": "Bad Request", "mensagem": "Prompt ausente ou vazio."}), 400

            if RAG_ENABLED:
                resposta = _get_agente()(prompt)
                modo = "rag"
            else:
                # Fallback deterministico: mantem a rota saudavel sob carga mesmo
                # com o agente desligado (nao inventa resposta institucional).
                resposta = (
                    "Agente de IA desativado nesta instancia (RAG_ENABLED=false). "
                    "Prompt recebido e validado com sucesso."
                )
                modo = "fallback_sem_rag"

            return jsonify(
                {
                    "sucesso": True,
                    "trilha": TRILHA,
                    "modo": modo,
                    "prompt": prompt[:200],
                    "resposta": resposta,
                    "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2),
                }
            ), 200

        # --- Trilha Padrao: operacao utilitaria ---
        if "num1" in data or "num2" in data:
            resultado = _calcular(data)
            return jsonify(
                {
                    "sucesso": True,
                    "trilha": TRILHA,
                    "modo": "utilitario",
                    "dados": resultado,
                    "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2),
                }
            ), 200

        return jsonify(
            {
                "erro": "Bad Request",
                "mensagem": "Envie 'prompt' (trilha integrada) ou 'num1'/'num2'/'operacao' (trilha padrao).",
            }
        ), 400

    except ValueError as e:
        # Erro de dominio previsto -> 400, sem derrubar o processo
        return jsonify({"erro": "Bad Request", "mensagem": str(e)}), 400

    except Exception as e:
        # Rede de seguranca final: devolve JSON em vez de estourar o worker
        return jsonify({"status": "error", "message": str(e)}), 500


@app.errorhandler(404)
def nao_encontrado(_):
    return jsonify({"erro": "Not Found", "mensagem": "Rota inexistente."}), 404


@app.errorhandler(405)
def metodo_invalido(_):
    return jsonify({"erro": "Method Not Allowed", "mensagem": "Verifique o metodo HTTP da rota."}), 405


if __name__ == "__main__":
    porta = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=porta, debug=False)
