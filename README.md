# 🏥 Clínica Sem Stress™ (Powered by NutricioneS Sabla - NSS)

> **"A tecnologia perfeita é aquela que você esquece que existe."**

O **NutricioneS Sabla (NSS)** é uma Infraestrutura Autônoma de Gestão Clínica e Bio-Inteligência. Construído sob a filosofia de *"Software a Menos"* e *"Encanamento Invisível"*, o NSS foi projetado para devolver ao profissional de saúde o foco 100% clínico, eliminando o estresse operacional através de fluxos agênticos (IA) e arquitetura DevOps de alta disponibilidade.

---

## 🧠 A Filosofia Operacional: Os 4 Inputs Clínicos

O sistema elimina a necessidade de o profissional navegar por dezenas de abas e formulários. A inteligência central é acionada exclusivamente pelo preenchimento de **4 pilares pós-consulta**:

1. **Objetivo:** A meta central do paciente (Ex: *"Perda de 5kg de gordura"*).
2. **Diagnóstico:** A análise técnica baseada em histórico e exames.
3. **Conduta:** A prescrição terapêutica/nutricional baseada em evidências.
4. **Orientação:** O plano de ação digerido para o paciente.

Ao salvar estes 4 inputs, o NSS orquestra autonomamente o envio de e-mails, arquivamento de documentos, organização de pastas no Drive e o agendamento de retornos.

---

## 🧩 O Ecossistema de Automação Invisível (NSS Suite)

O NSS opera em background ("sob as paredes" do consultório) monitorando, escutando e aprendendo com o ambiente clínico através de 6 sub-módulos independentes:

* 🎙️ **NSS Listen (Ingestão de Áudio):** Integração via Webhook com o **Fathom AI**. Transcreve e processa a consulta em tempo real, gerando rascunhos automáticos para os 4 Inputs Clínicos.
* 👁️ **NSS Vision (Biometria & OCR):** Integração com pipelines (n8n/Tesseract) para leitura de exames de sangue em PDF. Estrutura biomarcadores e alerta a IA sobre deficiências (ex: Ferritina baixa).
* 🔬 **NSS Intelligence (Pesquisa Científica):** Web Crawler estruturado (via **Firecrawl**) que busca ativamente artigos no *PubMed* e *Google Scholar* para embasar condutas diante de diagnósticos complexos.
* 🔮 **NSS Oracle (Memória Vetorial / RAG):** Cérebro institucional baseado em **ChromaDB**. O sistema vetoriza e "lembra" de todos os desfechos clínicos anteriores da clínica, sugerindo protocolos de sucesso com base em dados históricos locais.
* ⚡ **NSS Flow (Workflows de Engajamento):** Executa as 7 automações invisíveis de engajamento (Gotejamento de conteúdo, réguas de confirmação de 14d/7d/2d/2h e Digest Diário às 07:00 AM para o médico).
* 🛡️ **NSS Shield (Disaster Recovery):** Snapshot diário da Single Source of Truth (Google Sheets/SQLite) criptografado e salvo em Cold Storage, garantindo resiliência contra falhas humanas.

---

## 🏗️ Arquitetura e Governança (12-Factor App)

O repositório NSS segue rigorosamente as metodologias de **Twelve-Factor App**, garantindo que seja robusto, escalável e de fácil manutenção:

* **I. Codebase & SSoT:** Todo o estado relacional vive no Google Sheets (Single Source of Truth), enquanto dependências em massa (Tabela TACO) vivem em um SQLite imutável.
* **VI. Stateless Processes:** Zero dependência de arquivos locais temporários. Todo o cache de relações e controle de Idempotência vive em memória no **Redis**. O container pode ser destruído e recriado sem perda de contexto.
* **IX. Disposability:** Resiliência através de degradação graciosa. O sistema lida autonomamente com *rate limits* do Google e interrupções externas.
* **X. Dev/Prod Parity:** Orquestração via `docker-compose`. O ambiente local do desenvolvedor é idêntico ao ambiente de nuvem do cliente.
* **XI. Logs e Telemetria:** Centralização de Logs com *Correlation IDs* e *Dead Man's Snitch* (Alertas proativos via Webhook em caso de falha de serviços críticos).

---

## 🚀 CI/CD & Zero-Touch Deployment

Atualizações no sistema são gerenciadas através de uma esteira madura de DevOps:

1. **Continuous Integration (GitHub Actions):** Todo commit na branch `main` dispara auditorias de código (`ruff`), testes de unidade e de integração isolados via `pytest` e `fakeredis`.
2. **Release Management (Release Please):** Versionamento semântico autogerado e Changelogs documentados a cada *Conventional Commit*.
3. **Continuous Deployment (Watchtower & GHCR):** Imagens Docker são compiladas e enviadas ao *GitHub Container Registry*. Servidores em produção utilizam o sentinela *Watchtower* para realizar atualizações de imagem (Pull & Restart) de forma 100% autônoma (*zero-downtime update*).

---

## 🛠️ Stack Tecnológico

* **Backend & API:** Python 3.11+, FastAPI.
* **Persistência & Cache:** Redis (Stateless Cache), SQLite (Read-Only Dataset), ChromaDB (Vector Store).
* **IA & Agentes:** OpenAI (LLMs), CrewAI (Roteamento Agêntico).
* **Cloud & Integrações:** Google Workspace API (Drive, Docs, Sheets, Gmail, Calendar), Fathom AI, Firecrawl.
* **DevOps:** Docker, GitHub Actions, Pytest, Ruff.

---

## 🏁 Quick Start (Desenvolvimento)

Para iniciar o desenvolvimento ou a primeira execução local com isolamento total:

```bash
# 1. Clone o repositório e configure o .env
git clone [https://github.com/seu-usuario/nutriciones-abr26-rodrigo.git](https://github.com/seu-usuario/nutriciones-abr26-rodrigo.git)
cd nutriciones-abr26-rodrigo

# 2. Rode o Setup e as validações (Cria venv e verifica chaves)
python setup_nss.py

# 3. Suba a infraestrutura Stateless e o Banco Vetorial
docker-compose up -d --build

# 4. Autorize o App e Inicie o "Encanamento"
# Acesse: http://localhost:8000/onboarding/google
Nota: Para rodar a esteira de testes localmente sem acionar dependências externas, execute pytest --cov=nutriciones.

Desenvolvido para profissionais que escolhem focar em pessoas, não em sistemas.