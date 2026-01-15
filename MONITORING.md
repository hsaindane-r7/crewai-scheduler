# Prometheus Monitoring Guide

## Quick Start Queries

Copy and paste these queries into Prometheus to see your pod metrics:

### 1. Pod CPU Usage (per second)
```
rate(container_cpu_usage_seconds_total{namespace="crewai-agent"}[5m])
```

### 2. Pod Memory Usage (bytes)
```
container_memory_working_set_bytes{namespace="crewai-agent"}
```

### 3. Pod Memory Usage (human-readable MB)
```
container_memory_working_set_bytes{namespace="crewai-agent"} / 1024 / 1024
```

### 4. Pod CPU Usage Percentage
```
rate(container_cpu_usage_seconds_total{namespace="crewai-agent"}[5m]) * 100
```

### 5. All Metrics for crewai-agent Pod
```
{namespace="crewai-agent", pod=~"crewai-agent.*"}
```

### 6. Pod Resource Requests vs Usage (CPU)
```
kube_pod_container_resource_requests{namespace="crewai-agent", resource="cpu"}
```

### 7. Pod Resource Limits vs Usage (Memory)
```
kube_pod_container_resource_limits{namespace="crewai-agent", resource="memory"}
```

## Check Prometheus Targets

1. In Prometheus UI, click **"Status"** → **"Targets"** in the top menu
2. You should see targets like:
   - `kubernetes-pods`
   - `kubernetes-nodes`
   - `kubernetes-cadvisor`
   - `prometheus`

If targets show as "DOWN", check:
- Prometheus has RBAC permissions (should be automatic)
- Kubernetes API is accessible from Prometheus pod

## Troubleshooting

### No metrics showing up?

1. **Check if Prometheus can scrape Kubernetes:**
   ```
   kubectl logs -n crewai-agent deployment/prometheus | grep -i error
   ```

2. **Verify pod is running:**
   ```
   kubectl get pods -n crewai-agent
   ```

3. **Check Prometheus targets:**
   - Go to Prometheus UI → Status → Targets
   - Look for `kubernetes-cadvisor` target (should be UP)

4. **Test a simple query:**
   ```
   up{job="kubernetes-cadvisor"}
   ```
   This should return `1` if cAdvisor scraping is working.

### cAdvisor metrics not available?

Some Kubernetes distributions (like Docker Desktop) may not expose cAdvisor metrics. In that case:

1. **Use node exporter** (if available)
2. **Or use kube-state-metrics** for resource requests/limits
3. **Or rely on Prometheus node_exporter** if installed

## View in Grafana

For a visual dashboard, use Grafana:
- URL: http://localhost:3000
- Login: `admin` / `admin`
- Pre-configured dashboard: "Kubernetes Resource Utilization"

