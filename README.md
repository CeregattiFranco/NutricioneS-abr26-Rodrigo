# 🥗 NutricioneS Sabla (NSS) - A Clínica Autônoma (Clínica Sem Stress)

Bem-vindo ao **NutricioneS Sabla (NSS)**, a espinha dorsal de inteligência do ecossistema NutricioneS. O NSS evoluiu de um robusto motor de dietas para uma **Infraestrutura de Bio-Inteligência e Automação Clínica** completa, operando sob os princípios **Twelve-Factor App** e orquestrada via **Docker**.

---

## 🚀 Os 5 Pilares da "Clínica Sem Stress"

O NSS atua como um "encanamento invisível" que orquestra a jornada do paciente através de módulos especializados:

### 🎙️ 1. NSS Listen (Escuta Ativa)

- **Transcrição Fathom AI**: Ingestão automática de áudio de consultas via Webhooks seguros (HMAC). 👋📥
- **Rascunho Clínico**: O sistema "ouve" a consulta e gera sugestões automáticas dos 4 Inputs (Objetivo, Diagnostico, Conduta, Orientação), eliminando a digitação manual.

### 👁️ 2. NSS Vision (Visão Clínica)

- **OCR de Exames de Sangue**: Através de webhooks do n8n, o NSS ingere resultados laboratoriais estruturados. 👋🔬
- **Alertas de Biomarcadores**: Identificação automática de deficiências ou excessos (ex: Ferritina Baixa) com cruzamento imediato de valores de referência.

### 🔬 3. NSS Intelligence (Pesquisa Científica)

- **Clinical Scholar via Firecrawl**: O Agente Ph.D. realiza pesquisas em tempo real no PubMed e bases acadêmicas para fundamentar condutas complexas ou raras. 👋📚
- **Curadoria Científica**: Seu Digest Diário inclui uma seção de estudos relevantes baseada nos temas dos pacientes agendados para o dia.

### 🧠 4. NSS Oracle (Memória do Conhecimento)

- **Vector Memory (ChromaDB)**: Base de conhecimento privada da clínica. O NSS "vetoriza" cada consulta e sucesso anterior em uma memória de longo prazo. 👋🧠
- **RAG Clínico**: Antes de prescrever, a IA consulta o Oracle: *"O que funcionou para pacientes similares no passado?"*. A clínica torna-se um ativo intelectual que aprende a cada consulta.

### 🎮 5. NSS Command (Centro de Comando)

- **Conversacional Agent**: Interface única via `/chat/command`. O médico gerencia toda a clínica por linguagem natural. 👋🤖
- **Roteamento de Intenções**: A IA orquestra todos os módulos acima em uma única resposta clínica curta e precisa, mantendo o contexto de sessão via **Redis**.

---

## 🛠️ Tecnologias de Elite

- **Backend & API**: Python 3.12 + FastAPI + Uvicorn
- **Cache & Session**: Redis (Stateless Mode - Fator VI)
- **Vector DB**: ChromaDB (RAG e Memória Clínica)
- **AI Suite**: CrewAI + OpenAI GPT-4o
- **Cloud Crawler**: Firecrawl (Pesquisa Clínica PubMed)
- **Webhooks**: Fathom AI (Listen) e n8n (Vision)
- **Telemetria**: Papertrail + Slack Webhooks + contextvars (Correlation ID - Fator XI)
- **Data Flow**: Google Workspace API (Sheets, Docs, Drive, Gmail, Calendar)

---

## 📦 Como Subir a Clínica (Setup de Produção)

O NSS Sabla foi desenhado para ser "Plug and Play" e resiliente.

### 1. Preparação das Chaves

Coloque seu `credentials.json` na raiz e preencha o `.env` (API Keys: OpenAI, Redis, Firecrawl, Fathom, Slack Webhook).

### 2. Ativação via Docker

```powershell
# Sobe todo o ecossistema (App + Redis + ChromaDB + Telemetria)
docker-compose up -d --build
```

### 3. Realizar o Login (Onboarding)

Abra o navegador em:
[http://localhost:8000/onboarding/google](http://localhost:8000/onboarding/google)

Após o login bem-sucedido, o sistema estará 100% autorizado e operando.

### 4. Health Check e Interface

- **Status Geral**: [http://localhost:8000/health](http://localhost:8000/health)
- **Command Query**: [http://localhost:8000/oracle/query?q=pergunta](http://localhost:8000/oracle/query?q=pergunta)

---

## ⚖️ Estrutura de Governança

```bash
├── nutriciones/
│   ├── core.py           # Central de Telemetria e Config (Fator III)
│   ├── models/           # Bio-Modelos e Rascunhos (Listen/Vision)
│   ├── services/         
│   │   ├── memory/       # NSS Oracle (ChromaDB Embeddings)
│   │   ├── search/       # NSS Intelligence (Firecrawl Scholar)
│   │   ├── google/       # SSoT e Workspace Flow
│   │   └── fathom_service.py # NSS Listen
│   └── agents/           # Centro de Comando e Oráculo Ph.D.
├── main_api.py           # Webhooks e Centro de Comando Conversacional
├── Dockerfile            # Imagem Stateless Otimizada
└── docker-compose.yml    # Orquestração Total do Ecossistema
```

---

> [!TIP]
> **Alívio Cognitivo**: O profissional não opera um software; ele gerencia um ecossistema de inteligência que olha, ouve, estuda e aprende a cada minuto.

**NutricioneS Sabla - High Performance Clinical Intelligence** 🚀🥗
