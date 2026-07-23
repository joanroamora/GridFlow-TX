# 📐 Technical Architecture Specification — GridFlow-TX

This document provides a deep technical architecture specification for the **GridFlow-TX** platform, detailing its component topology, telemetry tracing pipelines, machine learning forecasting engine, and infrastructure automation models.

---

## 1. High-Level Component Topology

```mermaid
graph TD
    subgraph ClientLayer ["Client & Interface Layer"]
        User["👤 Web User / Dispatch Engineer"]
        Dashboard["🎨 Streamlit Reactive Dashboard (app.py)"]
    end

    subgraph ServiceLayer ["Microservices & Core Logic"]
        Registry["🌐 Service Registry (services/service_registry.py)"]
        Analytics["📈 Live Grid Analytics (services/live_analytics.py)"]
        BESSEngine["🔋 BESS Arbitrage Engine (services/bess_intelligence.py)"]
        I18n["🌐 I18n Engine (translations.py)"]
    end

    subgraph DataLayer ["Data & External APIs"]
        ERCOT_API["⚡ ERCOT Market Data / GridStatus"]
        Cache["💾 In-Memory Dataframes & Rolling Buffer"]
    end

    subgraph TelemetryLayer ["Observability & Monitoring (LGTM Stack)"]
        Tracer["📡 OpenTelemetry Tracer (observability/telemetry_tracer.py)"]
        Prometheus["📊 Prometheus (Metrics Collector :9090)"]
        Tempo["🔗 Grafana Tempo (Tracing Engine :3200)"]
        Loki["📜 Grafana Loki (Log Aggregation :3100)"]
        Grafana["🖥️ Grafana Visualization Platform (:3000)"]
    end

    User --> Dashboard
    Dashboard --> Registry
    Dashboard --> Analytics
    Dashboard --> BESSEngine
    Dashboard --> I18n

    Analytics --> ERCOT_API
    BESSEngine --> Cache
    Analytics --> Cache

    Dashboard --> Tracer
    BESSEngine --> Tracer
    Analytics --> Tracer

    Tracer -->|Non-blocking OTLP| Tempo
    Tracer -->|Custom RED Metrics| Prometheus
    Dashboard -->|Container Logs| Loki

    Tempo --> Grafana
    Prometheus --> Grafana
    Loki --> Grafana
```

---

## 2. Microservices Gateway & Service Registry Design

The microservices hub uses a decentralized registry pattern defined in [`services/service_registry.py`](file:///home/joanr/agentic-platforms/GridFlow-TX/services/service_registry.py).

### Registered Modules
- `live_analytics`: Fetches real-time ERCOT frequency, system load, and zonal LMPs.
- `bess_intelligence`: Handles ML feature extraction, price ranking, and financial arbitrage matrix generation.
- `observability`: Monitors OpenTelemetry exporter health and Prometheus RED metrics endpoint.

```mermaid
sequenceDiagram
    autonumber
    participant App as app.py
    participant Registry as ServiceRegistry
    participant Service as Live Analytics / BESS Engine

    App->>Registry: get_instance()
    Registry-->>App: ServiceRegistry Singleton
    App->>Registry: register_service(name, endpoint, health_fn)
    Registry->>Service: Execute health check probe
    Service-->>Registry: HealthStatus (UP / DOWN, latency_ms)
    Registry-->>App: Service Registration Verified
```

---

## 3. BESS Machine Learning & Financial Arbitrage Engine

The BESS Arbitrage Engine ([`services/bess_intelligence.py`](file:///home/joanr/agentic-platforms/GridFlow-TX/services/bess_intelligence.py)) converts raw ERCOT Locational Marginal Prices (LMP) into actionable charge/discharge schedules.

### Mathematical Formulation
Given an array of predicted hourly prices $P = [p_1, p_2, \dots, p_T]$ over horizon $T \in \{8, 16, 24\}$ hours:

1. **Optimal Charging Hours ($C$)**:
   $$C = \arg\min_{t \in T, |C|=k} \sum_{t \in C} p_t$$
2. **Optimal Discharging Hours ($D$)**:
   $$D = \arg\max_{t \in T, |D|=k} \sum_{t \in D} p_t \quad \text{subject to } t_D > t_C$$
3. **Gross Financial Yield ($Y_{\text{gross}}$)**:
   $$Y_{\text{gross}} = \sum_{t \in D} (p_t \cdot \eta_{\text{discharge}}) - \sum_{t \in C} \left(\frac{p_t}{\eta_{\text{charge}}}\right)$$
4. **Net Arbitrage Profit ($Y_{\text{net}}$)**:
   $$Y_{\text{net}} = Y_{\text{gross}} - \text{Degradation Cost} - \text{O\&M Expenses}$$

---

## 4. Telemetry & Observability Pipeline

Distributed tracing and metric gathering are implemented in [`observability/telemetry_tracer.py`](file:///home/joanr/agentic-platforms/GridFlow-TX/observability/telemetry_tracer.py).

```mermaid
flowchart LR
    subgraph ApplicationCode ["Application Code Execution"]
        SpanStart["@trace_span('bess_compute')"]
        Logic["Compute Arbitrage Matrix"]
        SpanEnd["Span End & Record Exception/Status"]
    end

    subgraph TelemetryTracer ["telemetry_tracer.py"]
        OTLP_Exp["OTLPSpanExporter (Async BatchSpanProcessor)"]
        Prom_Exp["Prometheus RED HTTP Exporter (:8000)"]
    end

    subgraph LGTM ["Grafana LGTM Stack"]
        TempoDB["Grafana Tempo (:4318)"]
        PromDB["Prometheus DB (:9090)"]
        GrafanaUI["Grafana Dashboards (:3000)"]
    end

    SpanStart --> Logic
    Logic --> SpanEnd
    SpanEnd --> OTLP_Exp
    SpanEnd --> Prom_Exp

    OTLP_Exp -->|HTTP / OTLP| TempoDB
    Prom_Exp -->|Scrape /metrics| PromDB
    TempoDB --> GrafanaUI
    PromDB --> GrafanaUI
```

### RED Metrics Specification
- **Request Rate (`gridflow_requests_total`)**: Counter tracking total API & analytics requests segmented by route.
- **Error Count (`gridflow_errors_total`)**: Counter tracking exception rates across microservice operations.
- **Execution Duration (`gridflow_request_duration_seconds`)**: Histogram measuring end-to-end processing latency.

---

## 5. Infrastructure & Deployment Model

The cloud architecture is specified declaratively in [`terraform/`](file:///home/joanr/agentic-platforms/GridFlow-TX/terraform) and configured via [`ansible/`](file:///home/joanr/agentic-platforms/GridFlow-TX/ansible).

```mermaid
flowchart TD
    subgraph AWS ["AWS Cloud (us-east-1)"]
        subgraph VPC ["VPC (10.0.0.0/16)"]
            subgraph PublicSubnet ["Public Subnet (10.0.1.0/24)"]
                EC2["EC2 Instance (t3.medium / Amazon Linux 2023)"]
                EIP["Elastic IP (44.214.20.80)"]
            end
            subgraph PrivateSubnet ["Private Subnet (10.0.10.0/24)"]
                DB["Internal Data Storage / S3 Telemetry Bucket"]
            end
            IGW["Internet Gateway"]
        end
    end

    subgraph CI_CD ["CI/CD Pipeline"]
        GHA["GitHub Actions Runner"]
        GHCR["GitHub Container Registry (GHCR)"]
    end

    EIP --- EC2
    PublicSubnet --- IGW
    GHA -->|Push Docker Image| GHCR
    EC2 -->|Pull Docker Image| GHCR
```

---

## 6. Directory Structure Overview

```
GridFlow-TX/
├── app.py                      # Main Streamlit Application Entrypoint
├── dashboard.py                # Core Dashboard Rendering & UI Layout
├── translations.py             # Internationalization Dictionary (EN / ES)
├── requirements.txt            # Python Dependencies Specification
├── docker-compose.yml          # Container Orchestration (LGTM Stack + App)
├── Dockerfile                  # Production Multi-Stage Container Spec
├── README.md                   # Project Overview & Quickstart Guide
├── ARCHITECTURE.md             # Deep Technical Architecture Specification
├── services/
│   ├── bess_intelligence.py    # BESS Energy Arbitrage ML Engine
│   ├── live_analytics.py       # ERCOT Real-time Data Ingestion Engine
│   └── service_registry.py     # Microservices Gateway Hub & Registry
├── observability/
│   ├── telemetry_tracer.py     # OpenTelemetry & Prometheus RED Exporter
│   ├── grafana/                # Pre-configured Dashboards & Datasources
│   ├── prometheus/             # Prometheus Scrape Configurations
│   ├── tempo/                  # Grafana Tempo Tracing Configuration
│   ├── loki/                   # Grafana Loki Configuration
│   └── promtail/               # Promtail Container Log Configuration
├── terraform/                  # Infrastructure as Code (AWS VPC, EC2, S3)
├── ansible/                    # Configuration Management & Deployment Playbooks
└── tests/                      # Automated Pytest Suite (100% Pass Rate)
```
