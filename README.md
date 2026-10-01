# API — 1ª Avaliação Bimestral | Computação em Nuvem e SOA

IFPA Campus Ananindeua — Bacharelado em Ciência da Computação (7º período)
Professor: Fábio Ferreira | 2026.2

**Equipe:** João Vitor de Almeida Miranda · Ederson · Ilard

## Sobre

API Flask conteinerizada (Alpine Linux) publicada em PaaS, usada como alvo dos
testes de carga da Prática 2 (Locust).

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Healthcheck / sonda de disponibilidade |
| `/predict` | POST | Processamento (calculadora ou agente RAG) |

## Rodando localmente

```bash
docker build -t api-cn-soa .
docker run -p 5000:5000 api-cn-soa
```

```bash
curl http://localhost:5000/
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"num1":150,"num2":35,"operacao":"multiplicacao"}'
```

## Teste de carga

```bash
pip install locust
locust -f locustfile.py
# http://localhost:8089
```

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `5000` | Injetada pelo PaaS |
| `RAG_ENABLED` | `false` | `true` ativa o agente de IA com RAG (Trilha Integrada) |
| `GEMINI_API_KEY` | — | Obrigatória apenas se `RAG_ENABLED=true` |

## Deploy

Render (Docker, plano Free) — deploy contínuo a partir do branch `main`.
URL pública: `https://SEU-SERVICO.onrender.com`
