# ⚡ GridFlow-TX: ERCOT Real-Time Grid Analytics & BESS Arbitrage Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Grafana](https://img.shields.io/badge/Observability-LGTM_Stack-F46800?style=flat-square&logo=grafana&logoColor=white)](https://grafana.com/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform_1.13-7B42BC?style=flat-square&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Ansible](https://img.shields.io/badge/DevOps-Ansible-EE0000?style=flat-square&logo=ansible&logoColor=white)](https://www.ansible.com/)
[![Docker](https://img.shields.io/badge/Containers-Docker_Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/features/actions)

---

## 📌 Executive Summary

**GridFlow-TX** is an enterprise-grade, real-time energy analytics and Battery Energy Storage System (**BESS**) price arbitrage intelligence platform designed for the **Texas ERCOT (Electric Reliability Council of Texas)** power grid market. 

The platform aggregates real-time electric grid settlement prices, system demand, and generation mix to provide predictive machine learning models for battery storage arbitrage operations. It features a complete **LGTM (Loki, Grafana, Tempo, Prometheus)** observability stack with **OpenTelemetry** distributed tracing, automated **Terraform** infrastructure provisioning on AWS, and zero-downtime **Ansible** configuration management.

---

## 🏛️ System Architecture

GridFlow-TX follows an event-driven microservices hub architecture supported by full-stack observability and automated cloud deployment pipelines.

```mermaid
flowchart TB
    subgraph DataSources["🔌 Real-Time Data Ingestion Layer"]
        ERCOT["⚡ ERCOT Grid API / GridStatus"]
        HIST["📊 30-Day Historical Settlement Window"]
    end

    subgraph CorePlatform["🚀 GridFlow Core Application Hub"]
        GW["🌐 Microservices Gateway Hub (service_registry.py)"]
        DASH["🎨 Streamlit Reactive Dashboard (app.py / dashboard.py)"]
        BESS["🔋 BESS Arbitrage ML Engine (bess_intelligence.py)"]
        LIVE["📈 Real-Time Grid Analytics Engine (live_analytics.py)"]
    end

    subgraph ObservabilityStack["🔭 LGTM Observability & Telemetry Stack"]
        OTEL["📡 Telemetry Tracer (telemetry_tracer.py)"]
        PROM["📊 Prometheus RED Metrics (Port 8000/9090)"]
        TEMPO["🔗 Tempo Distributed Tracing (Port 3200/4318)"]
        LOKI["📜 Loki Log Aggregator (Port 3100)"]
        PROMTAIL["📦 Promtail Log Collector (Port 9080)"]
        GRAFANA["🖥️ Grafana Dashboards (Port 3000)"]
    end

    subgraph Infrastructure["☁️ Cloud & DevOps Infrastructure"]
        TF["🏗️ Terraform AWS Provisioning (VPC, Subnets, EC2, S3)"]
        ANS["⚙️ Ansible Automation Playbooks (setup-node, deploy-app)"]
        GHA["🚀 GitHub Actions CI/CD Pipeline & GHCR Matrix"]
    end

    ERCOT --> GW
    HIST --> BESS
    GW --> DASH
    BESS --> DASH
    LIVE --> DASH

    DASH --> OTEL
    OTEL -->|Spans & Traces| TEMPO
    OTEL -->|RED Metrics| PROM
    DASH -->|Application Logs| PROMTAIL
    PROMTAIL --> LOKI

    TEMPO --> GRAFANA
    PROM --> GRAFANA
    LOKI --> GRAFANA

    GHA -->|Build & Test| TF
    GHA -->|Deploy Containers| ANS
```

---

## 🔋 BESS Arbitrage & Machine Learning Pipeline

The BESS Intelligence Engine analyzes historical price volatility and predicts optimal charge/discharge windows across flexible horizons (**8h, 16h, 24h**).

```mermaid
sequenceDiagram
    autonumber
    participant UI as Streamlit Dashboard
    participant BESS as BESS ML Engine
    participant Data as ERCOT Settlement Data
    participant Model as Random Forest / XGB Regressor
    participant OTEL as Telemetry Tracer

    UI->>BESS: Request Arbitrage Matrix (Window: 8h/16h/24h, Capacity: MWh)
    BESS->>OTEL: Start Span "bess_arbitrage_computation"
    BESS->>Data: Fetch 30-day historical LMP settlement prices
    Data-->>BESS: Return Pandas DataFrame (Time-indexed LMPs)
    BESS->>Model: Run multi-step forecast & price ranking
    Model-->>BESS: Return predicted prices & confidence intervals
    BESS->>BESS: Calculate Optimal Charge (Lowest LMP) & Discharge (Highest LMP)
    BESS->>BESS: Compute Net Daily Arbitrage Profit ($) & ROI (%)
    BESS->>OTEL: Record Metrics (Execution time, Arbitrage Profit)
    BESS-->>UI: Render Interactive Matrix & Forecast Table
```

---

## 🛠️ Key Capabilities & Features

### 1. 🌐 Microservices Gateway Hub & Dynamic Registry
- Dynamic health checks and uptime monitoring for internal services.
- Real-time routing state across core modules (`live_analytics`, `bess_intelligence`, `observability`).

### 2. 🔋 BESS Energy Arbitrage Matrix
- **Flexible Time Horizons**: Selectable prediction windows for **8 hours, 16 hours, and 24 hours**.
- **Financial Arbitrage Modeling**: Calculates round-trip efficiency losses, degradation estimates, net profit ($), and return on investment (ROI %).
- **Interactive Prediction Tables**: Detailed breakdown of hourly prices, charge recommendations, and peak discharge slots.

### 3. 📈 ERCOT Real-Time Analytics
- **Live System Demand & Frequency**: Monitors Texas grid load (MW) and grid frequency stability (Hz).
- **Zonal Locational Marginal Prices (LMP)**: Real-time price tracking across Houston, North, South, and West ERCOT congestion zones.
- **Fuel Generation Mix**: Visualizes wind, solar, natural gas, nuclear, and coal power output percentages.

### 4. 🔭 LGTM Dual-Layer Observability & OpenTelemetry
- **Asynchronous Non-Blocking Tracing**: OpenTelemetry spans export via background threads without blocking main UI execution.
- **Custom RED Metrics**: Tracks Request Rate, Error Count, and Execution Duration exposed via Prometheus endpoints (`:8000` and `:8501`).
- **Pre-Configured Grafana Dashboards**: Dual-layer monitoring for microservices RED performance and waterfall distributed trace analysis in Grafana.

### 5. ☁️ DevOps & Infrastructure as Code (IaC)
- **Terraform AWS Infrastructure**: Automated VPC, public/private subnets, Security Groups, EC2 instances, and S3 telemetry storage.
- **Ansible Playbooks**: Automated node configuration, Docker installation, and one-command deployment (`ansible/playbooks/deploy-app.yml`).
- **GitHub Actions CI/CD**: Automated unit test execution via `pytest`, Security Component Analysis (SCA) scans, and multi-environment container image publishing to **GHCR**.

---

## 🌐 Services & Ports Map

| Component | Technology | Default Port | Description |
| :--- | :--- | :--- | :--- |
| **Streamlit Dashboard** | Python / Streamlit | `8501` | Interactive User Interface & Analytics Portal |
| **RED Metrics Server** | Prometheus Client | `8000` | Custom RED (Rate, Error, Duration) Metrics Endpoint |
| **Grafana** | Grafana LGTM | `3000` | Unified Telemetry, Log & Distributed Trace Dashboards |
| **Prometheus** | Prometheus | `9090` | Metrics Collector & Time-Series Database |
| **Tempo** | Grafana Tempo | `3200` / `4318` | OpenTelemetry OTLP/HTTP Distributed Tracing Sink |
| **Loki** | Grafana Loki | `3100` | Centralized Log Aggregation Engine |
| **Promtail** | Grafana Promtail | `9080` | Container Log Shipper for Loki |

---

## 💻 Quickstart & Local Setup Guide

### Option 1: Running with Docker Compose (Recommended)

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/joanroamora/GridFlow-TX.git
   cd GridFlow-TX
   ```

2. **Launch the Full Application Stack**:
   ```bash
   docker-compose up -d
   ```

3. **Access Services**:
   - **Streamlit App**: [http://localhost:8501](http://localhost:8501)
   - **Grafana Observability**: [http://localhost:3000](http://localhost:3000) (Anonymous admin enabled)
   - **Prometheus Metrics**: [http://localhost:9090](http://localhost:9090)

---

### Option 2: Manual Python Environment Setup

1. **Create and Activate a Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit Dashboard**:
   ```bash
   streamlit run app.py
   ```

---

## 🧪 Testing & Quality Assurance

GridFlow-TX includes a comprehensive automated test suite covering analytics, BESS intelligence algorithms, service registries, and telemetry tracing.

```bash
# Run pytest using the virtual environment
.venv/bin/pytest tests/ -v
```

### Test Suite Summary
- `tests/test_bess_intelligence.py`: Validates ML price forecasts and financial arbitrage ROI calculations.
- `tests/test_dashboard.py`: Verifies Streamlit UI layout logic, time windows, and multi-language translations.
- `tests/test_observability.py`: Ensures non-blocking OpenTelemetry spans and Prometheus RED metrics generation.
- `tests/test_service_registry.py`: Tests Gateway Hub service registration and health probes.
- `tests/test_translations.py`: Validates internationalization dictionaries (EN/ES).

---

## 🚀 DevOps & CI/CD Deployment

### Terraform AWS Provisioning
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Ansible Automated Deployment
```bash
cd ansible
ansible-playbook -i inventory.ini playbooks/setup-node.yml
ansible-playbook -i inventory.ini playbooks/deploy-app.yml
```

---

## 📄 License & Author

Developed with ❤️ by **Joan Roa** ([@joanroamora](https://github.com/joanroamora)).  
Project Repository: [GridFlow-TX](https://github.com/joanroamora/GridFlow-TX)

Released under the **MIT License**.
