# -*- mode: Python -*-

# Tiltfile for crewai-agent local Kubernetes development
# 
# Prerequisites:
#   - Docker Desktop with Kubernetes enabled, or minikube/kind
#   - Tilt installed: https://docs.tilt.dev/install.html
#   - Create your secret: cp k8s/secret.yaml.example k8s/secret.yaml
#     and fill in your GROQ_API_KEY
#
# Usage:
#   tilt up        # Start development environment
#   tilt down      # Tear down resources


# ============================================================================
# Configuration
# ============================================================================

# Allow deploying to the local Kubernetes context
allow_k8s_contexts(['docker-desktop', 'minikube', 'kind-kind', 'colima'])

# Load secret from file if it exists, otherwise remind user to create it
secret_file = 'k8s/secret.yaml'


# ============================================================================
# Build Docker Image
# ============================================================================

# Build the crewai-agent image with live updates for faster iteration
docker_build(
    'crewai-agent',
    '.',
    dockerfile='Dockerfile',
    live_update=[
        # Sync Python files for fast updates (no rebuild needed)
        sync('.', '/app'),
        # Trigger a rebuild if dependencies change
        run('uv sync --frozen --no-dev', trigger=['pyproject.toml', 'uv.lock']),
    ],
)


# ============================================================================
# Deploy Kubernetes Resources
# ============================================================================

# Create namespace first
k8s_yaml('k8s/namespace.yaml')

# Load secret (user must create this from the example file)
if os.path.exists(secret_file):
    k8s_yaml(secret_file)
else:
    fail('''
    ⚠️  Secret file not found!
    
    Create your secret file:
      cp k8s/secret.yaml.example k8s/secret.yaml
    
    Then edit k8s/secret.yaml and add your GROQ_API_KEY.
    ''')

# Deploy the long-running pod for interactive development
k8s_yaml('k8s/deployment.yaml')

# Give namespace its own resource for visibility
k8s_resource(
    objects=['crewai-agent:namespace'],
    new_name='crewai-agent-namespace',
    labels=['infra'],
)

# Track the secret as a resource
k8s_resource(
    objects=['groq-api-key:secret'],
    new_name='groq-api-key',
    labels=['infra'],
    resource_deps=['crewai-agent-namespace'],  # Secret needs namespace first
)

# Configure the deployment resource - depends on BOTH namespace AND secret
k8s_resource(
    'crewai-agent',
    port_forwards=[],  # No ports needed for CLI tool
    labels=['app'],
    resource_deps=['crewai-agent-namespace', 'groq-api-key'],  # Wait for namespace and secret
)

# ============================================================================
# Monitoring Stack (Prometheus + Grafana + OpenTelemetry)
# ============================================================================

# Deploy Prometheus for metrics collection
k8s_yaml('k8s/monitoring/prometheus-config.yaml')
k8s_yaml('k8s/monitoring/prometheus.yaml')

k8s_resource(
    'prometheus',
    port_forwards=['9090:9090'],  # Forward Prometheus UI to localhost:9090
    labels=['monitoring'],
    resource_deps=['crewai-agent-namespace'],
)

# Deploy Grafana for visualization
k8s_yaml('k8s/monitoring/grafana.yaml')

k8s_resource(
    'grafana',
    port_forwards=['3000:3000'],  # Forward Grafana UI to localhost:3000
    labels=['monitoring'],
    resource_deps=['prometheus'],  # Wait for Prometheus to be ready
)

# Optional: Deploy OpenTelemetry Collector
# Uncomment the lines below to enable OpenTelemetry
# k8s_yaml('k8s/monitoring/opentelemetry-collector.yaml')
# 
# k8s_resource(
#     'otel-collector',
#     port_forwards=['4317:4317', '4318:4318', '8889:8889'],
#     labels=['monitoring'],
#     resource_deps=['crewai-agent-namespace'],
# )


# ============================================================================
# Local Commands (Buttons in Tilt UI)
# ============================================================================

# Button to run the planner with a sample goal
local_resource(
    'run-planner',
    cmd='''
    kubectl exec -n crewai-agent deployment/crewai-agent -- \
        uv run python main.py "Get fit in 3 months" \
        --description "Create a workout plan, schedule gym sessions, track nutrition, and set up weekly progress check-ins."
    ''',
    labels=['commands'],
    resource_deps=['crewai-agent'],
    auto_init=False,  # Don't run automatically
    trigger_mode=TRIGGER_MODE_MANUAL,
)

# Button to run with custom goal (edit the command as needed)
local_resource(
    'run-custom-goal',
    cmd='''
    kubectl exec -n crewai-agent deployment/crewai-agent -- \
        uv run python main.py "Learn Python basics" \
        --description "Complete online course, build 3 small projects, document in GitHub"
    ''',
    labels=['commands'],
    resource_deps=['crewai-agent'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

# Button to get a shell in the pod
local_resource(
    'shell',
    cmd='kubectl exec -it -n crewai-agent deployment/crewai-agent -- /bin/bash',
    labels=['commands'],
    resource_deps=['crewai-agent'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

# Button to view logs
local_resource(
    'view-logs',
    cmd='kubectl logs -n crewai-agent deployment/crewai-agent --tail=100',
    labels=['commands'],
    resource_deps=['crewai-agent'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

# Button to open Grafana UI
local_resource(
    'open-grafana',
    cmd='open http://localhost:3000',
    labels=['monitoring'],
    resource_deps=['grafana'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

# Button to open Prometheus UI
local_resource(
    'open-prometheus',
    cmd='open http://localhost:9090',
    labels=['monitoring'],
    resource_deps=['prometheus'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)


# ============================================================================
# Cleanup helpers
# ============================================================================

# Button to delete and recreate the job (useful for re-running)
local_resource(
    'cleanup-jobs',
    cmd='kubectl delete jobs -n crewai-agent --all',
    labels=['cleanup'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

