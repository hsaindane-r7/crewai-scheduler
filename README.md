## CrewAI Task Planner Agent

A multi-agent task planner and executor built with **CrewAI**, **Pydantic**, and **async Python**. Given a goal, it breaks it into concrete subtasks with time estimates using two AI agents:

1. **Task Planner** - Decomposes goals into 5-10 actionable subtasks
2. **Task Executor & Refiner** - Adds realistic time estimates and logical ordering

Uses **Groq** (LLaMA 3.3 70B) as the LLM provider.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Groq API key (get one at [console.groq.com](https://console.groq.com))

## Quick Start

### 1. Clone and setup

```bash
cd crewai-agent

# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv sync
```

### 2. Configure API key

Create a `.env` file:

```bash
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

### 3. Run the planner

```bash
uv run python main.py "Get fit in 3 months" \
  --description "Create a workout plan, schedule gym sessions, track nutrition, and set up weekly progress check-ins."
```

Output files:
- `schedule.json` - Structured JSON output
- `schedule.txt` - Human-readable schedule

## Example Goals

```bash
# Personal fitness
uv run python main.py "Get fit in 3 months" \
  --description "Create a workout plan, schedule gym sessions, track nutrition, and set up weekly progress check-ins."

# Learning
uv run python main.py "Learn Python basics" \
  --description "Complete online course, build 3 small projects, document in GitHub"

# Project launch
uv run python main.py "Launch personal blog" \
  --description "Choose platform, design layout, write 5 posts, set up analytics, promote on social media"
```

---

## Docker

### Build the image

```bash
docker build -t crewai-agent .
```

### Run with Docker

```bash
docker run --rm \
  -e GROQ_API_KEY=your_key_here \
  crewai-agent \
  "Get fit in 3 months" \
  --description "Create a workout plan and track nutrition"
```

### Run interactively

```bash
docker run --rm -it \
  -e GROQ_API_KEY=your_key_here \
  --entrypoint /bin/bash \
  crewai-agent
```

---

## Kubernetes (Local)

Deploy locally using Docker Desktop, minikube, or kind.

### 1. Setup secret

```bash
# Copy the example and edit with your API key
cp k8s/secret.yaml.example k8s/secret.yaml
# Edit k8s/secret.yaml and replace YOUR_GROQ_API_KEY_HERE

# Or create directly with kubectl:
kubectl create namespace crewai-agent
kubectl create secret generic groq-api-key \
  --namespace=crewai-agent \
  --from-literal=GROQ_API_KEY=your_actual_key_here
```

### 2. Deploy manually

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply secret (after editing)
kubectl apply -f k8s/secret.yaml

# Deploy (long-running pod for debugging)
kubectl apply -f k8s/deployment.yaml

# Or run as a one-shot job
kubectl apply -f k8s/job.yaml
```

### 3. Run commands in the pod

```bash
# Get a shell
kubectl exec -it -n crewai-agent deployment/crewai-agent -- /bin/bash

# Run the planner
kubectl exec -n crewai-agent deployment/crewai-agent -- \
  uv run python main.py "Your goal" --description "Details here"

# View logs
kubectl logs -n crewai-agent deployment/crewai-agent
```

### 4. Cleanup

```bash
kubectl delete namespace crewai-agent
```

---

## Tilt (Local Development)

[Tilt](https://tilt.dev) provides live-reload Kubernetes development.

### Prerequisites

- Docker Desktop with Kubernetes enabled (or minikube/kind)
- [Install Tilt](https://docs.tilt.dev/install.html)

### Setup

```bash
# Create your secret file
cp k8s/secret.yaml.example k8s/secret.yaml
# Edit k8s/secret.yaml with your GROQ_API_KEY
```

### Run Tilt

```bash
tilt up
```

This will:
1. Build the Docker image
2. Deploy to your local Kubernetes cluster
3. Open the Tilt UI in your browser
4. Watch for file changes and live-reload

### Tilt UI Features

In the Tilt UI (`http://localhost:10350`):

- **run-planner** - Run with sample fitness goal
- **run-custom-goal** - Run with custom goal (edit Tiltfile to change)
- **shell** - Open a shell in the pod
- **view-logs** - View pod logs
- **cleanup-jobs** - Delete completed jobs
- **open-grafana** - Open Grafana dashboard (see Monitoring section)
- **open-prometheus** - Open Prometheus UI

### Tear down

```bash
tilt down
```

---

## Monitoring with Grafana & Prometheus

The project includes a monitoring stack for resource utilization:

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization dashboards
- **OpenTelemetry Collector** (optional) - Unified observability

### Access Dashboards

When running with Tilt, the monitoring stack is automatically deployed:

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin` (change in production!)
- **Prometheus**: http://localhost:9090

### Grafana Dashboard

A pre-configured dashboard shows:
- Pod CPU usage
- Pod memory usage
- CPU requests vs actual usage
- Memory requests vs actual usage

The dashboard automatically filters to the `crewai-agent` namespace.

### Metrics Collected

Prometheus automatically scrapes:
- **Kubernetes pod metrics** (CPU, memory, network)
- **Container metrics** via cAdvisor
- **Node metrics** (if available)

Pods are automatically discovered if they have the annotation:
```yaml
prometheus.io/scrape: "true"
```

### OpenTelemetry (Optional)

To enable OpenTelemetry Collector:

1. Uncomment the OpenTelemetry section in `Tiltfile`
2. Restart Tilt: `tilt up`

The collector will:
- Scrape Prometheus metrics
- Accept OTLP traces/metrics from your application
- Export to Prometheus format for Grafana

### Manual Deployment

If not using Tilt:

```bash
# Deploy Prometheus
kubectl apply -f k8s/monitoring/prometheus-config.yaml
kubectl apply -f k8s/monitoring/prometheus.yaml

# Deploy Grafana
kubectl apply -f k8s/monitoring/grafana.yaml

# Optional: Deploy OpenTelemetry Collector
kubectl apply -f k8s/monitoring/opentelemetry-collector.yaml

# Port forward to access UIs
kubectl port-forward -n crewai-agent service/prometheus 9090:9090
kubectl port-forward -n crewai-agent service/grafana 3000:3000
```

---

## Project Structure

```
crewai-agent/
├── main.py           # CLI entrypoint
├── agents.py         # CrewAI agents and crew setup
├── models.py         # Pydantic models (Goal, SubTask, Schedule)
├── async_io.py       # Async file I/O and mock calendar
├── pyproject.toml    # Project dependencies (uv)
├── Dockerfile        # Container image
├── Tiltfile          # Tilt configuration
└── k8s/
    ├── namespace.yaml
    ├── secret.yaml.example
    ├── deployment.yaml
    ├── job.yaml
    └── monitoring/
        ├── prometheus-config.yaml
        ├── prometheus.yaml
        ├── grafana.yaml
        └── opentelemetry-collector.yaml
```

## License

MIT

