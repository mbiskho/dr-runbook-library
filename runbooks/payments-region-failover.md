---
service: payments-api
scenario: Primary region unavailable
tier: 1
rto: 1h
owner: payments-oncall
last_tested: 2026-09-14
---
## When to use
The primary region (ap-southeast-1) is unavailable or degraded beyond the payments SLO for more than 15 minutes, and the cloud provider has not given a recovery time under 30 minutes.

## Decision
The incident commander decides, with the Head of Payments. State the expected data loss before deciding: check the replica lag in step 1. Failing over with high lag means losing those transactions, and they'll need reconciliation afterwards.

## Steps
1. Check replication lag on the secondary (ap-southeast-3) Aurora cluster: `aws rds describe-global-clusters --global-cluster-identifier payments-global`.
   Expect: secondary listed with `IsWriter: false`; note the replication lag in the incident channel.
2. Freeze deploys: `gh workflow disable deploy.yml`.
   Expect: the workflow shows as disabled.
3. Promote the secondary: `aws rds failover-global-cluster --global-cluster-identifier payments-global --target-db-cluster-identifier arn:...:payments-apse3 --allow-data-loss`.
   Expect: within ~2 minutes the apse3 cluster reports `IsWriter: true`.
4. Scale the secondary-region application to production size: `kubectl --context apse3 scale deploy/payments-api --replicas=12`.
   Expect: 12/12 pods Ready.
5. Shift traffic: set the Route 53 failover record's primary health check to failed (`scripts/force-failover.sh payments`).
   Expect: `dig api.example.com` returns the apse3 load balancer within the 60 s TTL.

## Verify
- Payments success rate back above 98% on the dashboard.
- A test transaction from the synthetic monitor succeeds end to end.
- Post in the incident channel: time of promotion, estimated transactions lost (from the lag), next update time.

## Rollback
Before writes reach the promoted cluster (step 3 not yet run): revert step 5 and scale apse3 back down. After promotion, do **not** fail back during the incident. Failback is a planned change once the primary region is stable (see `payments-region-failback.md`).
