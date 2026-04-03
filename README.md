# 🥗 NutricioneS Sabla (NSS) - Diet Engine Architecture

Bem-vindo ao **NutricioneS Sabla (NSS)**, o motor de alta performance do ecossistema NutricioneS. Este projeto foi refatorado para seguir estritamente os padrões de arquitetura **Twelve-Factor App**, garantindo isolamento, escalabilidade e performance **O(1)** em consultas.

---

## 🚀 Principais Funcionalidades

- **Agente Nutricionista AI**: CrewAI integrado com a base TACO (SQLite) para gerar planos 100% plant-based e balanceados.
- **Performance O(1)**: Sistema de indexação binária local para o Google Sheets, eliminando latências de rede desnecessárias.
- **Embarque Atômico**: Cadastro simultâneo de pacientes, endereços, e-mails e telefones com provisionamento automático de pastas no **Google Drive**.
- **Gestão de Agenda**: Criação de slots de atendimento e agendamento de consultas com geração automática de links **Google Meet**.
- **Engine de PDF**: Geração de planos alimentares profissionais diretamente via Google Docs API.

---

## 🛠️ Tecnologias Utilizadas

- **Núcleo**: Python 3.10+
- **Database SSoT**: Google Sheets API v4
- **Cache Local**: Binário (.bin) via Pickle (Performance O(1))
- **Base Food**: SQLite (TACO Database)
- **AI Orchestrator**: CrewAI (com LangChain)
- **Cloud Suite**: Google Drive API, Google Docs API, Google Calendar API
- **Testes**: Pytest com Injeção de Mocks

---

## ⚙️ Configuração do Ambiente

Este projeto utiliza o **Factor II (Dependências)** do Twelve-Factor App, garantindo que o ambiente seja isolado e reproduzível.

### **1. Setup Rápido (Automatizado)**
Se você já possui o Python instalado, execute o script de bootstrap que cria o ambiente virtual e instala as dependências:
```powershell
python setup_dev.py
```

### **2. Ativação do Ambiente**
```powershell
# Windows
.\.venv\Scripts\Activate.ps1
```

### **3. Configuração do SSoT (Google Sheets)**
Para preparar a sua planilha do Google Sheets para receber os dados, rode o bootstrap de tabelas:
```powershell
python scripts/bootstrap_sheets.py
```

---

## 🧪 Suíte de Testes

Para garantir a integridade do sistema, execute a suíte de testes de integração:
```powershell
python -m pytest tests/
```

---

## 📁 Estrutura do Projeto

```bash
├── nutriciones/
│   ├── core/           # Configuração (Twelve-Factor: Factor III)
│   ├── models/         # Dataclasses Estritas (Rebirth Pattern)
│   ├── services/       # Lógica de Negócio (Sheets, Drive, Calendar, Dieta)
│   └── agents/         # CrewAI - Inteligência do Nutricionista
├── data/               # Base TACO (SQLite/JSON)
├── scripts/            # Utilitários de Bootstrap e Importação
├── tests/              # Testes de Integração e Performance
├── .env                # Variáveis de Ambiente (Segurança)
├── requirements.txt    # Manifesto de Dependências
└── setup_dev.py        # Setup Automatizado
```

---

## 🛡️ Contribuição

1. Mantenha os novos modelos compatíveis com o `WithPrimaryKeyProperty`.
2. Sempre declare novas dependências no `requirements.txt`.
3. Certifique-se de que novos scripts executam a verificação de `venv`.

---
*NutricioneS Sabla - High Performance Nutrition Backend*
