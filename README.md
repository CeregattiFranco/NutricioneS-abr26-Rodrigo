# 🏥 Clínica Sem Stress™ (Powered by NutricioneS Sabla - NSS)

> **"A tecnologia perfeita é aquela que você esquece que existe."**

O **NutricioneS Sabla (NSS)** é uma Infraestrutura Autônoma de Gestão Clínica e Bio-Inteligência. Construído sob a filosofia de *"Software a Menos"* e *"Encanamento Invisível"*, o NSS foi projetado para devolver ao profissional de saúde o foco 100% clínico, eliminando o estresse operacional através de fluxos agênticos (IA) e arquitetura DevOps de alta disponibilidade.

---

## 🚀 Os 7 Pilares da "Clínica Sem Stress"

O NSS opera em background ("sob as paredes" do consultório) monitorando, escutando e aprendendo com o ambiente clínico através de 7 módulos independentes:

### 🎙️ 1. NSS Listen (Escuta Ativa)

- **Transcrição Fathom AI**: Ingestão de áudio via Webhooks seguros (HMAC). 👋📥
- **Rascunho Clínico**: O sistema "ouve" a consulta e gera sugestões automáticas dos 4 Inputs (Objetivo, Diagnóstico, Conduta, Orientação), eliminando a digitação manual.

### 👁️ 2. NSS Vision (Visão Clínica)

- **OCR de Exames & Biometria**: Ingestão via webhooks do n8n (Tesseract/Vision). 👋🔬
- **Alertas de Biomarcadores**: Identificação automática de deficiências (ex: Ferritina baixa) com cruzamento imediato de valores de referência.

### 🔬 3. NSS Intelligence (Pesquisa Científica)

- **Clinical Scholar (Firecrawl)**: Pesquisas em tempo real no *PubMed* e *Google Scholar* para fundamentar condutas diante de diagnósticos complexos. 👋📚
- **Curadoria no Digest**: Seu e-mail diário inclui artigos científicos baseados nos temas das consultas do dia.

### 🧠 4. NSS Oracle (Memória Vetorial)

- **Cérebro Institucional (ChromaDB)**: O sistema vetoriza e "lembra" de todos os desfechos clínicos anteriores. 👋🧠
- **RAG de Sucesso**: Antes de prescrever, a IA consulta o Oráculo: *"O que funcionou para pacientes similares no passado?"*.

### 🚥 5. NSS Triage (Perfil Dominante)

- **Semáforo Clínico**: Pipeline de triagem que calcula scores em 5 dimensões (Metabólica, Emocional, Energia, Urgência, Segurança). 👋🚦
- **Safety Locks**: A IA é fisicamente bloqueada de prescrever protocolos agressivos para pacientes em "Alerta Vermelho" de estresse ou custo energético.

### 📊 6. NSS Analytics (Governança de Desfechos)

- **Auditoria de Retenção & LTV**: Correlação entre a Triagem de entrada e a Aderência final do paciente. 👋📈
- **Relatório de Eficácia**: Prova estatística de que as travas de segurança da IA aumentam o sucesso do tratamento e reduzem o Churn.

### 🛡️ 7. NSS Shield (Disaster Recovery)

- **Snapshots & Imutabilidade**: Exportação diária (03:00 AM) de todo o SSoT (Google Sheets) e Banco TACO para arquivos CSV. 👋🔐
- **Cloud Cold Storage**: Envio de backups compactados para AWS S3, garantindo resiliência total contra falhas humanas ou de infraestrutura.

---

## 🏗️ Arquitetura & Governança (12-Factor App)

O repositório NSS segue rigorosamente as metodologias de **Twelve-Factor App**:

- **I. Codebase & SSoT:** Todo o estado relacional vive no Google Sheets (Single Source of Truth), com datasets imutáveis em SQLite.
- **VI. Stateless Processes:** Zero dependência de arquivos locais. Todo o cache de relações e controle de Idempotência vive em **Redis**.
- **X. Dev/Prod Parity:** Orquestração via `docker-compose`. O ambiente local é idêntico ao ambiente de nuvem do cliente.
- **XI. Logs e Telemetria:** Centralização de Logs com *Correlation IDs* e *Dead Man's Snitch* (GitHub CI/CD Integrado).

---

## 🚀 CI/CD & Zero-Touch Deployment

Atualizações no sistema são gerenciadas através de uma esteira madura de DevOps:

1. **Continuous Integration (GitHub Actions):** Auditorias de código (`ruff`), testes de unidade e de integração isolados via `pytest` e `fakeredis`.
2. **Release Management (Release Please):** Versionamento semântico autogerado e Changelogs documentados a cada commit.
3. **Continuous Deployment (Watchtower & GHCR):** Imagens Docker compiladas no *GitHub Container Registry* com auto-update silencioso no servidor do cliente.

---

## 🛠️ Stack Tecnológico

- **Backend & API:** Python 3.11+, FastAPI.
- **Persistência & Cache:** Redis (Stateless Cache), SQLite (Dataset), ChromaDB (Vector Store).
- **Cloud & Infra:** AWS S3 (Backups), Google Workspace, Fathom AI, Firecrawl.
- **DevOps:** Docker, GitHub Actions, Pytest, Ruff, Watchtower.

---

## 🏁 Quick Start (Desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/nss-abr26-rodrigo.git

# 2. Suba a infraestrutura Stateless e o Banco Vetorial
docker-compose up -d --build

# 3. Autorize o App e Inicie o "Encanamento"
# Acesse: http://localhost:8000/onboarding/google
```

**NutricioneS Sabla - High Performance Clinical Intelligence** 🚀🥗🏗️📊⚖️🏆🏁🛡️⚓🚥🌥️📥

---

> [!NOTE]
> Para rodar a esteira de testes localmente sem acionar dependências externas, execute `pytest --cov=nutriciones`.

Desenvolvido para profissionais que escolhem focar em pessoas, não em sistemas.