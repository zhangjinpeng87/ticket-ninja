"""
Sample script to populate the knowledge base with example IT issues.
This demonstrates how to add entries to both common and tenant knowledge bases.
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.knowledge_base import get_knowledge_base_service
from app.models.knowledge_base import ITIssueCategory


def populate_common_kb():
    """Populate common knowledge base with example IT issues"""
    kb_service = get_knowledge_base_service()
    
    examples = [
        {
            "title": "PostgreSQL Connection Pool Exhaustion",
            "phenomenon": "Error: FATAL: remaining connection slots are reserved for non-replication superuser connections. Application unable to connect to database.",
            "root_cause_analysis": "The PostgreSQL database has reached its maximum connection limit. This typically occurs when connection pooling is not properly configured, connections are not being closed properly, or the max_connections setting is too low for the application load.",
            "solutions": [
                "Increase max_connections in postgresql.conf (requires restart)",
                "Implement connection pooling (e.g., PgBouncer) to reduce actual database connections",
                "Review application code to ensure all database connections are properly closed",
                "Monitor active connections using: SELECT count(*) FROM pg_stat_activity;",
                "Consider using read replicas to distribute read queries"
            ],
            "category": ITIssueCategory.DATABASE,
            "tags": ["postgresql", "connection", "pool", "database"],
        },
        {
            "title": "Kubernetes Pod CrashLoopBackOff",
            "phenomenon": "Pod status shows CrashLoopBackOff. kubectl logs shows: Error: failed to start application, exit code 1",
            "root_cause_analysis": "The container is crashing immediately after starting. Common causes include: application startup errors, missing environment variables, incorrect resource limits, health check failures, or dependency issues.",
            "solutions": [
                "Check pod logs: kubectl logs <pod-name>",
                "Verify environment variables are set correctly: kubectl describe pod <pod-name>",
                "Check resource limits and requests are appropriate",
                "Review application startup logs for configuration errors",
                "Verify health check endpoints are responding correctly",
                "Check if the container image is correct and dependencies are installed"
            ],
            "category": ITIssueCategory.KUBERNETES,
            "tags": ["kubernetes", "pod", "crashloop", "container"],
        },
        {
            "title": "AWS S3 403 Forbidden Error",
            "phenomenon": "Error: AccessDenied when calling the PutObject operation. 403 Forbidden response from S3 API.",
            "root_cause_analysis": "The IAM role or user credentials don't have sufficient permissions to perform the S3 operation. This could be due to missing IAM policies, incorrect bucket policies, or incorrect resource ARN in the policy.",
            "solutions": [
                "Verify IAM user/role has s3:PutObject permission for the bucket",
                "Check bucket policy allows the operation from the IAM principal",
                "Verify the bucket name and object key are correct",
                "Check if bucket encryption requires additional kms: permissions",
                "Review CloudTrail logs for detailed access denial reasons",
                "Ensure the IAM policy includes the correct resource ARN (bucket and objects)"
            ],
            "category": ITIssueCategory.CLOUD_INFRA,
            "tags": ["aws", "s3", "iam", "permissions", "403"],
        },
        {
            "title": "MySQL Deadlock Error",
            "phenomenon": "Error: Deadlock found when trying to get lock; try restarting transaction. (1213)",
            "root_cause_analysis": "Two or more transactions are waiting for each other to release locks, creating a circular dependency. This often happens with concurrent transactions accessing the same rows in different orders, or long-running transactions holding locks.",
            "solutions": [
                "Retry the transaction (MySQL automatically retries once)",
                "Ensure transactions access tables in a consistent order",
                "Reduce transaction duration by moving non-critical operations outside transactions",
                "Use lower isolation levels (READ COMMITTED instead of REPEATABLE READ) if appropriate",
                "Add appropriate indexes to reduce lock contention",
                "Consider using SELECT ... FOR UPDATE SKIP LOCKED for queue-like operations"
            ],
            "category": ITIssueCategory.DATABASE,
            "tags": ["mysql", "deadlock", "transaction", "locking"],
        },
        {
            "title": "Kubernetes Node Not Ready",
            "phenomenon": "kubectl get nodes shows node status as NotReady. Pods cannot be scheduled on the node.",
            "root_cause_analysis": "The kubelet on the node is not communicating with the API server, or the node has resource issues. Common causes: kubelet service stopped, disk pressure, network connectivity issues, or node resource exhaustion.",
            "solutions": [
                "Check kubelet status: systemctl status kubelet",
                "Review kubelet logs: journalctl -u kubelet -n 100",
                "Check node conditions: kubectl describe node <node-name>",
                "Verify disk space: df -h (especially /var/lib/kubelet)",
                "Check network connectivity between node and API server",
                "Review node resource usage (CPU, memory, disk)"
            ],
            "category": ITIssueCategory.KUBERNETES,
            "tags": ["kubernetes", "node", "notready", "kubelet"],
        },
        {
            "title": "CI/CD Pipeline Failure Due to Missing Secrets",
            "phenomenon": "Deployment pipeline fails at deploy stage. Error: Failed to fetch secret 'PROD_API_KEY' from secret store.",
            "root_cause_analysis": "A new environment variable was introduced but not added to the secret manager for the target environment. The pipeline attempts to retrieve the secret but fails, causing the deployment stage to stop.",
            "solutions": [
                "Add the missing secret to the secret manager (e.g., HashiCorp Vault, AWS Secrets Manager).",
                "Verify CI/CD service account/role has access to the secret.",
                "Add pipeline validation to ensure required secrets exist before deployment.",
                "Document new secret dependencies and update onboarding checklists.",
                "Add automated tests or pre-flight checks for secret availability."
            ],
            "category": ITIssueCategory.CI_CD,
            "tags": ["cicd", "pipeline", "secrets", "deployment"],
        },
    ]
    
    print("Populating common knowledge base...")
    for example in examples:
        entry_id = kb_service.add_common_entry(
            title=example["title"],
            phenomenon=example["phenomenon"],
            root_cause_analysis=example["root_cause_analysis"],
            solutions=example["solutions"],
            category=example["category"],
            tags=example["tags"],
            source_type="manual",
        )
        print(f"  ✓ Added: {example['title']} (ID: {entry_id})")
    
    print(f"\nCommon KB populated with {len(examples)} entries.")


def populate_tenant_kb_example(tenant_id: str = "example-tenant-1"):
    """Populate a tenant knowledge base with example resolved tickets"""
    kb_service = get_knowledge_base_service()
    
    examples = [
        {
            "title": "Payment Service Timeout in Production",
            "phenomenon": "Payment service timing out after 30 seconds. Error logs show: java.net.SocketTimeoutException: Read timed out when calling external payment gateway.",
            "root_cause_analysis": "The external payment gateway was experiencing high latency (500-800ms response times). Our service timeout was set to 30 seconds, but with retries and multiple gateway calls, the total time exceeded the timeout threshold.",
            "solutions": [
                "Increased payment gateway timeout from 5s to 10s per request",
                "Reduced retry attempts from 3 to 2 to prevent cascading timeouts",
                "Implemented circuit breaker pattern to fail fast when gateway is slow",
                "Added monitoring alerts for payment gateway response times",
                "Created fallback to secondary payment gateway when primary is slow"
            ],
            "category": ITIssueCategory.APPLICATION,
            "tags": ["payment", "timeout", "gateway", "production"],
            "ticket_key": "PROJ-1234",
            "source_type": "jira",
        },
        {
            "title": "Database Connection Leak in User Service",
            "phenomenon": "User service experiencing gradual slowdown and eventually crashes. Database connection pool exhausted. Error: Unable to acquire connection from pool.",
            "root_cause_analysis": "The user service was not properly closing database connections in error scenarios. When exceptions occurred during database operations, the connection.close() was not called, leading to connection leaks.",
            "solutions": [
                "Refactored to use try-with-resources pattern for all database connections",
                "Added connection pool monitoring and alerts",
                "Implemented connection leak detection with timeout warnings",
                "Added unit tests to verify connections are closed in all scenarios",
                "Increased connection pool size temporarily while monitoring"
            ],
            "category": ITIssueCategory.APPLICATION,
            "tags": ["database", "connection", "leak", "pool"],
            "ticket_key": "PROJ-1235",
            "source_type": "jira",
        },
    ]
    
    print(f"\nPopulating tenant knowledge base for {tenant_id}...")
    for example in examples:
        entry_id = kb_service.add_tenant_entry(
            tenant_id=tenant_id,
            title=example["title"],
            phenomenon=example["phenomenon"],
            root_cause_analysis=example["root_cause_analysis"],
            solutions=example["solutions"],
            category=example["category"],
            tags=example["tags"],
            ticket_key=example.get("ticket_key"),
            source_type=example.get("source_type", "jira"),
        )
        print(f"  ✓ Added: {example['title']} (ID: {entry_id})")
    
    print(f"\nTenant KB populated with {len(examples)} entries.")


if __name__ == "__main__":
    print("=" * 60)
    print("Populating Knowledge Base with Example Entries")
    print("=" * 60)
    
    populate_common_kb()
    populate_tenant_kb_example("example-tenant-1")
    
    print("\n" + "=" * 60)
    print("Knowledge base population complete!")
    print("=" * 60)
    print("\nYou can now test the system by:")
    print("1. Making a POST request to /analyze with a query")
    print("2. Using the /kb/search endpoint to search the knowledge base")
    print("3. Adding more entries via /kb/common or /kb/tenant/{tenant_id}")

