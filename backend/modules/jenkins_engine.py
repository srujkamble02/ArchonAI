"""
jenkins_engine.py
Generates Jenkins CI/CD pipeline recommendations based on architecture and tech stack.
All logic is rule-based — no LLM involvement.
"""




from .currency import format_usd_as_inr


# ── Technology detection maps ────────────────────────────────────────────────
LANG_CONFIGS = {
    "python": {
        "build_tool": "pip",
        "test_cmd": "pytest",
        "lint_cmd": "flake8 . && pylint src/",
        "security_scan": "bandit -r src/ && safety check",
        "install_cmd": "pip install -r requirements.txt",
        "build_cmd": "python setup.py build",
        "docker_base": "python:3.11-slim",
    },
    "node": {
        "build_tool": "npm",
        "test_cmd": "npm test",
        "lint_cmd": "npm run lint",
        "security_scan": "npm audit --audit-level=moderate",
        "install_cmd": "npm ci",
        "build_cmd": "npm run build",
        "docker_base": "node:20-alpine",
    },
    "java": {
        "build_tool": "maven",
        "test_cmd": "mvn test",
        "lint_cmd": "mvn checkstyle:check",
        "security_scan": "mvn dependency-check:check",
        "install_cmd": "mvn install -DskipTests",
        "build_cmd": "mvn package -DskipTests",
        "docker_base": "eclipse-temurin:17-jre-alpine",
    },
    "go": {
        "build_tool": "go",
        "test_cmd": "go test ./...",
        "lint_cmd": "golangci-lint run",
        "security_scan": "gosec ./...",
        "install_cmd": "go mod download",
        "build_cmd": "go build -o app .",
        "docker_base": "golang:1.21-alpine",
    },
}


def generate_jenkins_pipeline(features: dict, architecture: dict, cloud_provider: str = "AWS") -> dict:
    """Generate a complete Jenkins CI/CD pipeline recommendation."""
    arch_type = architecture.get("architecture", "")
    components = architecture.get("components", [])
    scale = features.get("scale", 10_000)

    # Detect primary language from components
    lang = _detect_language(components, features)
    lang_cfg = LANG_CONFIGS.get(lang, LANG_CONFIGS["node"])

    # Determine if Docker/containerization is needed
    uses_docker = "Microservices" in arch_type or "Event-Driven" in arch_type or scale > 50_000
    uses_k8s = "Microservices" in arch_type or scale > 100_000

    # Build pipeline stages
    stages = _build_stages(lang, lang_cfg, arch_type, features, cloud_provider, uses_docker, uses_k8s)

    # Generate Jenkinsfile
    jenkinsfile = _generate_jenkinsfile(lang, lang_cfg, stages, arch_type, cloud_provider, uses_docker, uses_k8s)

    # Generate justification
    justification = _generate_justification(arch_type, features, scale)

    # Generate alternatives comparison
    alternatives = _build_devops_alternatives(arch_type, features, cloud_provider)

    # Rollback strategy
    rollback = _rollback_strategy(arch_type, uses_docker, uses_k8s)

    # Monitoring integration
    monitoring = _monitoring_integration(arch_type, cloud_provider)

    return {
        "ci_cd_tool": "Jenkins",
        "primary_language": lang,
        "uses_docker": uses_docker,
        "uses_kubernetes": uses_k8s,
        "stages": stages,
        "jenkinsfile": jenkinsfile,
        "justification": justification,
        "alternatives": alternatives,
        "rollback_strategy": rollback,
        "monitoring": monitoring,
        "deployment_target": _deployment_target(arch_type, cloud_provider, uses_k8s),
    }


def _detect_language(components: list, features: dict) -> str:
    """Detect primary language from components."""
    techs = " ".join(c.get("tech", "").lower() for c in components)

    if "fastapi" in techs or "python" in techs or "django" in techs or "flask" in techs:
        return "python"
    if "spring" in techs or "java" in techs or "maven" in techs or "gradle" in techs:
        return "java"
    if "go" in techs or "golang" in techs or "gin" in techs:
        return "go"
    # Default to Node.js (React + Node is the most common web stack)
    return "node"


def _build_stages(lang, lang_cfg, arch_type, features, cloud_provider, uses_docker, uses_k8s):
    """Build ordered pipeline stages based on project requirements."""
    stages = []

    # 1. Source Code Checkout
    stages.append({
        "name": "Source Code Checkout",
        "description": "Clone source repository and checkout target branch",
        "tools": ["Git", "Jenkins SCM"],
        "stage_id": "checkout",
    })

    # 2. Dependency Installation
    stages.append({
        "name": "Dependency Installation",
        "description": f"Install project dependencies using {lang_cfg['build_tool']}",
        "tools": [lang_cfg["build_tool"]],
        "stage_id": "install",
    })

    # 3. Code Compilation / Build
    stages.append({
        "name": "Code Compilation / Build",
        "description": f"Compile and build the application using {lang_cfg['build_cmd']}",
        "tools": [lang_cfg["build_tool"]],
        "stage_id": "build",
    })

    # 4. Static Code Analysis
    stages.append({
        "name": "Static Code Analysis",
        "description": f"Run linting and static analysis: {lang_cfg['lint_cmd']}",
        "tools": ["SonarQube", lang_cfg["build_tool"]],
        "stage_id": "lint",
    })

    # 5. Unit Testing
    stages.append({
        "name": "Unit Testing",
        "description": f"Execute unit tests: {lang_cfg['test_cmd']}",
        "tools": [lang_cfg["build_tool"]],
        "stage_id": "unit_test",
    })

    # 6. Integration Testing
    if "Microservices" in arch_type or features.get("real_time") or features.get("payments"):
        stages.append({
            "name": "Integration Testing",
            "description": "Run integration tests against dependent services and databases",
            "tools": ["Docker Compose", "Testcontainers"],
            "stage_id": "integration_test",
        })

    # 7. Security / Vulnerability Scanning
    stages.append({
        "name": "Security / Vulnerability Scanning",
        "description": f"Scan for security vulnerabilities: {lang_cfg['security_scan']}",
        "tools": ["OWASP Dependency-Check", "Trivy", "Snyk"],
        "stage_id": "security_scan",
    })

    # 8. Docker Image Build (if applicable)
    if uses_docker:
        stages.append({
            "name": "Docker Image Build",
            "description": f"Build Docker image from {lang_cfg['docker_base']} base image",
            "tools": ["Docker", "BuildKit"],
            "stage_id": "docker_build",
        })

        # 9. Container/Image Scan
        stages.append({
            "name": "Container Image Scan",
            "description": "Scan Docker image for CVEs and misconfigurations",
            "tools": ["Trivy", "Grype"],
            "stage_id": "container_scan",
        })

    # 10. Deploy to Staging
    stages.append({
        "name": "Deploy to Staging",
        "description": f"Deploy to staging environment on {cloud_provider}",
        "tools": _deploy_tools(cloud_provider, uses_k8s),
        "stage_id": "staging_deploy",
    })

    # 11. Automated Testing on Staging
    stages.append({
        "name": "Automated Smoke Tests",
        "description": "Run smoke tests, API health checks, and E2E tests on staging",
        "tools": ["Postman/Newman", "Cypress", "curl"],
        "stage_id": "smoke_test",
    })

    # 12. Approval / Quality Gate
    stages.append({
        "name": "Approval / Quality Gate",
        "description": "Manual approval required before production deployment",
        "tools": ["Jenkins Input Step", "Slack Notification"],
        "stage_id": "approval",
    })

    # 13. Production Deployment
    stages.append({
        "name": "Production Deployment",
        "description": f"Blue-green deployment to production on {cloud_provider}",
        "tools": _deploy_tools(cloud_provider, uses_k8s),
        "stage_id": "prod_deploy",
    })

    # 14. Post-Deploy Monitoring
    stages.append({
        "name": "Post-Deploy Monitoring & Rollback",
        "description": "Verify health metrics; automatic rollback if error rate exceeds threshold",
        "tools": ["Prometheus", "Grafana", "CloudWatch", "PagerDuty"],
        "stage_id": "monitoring",
    })

    return stages


def _deploy_tools(cloud_provider, uses_k8s):
    tools = []
    if uses_k8s:
        tools.extend(["kubectl", "Helm"])
    if cloud_provider == "AWS":
        tools.extend(["AWS CLI", "ECS/EKS" if uses_k8s else "EC2/ECS"])
    elif cloud_provider == "GCP":
        tools.extend(["gcloud CLI", "GKE" if uses_k8s else "Cloud Run"])
    elif cloud_provider == "Azure":
        tools.extend(["Azure CLI", "AKS" if uses_k8s else "App Service"])
    return tools


def _generate_jenkinsfile(lang, lang_cfg, stages, arch_type, cloud_provider, uses_docker, uses_k8s):
    """Generate a realistic Jenkinsfile for the project."""

    registry = {
        "AWS": "ECR_REGISTRY",
        "GCP": "GCR_REGISTRY",
        "Azure": "ACR_REGISTRY",
    }.get(cloud_provider, "DOCKER_REGISTRY")

    lines = [
        "pipeline {",
        "    agent any",
        "",
        "    environment {",
        f"        APP_NAME        = 'archon-app'",
        f"        REGISTRY        = credentials('{registry}')",
        "        IMAGE_TAG       = \"${env.BUILD_NUMBER}-${env.GIT_COMMIT?.take(7)}\"",
    ]

    if uses_docker:
        if cloud_provider == "AWS":
            lines.append("        AWS_REGION      = 'us-east-1'")
            lines.append("        ECR_REPO        = \"${REGISTRY}/${APP_NAME}\"")
        elif cloud_provider == "GCP":
            lines.append("        GCP_PROJECT     = credentials('GCP_PROJECT_ID')")
            lines.append("        GCR_REPO        = \"gcr.io/${GCP_PROJECT}/${APP_NAME}\"")
        elif cloud_provider == "Azure":
            lines.append("        ACR_REPO        = \"${REGISTRY}.azurecr.io/${APP_NAME}\"")

    lines += [
        "    }",
        "",
        "    options {",
        "        timeout(time: 30, unit: 'MINUTES')",
        "        disableConcurrentBuilds()",
        "        buildDiscarder(logRotator(numToKeepStr: '10'))",
        "    }",
        "",
        "    stages {",
    ]

    # Generate stage blocks
    for stage in stages:
        sid = stage["stage_id"]
        lines.append(f"        stage('{stage['name']}') {{")
        lines.append("            steps {")

        if sid == "checkout":
            lines.append("                checkout scm")
            lines.append("                echo \"Building branch: ${env.BRANCH_NAME}\"")

        elif sid == "install":
            lines.append(f"                sh '{lang_cfg['install_cmd']}'")

        elif sid == "build":
            lines.append(f"                sh '{lang_cfg['build_cmd']}'")

        elif sid == "lint":
            lines.append(f"                sh '{lang_cfg['lint_cmd']}'")

        elif sid == "unit_test":
            lines.append(f"                sh '{lang_cfg['test_cmd']}'")
            if lang == "python":
                lines.append("                junit 'reports/*.xml'")
            elif lang == "java":
                lines.append("                junit '**/target/surefire-reports/*.xml'")

        elif sid == "integration_test":
            lines.append("                sh 'docker-compose -f docker-compose.test.yml up -d'")
            lines.append(f"                sh '{lang_cfg['test_cmd']} --integration'")
            lines.append("                sh 'docker-compose -f docker-compose.test.yml down'")

        elif sid == "security_scan":
            lines.append(f"                sh '{lang_cfg['security_scan']}'")

        elif sid == "docker_build":
            lines.append("                sh \"docker build -t ${APP_NAME}:${IMAGE_TAG} .\"")
            if cloud_provider == "AWS":
                lines.append("                sh \"aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${REGISTRY}\"")
                lines.append("                sh \"docker tag ${APP_NAME}:${IMAGE_TAG} ${ECR_REPO}:${IMAGE_TAG}\"")
                lines.append("                sh \"docker push ${ECR_REPO}:${IMAGE_TAG}\"")
            elif cloud_provider == "GCP":
                lines.append("                sh \"docker tag ${APP_NAME}:${IMAGE_TAG} ${GCR_REPO}:${IMAGE_TAG}\"")
                lines.append("                sh \"docker push ${GCR_REPO}:${IMAGE_TAG}\"")

        elif sid == "container_scan":
            lines.append("                sh \"trivy image --severity HIGH,CRITICAL --exit-code 1 ${APP_NAME}:${IMAGE_TAG}\"")

        elif sid == "staging_deploy":
            if uses_k8s:
                lines.append("                sh \"helm upgrade --install ${APP_NAME}-staging ./helm-chart --namespace staging --set image.tag=${IMAGE_TAG}\"")
            else:
                lines.append(f"                sh 'echo Deploying to {cloud_provider} staging...'")
                if cloud_provider == "AWS":
                    lines.append("                sh \"aws ecs update-service --cluster staging --service ${APP_NAME} --force-new-deployment\"")

        elif sid == "smoke_test":
            lines.append("                sh 'sleep 30'  // Wait for deployment to stabilize")
            lines.append("                sh 'curl -f http://staging.example.com/health || exit 1'")
            lines.append("                sh 'newman run postman/smoke-tests.json --bail'")

        elif sid == "approval":
            lines.append("                input message: 'Deploy to Production?', ok: 'Approve'")

        elif sid == "prod_deploy":
            if uses_k8s:
                lines.append("                sh \"helm upgrade --install ${APP_NAME} ./helm-chart --namespace production --set image.tag=${IMAGE_TAG} --set replicaCount=3\"")
            else:
                if cloud_provider == "AWS":
                    lines.append("                sh \"aws ecs update-service --cluster production --service ${APP_NAME} --force-new-deployment\"")
                else:
                    lines.append(f"                sh 'echo Deploying to {cloud_provider} production...'")

        elif sid == "monitoring":
            lines.append("                sh 'sleep 60'  // Allow metrics to stabilize")
            lines.append("                sh './scripts/verify-health.sh production'")
            lines.append("                echo 'Post-deploy verification complete'")

        lines.append("            }")
        lines.append("        }")
        lines.append("")

    # Close stages
    lines.append("    }")
    lines.append("")

    # Post block
    lines += [
        "    post {",
        "        success {",
        "            slackSend channel: '#deployments', color: 'good',",
        "                message: \"✅ ${APP_NAME} v${IMAGE_TAG} deployed to production successfully\"",
        "        }",
        "        failure {",
        "            slackSend channel: '#deployments', color: 'danger',",
        "                message: \"❌ ${APP_NAME} build #${env.BUILD_NUMBER} failed\"",
    ]
    if uses_k8s:
        lines += [
            "            sh \"helm rollback ${APP_NAME} --namespace production\"",
        ]
    lines += [
        "        }",
        "        always {",
        "            cleanWs()",
        "        }",
        "    }",
        "}",
    ]

    return "\n".join(lines)


def _generate_justification(arch_type, features, scale):
    reasons = [
        "Jenkins provides full control over the CI/CD pipeline with declarative and scripted pipeline syntax.",
        "Self-hosted Jenkins ensures sensitive code and credentials never leave the organization's infrastructure.",
        "Extensive plugin ecosystem (1,800+ plugins) supports integration with virtually any tool in the stack.",
    ]

    if "Microservices" in arch_type:
        reasons.append("Jenkins supports multi-branch pipelines essential for microservices with independent deployment cycles.")
    if features.get("security_critical"):
        reasons.append("Jenkins allows air-gapped deployment for security-critical environments without external SaaS dependencies.")
    if scale > 100_000:
        reasons.append("Jenkins distributed builds (master-agent architecture) scale horizontally for large enterprise workloads.")

    return {
        "summary": "Jenkins is recommended as the primary CI/CD orchestration server for this project.",
        "reasons": reasons,
    }


def _build_devops_alternatives(arch_type, features, cloud_provider):
    """Return alternative CI/CD tools with comparison."""
    return [
        {
            "name": "GitHub Actions",
            "category": "Cloud-hosted CI/CD",
            "advantages": [
                "Native GitHub integration with zero setup",
                "Large marketplace of reusable actions",
                "Free tier for public repositories",
                "YAML-based workflow definitions",
            ],
            "disadvantages": [
                "Vendor lock-in to GitHub",
                "Limited self-hosted runner control",
                "Complex matrix builds can be expensive",
                "Less control over execution environment",
            ],
            "best_for": "Small-to-mid teams already using GitHub with standard deployment patterns.",
            "estimated_cost": f"Free for public repos; {format_usd_as_inr(4)}/user/month for Teams",
        },
        {
            "name": "GitLab CI/CD",
            "category": "Integrated DevOps platform",
            "advantages": [
                "Built-in CI/CD with source code management",
                "Auto DevOps with minimal configuration",
                "Container registry included",
                "Security scanning built-in (SAST, DAST, dependency scanning)",
            ],
            "disadvantages": [
                "Heavier platform — CI/CD is part of a full DevOps suite",
                "Self-hosted GitLab requires significant infrastructure",
                "Smaller community than Jenkins",
            ],
            "best_for": "Teams wanting an all-in-one DevOps platform with built-in security scanning.",
            "estimated_cost": f"Free tier available; Premium {format_usd_as_inr(29)}/user/month",
        },
        {
            "name": "AWS CodePipeline + CodeBuild",
            "category": "Cloud-native CI/CD",
            "advantages": [
                "Deep AWS service integration",
                "Pay-per-build pricing",
                "IAM-based access control",
                "No infrastructure to manage",
            ],
            "disadvantages": [
                "AWS vendor lock-in",
                "Less flexible than Jenkins pipelines",
                "Limited plugin ecosystem",
                "Complex multi-account setups",
            ],
            "best_for": "AWS-native architectures with minimal custom pipeline requirements.",
            "estimated_cost": f"{format_usd_as_inr(1)}/pipeline/month + {format_usd_as_inr(0.005, decimals=2)}/build minute",
        },
    ]


def _rollback_strategy(arch_type, uses_docker, uses_k8s):
    strategies = []

    if uses_k8s:
        strategies.append({
            "method": "Helm Rollback",
            "description": "Instantly revert to previous Helm release revision",
            "command": "helm rollback <release-name> <revision>",
            "rto": "< 30 seconds",
        })
        strategies.append({
            "method": "Kubernetes Rolling Update Reversal",
            "description": "kubectl rollout undo reverts to the previous deployment spec",
            "command": "kubectl rollout undo deployment/<name>",
            "rto": "< 60 seconds",
        })
    elif uses_docker:
        strategies.append({
            "method": "Docker Image Tag Revert",
            "description": "Re-deploy the previous Docker image tag from the container registry",
            "command": "docker pull <registry>/<image>:<previous-tag>",
            "rto": "2-5 minutes",
        })

    strategies.append({
        "method": "Blue-Green Switch",
        "description": "Redirect load balancer from green (new) to blue (previous) environment",
        "command": "Update ALB/NLB target group to previous environment",
        "rto": "< 60 seconds",
    })

    strategies.append({
        "method": "Database Migration Rollback",
        "description": "Apply down-migration scripts to revert database schema changes",
        "command": "alembic downgrade -1 (Python) / flyway undo (Java)",
        "rto": "5-15 minutes depending on data volume",
    })

    return strategies


def _monitoring_integration(arch_type, cloud_provider):
    return {
        "health_checks": [
            "HTTP health endpoint (/health) polled every 30s",
            "Database connection pool saturation check",
            "Memory and CPU usage thresholds (alert at 80%)",
        ],
        "metrics_pipeline": [
            "Prometheus scrapes application metrics",
            "Grafana dashboards for request rate, error rate, latency (RED method)",
            f"{'CloudWatch' if cloud_provider == 'AWS' else 'Cloud Monitoring' if cloud_provider == 'GCP' else 'Azure Monitor'} for infrastructure metrics",
        ],
        "alerting": [
            "Error rate > 5% for 2 minutes → PagerDuty critical alert",
            "p99 latency > 2x baseline → warning alert",
            "Deployment failure → automatic Slack + PagerDuty notification",
        ],
        "auto_rollback_trigger": "Error rate > 10% within 5 minutes post-deployment triggers automatic rollback",
    }


def _deployment_target(arch_type, cloud_provider, uses_k8s):
    if uses_k8s:
        targets = {
            "AWS": "Amazon EKS (Elastic Kubernetes Service)",
            "GCP": "Google Kubernetes Engine (GKE)",
            "Azure": "Azure Kubernetes Service (AKS)",
        }
        return targets.get(cloud_provider, "Kubernetes Cluster")

    targets = {
        "AWS": "Amazon ECS with Fargate" if "Serverless" in arch_type else "Amazon EC2 with ALB",
        "GCP": "Google Cloud Run" if "Serverless" in arch_type else "Google Compute Engine",
        "Azure": "Azure Container Apps" if "Serverless" in arch_type else "Azure App Service",
    }
    return targets.get(cloud_provider, "Cloud VM Instances")
