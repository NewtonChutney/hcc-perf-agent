# CPT metric noise, last 30 days

Generated 2026-11-17 19:13 UTC by `tools/measure_noise.py` from golden PASS/FAIL runs (PR-image runs excluded), groups with >= 5 runs.

`band needed` = 3 x robust CV: the +/- band a robust 3-sigma rule needs for this metric. `near zero` = median is 0, needs an absolute limit.

## Summary per config

| Config | Groups | Metric series | band <= 5% | band 5-10% | band 10-20% | band > 20% | near zero |
|---|---:|---:|---:|---:|---:|---:|---:|
| `advisor/advisor_backend/investigator-conf.yaml` | 1 | 7 | 2 | 1 | 1 | 2 | 1 |
| `ccx/investigator-conf.yaml` | 1 | 3 | 0 | 0 | 0 | 2 | 1 |
| `engine/investigator-conf.yaml` | 1 | 9 | 2 | 2 | 0 | 3 | 2 |
| `hbiperftest/investigator-conf.yaml` | 1 | 24 | 7 | 2 | 4 | 5 | 6 |
| `inventory/investigator-conf.yaml` | 1 | 29 | 8 | 2 | 3 | 12 | 4 |
| `kessel-k6/investigator-conf.yaml` | 12 | 84 | 2 | 24 | 23 | 15 | 20 |
| `playbook-dispatcher/investigator-conf.yaml` | 1 | 3 | 0 | 2 | 1 | 0 | 0 |
| **All** | | **159** | **21** | **33** | **32** | **39** | **34** |

## Configs without enough data

- `chrome/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `compliance/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `content-sources/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `cyndi/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `digital-roadmap/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `dvo/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `front-end/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `hbiperftest/xjoinless/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `ingress/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `inventory/export/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (1 runs, 0 PR runs dropped)
- `inventory/hbi-inventory-views/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (3 runs, 0 PR runs dropped)
- `kessel/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `kessel-migration/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `notifications/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 236 PR runs dropped)
- `patchman/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `rbac/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `receptor/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `remediations/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `ros/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `sources/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `tally/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `tally/metering/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `yupana/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)
- `yuptoo/investigator-conf.yaml`: no comparable group with >= 5 runs in 30 days (0 runs, 0 PR runs dropped)

## Detail

### `advisor/advisor_backend/investigator-conf.yaml` (`insights_perf_index_advisor_backend`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| Insights Advisor Backend perf test | `m.advisor-backend-service.cpu.max` | 5 | 1.274 | 1.4% | 4.1% |
| Insights Advisor Backend perf test | `m.advisor-backend-service.cpu.mean` | 5 | 1.225 | 1.2% | 3.7% |
| Insights Advisor Backend perf test | `m.advisor-backend-service.memory.max` | 5 | 4.632e+08 | 9.2% | 27.5% |
| Insights Advisor Backend perf test | `m.advisor-backend-service.memory.mean` | 5 | 3.976e+08 | 6.3% | 18.9% |
| Insights Advisor Backend perf test | `m.advisor-backend-service.restarts.mean` | 5 | 0 | - | near zero |
| Insights Advisor Backend perf test | `results.created_at.duration_stats.mean` | 5 | 0.1619 | 37.9% | 113.8% |
| Insights Advisor Backend perf test | `results.created_at.rps_stats.mean` | 5 | 33.45 | 2.6% | 7.9% |

### `ccx/investigator-conf.yaml` (`insights_perf_index_ccx`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| CCX memory monitoring test | `m.insights-operator.cpu.mean` | 12 | 0.01878 | 68.1% | 204.3% |
| CCX memory monitoring test | `m.insights-operator.memory.mean` | 12 | 3.445e+08 | 14.3% | 42.8% |
| CCX memory monitoring test | `m.insights-operator.restarts.mean` | 12 | 0 | - | near zero |

### `engine/investigator-conf.yaml` (`insights_perf_index_engine`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| engine CPT test | `m.engine-processor.cpu.max` | 11 | 0.003006 | 38.5% | 115.4% |
| engine CPT test | `m.engine-processor.cpu.mean` | 11 | 0.002545 | 22.7% | 68.2% |
| engine CPT test | `m.engine-processor.memory.max` | 11 | 2.209e+08 | 2.0% | 6.1% |
| engine CPT test | `m.engine-processor.memory.mean` | 11 | 1.776e+08 | 7.6% | 22.7% |
| engine CPT test | `m.engine-processor.restarts.max` | 11 | 0 | - | near zero |
| engine CPT test | `m.engine-processor.restarts.min` | 11 | 0 | - | near zero |
| engine CPT test | `results.created_at.duration_stats.mean` | 11 | 17.21 | 2.9% | 8.6% |
| engine CPT test | `results.created_at.rps_stats.mean` | 11 | 1.289 | 1.3% | 3.9% |
| engine CPT test | `results.kafka.consumed_platform_engine.results` | 11 | 50 | 0.0% | 0.0% |

### `hbiperftest/investigator-conf.yaml` (`insights_perf_index_inventory`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| duration=300 / clients=10 | `m.host-inventory-mq-p1.count_ready.mean` | 5 | 10 | 0.0% | 0.0% |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.cpu.mean` | 5 | 0.02238 | 0.3% | 0.9% |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.memory.mean` | 5 | 2.013e+09 | 0.0% | 0.0% |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.network_drop.mean` | 5 | 0 | - | near zero |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.network_throughput.mean` | 5 | 6.21e+04 | 3.9% | 11.6% |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.restarts.range` | 5 | 0 | - | near zero |
| duration=300 / clients=10 | `m.host-inventory.rds.cpu_utilization.mean` | 5 | 1.014 | 5.2% | 15.7% |
| duration=300 / clients=10 | `m.host-inventory.rds.load_average_minute.mean` | 5 | 0.1579 | 42.3% | 126.8% |
| duration=300 / clients=10 | `m.host-inventory.rds.memory_active.mean` | 5 | 2.628e+07 | 0.8% | 2.4% |
| duration=300 / clients=10 | `m.host-inventory.rds.network_rx.mean` | 5 | 5.174e+05 | 10.8% | 32.4% |
| duration=300 / clients=10 | `m.host-inventory.rds.network_tx.mean` | 5 | 2.654e+06 | 5.0% | 14.9% |
| duration=300 / clients=10 | `m.host-inventory.rds.read_iops.mean` | 5 | 0.2207 | 11.0% | 33.1% |
| duration=300 / clients=10 | `m.host-inventory.rds.temp_bytes.range` | 5 | 0 | - | near zero |
| duration=300 / clients=10 | `m.host-inventory.rds.temp_files.mean` | 5 | 0 | - | near zero |
| duration=300 / clients=10 | `m.host-inventory.rds.tup_fetched.mean` | 5 | 1599 | 17.1% | 51.2% |
| duration=300 / clients=10 | `m.host-inventory.rds.tup_inserted.mean` | 5 | 64.21 | 1.4% | 4.2% |
| duration=300 / clients=10 | `m.host-inventory.rds.tup_updated.mean` | 5 | 42.35 | 15.0% | 45.0% |
| duration=300 / clients=10 | `m.host-inventory.rds.write_iops.mean` | 5 | 205.9 | 4.2% | 12.7% |
| duration=300 / clients=10 | `m.host-inventory.rds.xact_commit.mean` | 5 | 9.436 | 2.4% | 7.2% |
| duration=300 / clients=10 | `avg_content_length` | 5 | 8.761e+04 | 0.0% | 0.0% |
| duration=300 / clients=10 | `fail_ratio` | 5 | 0 | - | near zero |
| duration=300 / clients=10 | `median_response_time` | 5 | 64.34 | 1.5% | 4.6% |
| duration=300 / clients=10 | `num_failures` | 5 | 0 | - | near zero |
| duration=300 / clients=10 | `total_rps` | 5 | 149.6 | 2.7% | 8.0% |

### `inventory/investigator-conf.yaml` (`insights_perf_index_inventory`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.count_ready.mean` | 33 | 1 | 0.0% | 0.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.cpu.mean` | 33 | 0.006063 | 61.4% | 184.2% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.memory.mean` | 33 | 2.095e+08 | 50.5% | 151.6% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.network_drop.mean` | 31 | 0 | - | near zero |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.network_throughput.mean` | 31 | 2.081e+04 | 3.6% | 10.8% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.restarts.range` | 33 | 0 | - | near zero |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.cpu_utilization.mean` | 19 | 0.95 | 31.2% | 93.6% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.load_average_minute.mean` | 19 | 0.17 | 78.5% | 235.5% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.memory_active.mean` | 20 | 2.658e+07 | 1.5% | 4.6% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.network_rx.mean` | 20 | 3500 | 67.9% | 203.6% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.network_tx.mean` | 20 | 1.338e+05 | 34.2% | 102.6% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.read_iops.mean` | 20 | 0.0575 | 135.4% | 406.1% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.temp_bytes.range` | 20 | 0 | - | near zero |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.temp_files.mean` | 20 | 0 | - | near zero |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.tup_fetched.mean` | 20 | 1408 | 16.8% | 50.4% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.tup_inserted.mean` | 20 | 1.258 | 148.3% | 444.8% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.tup_updated.mean` | 20 | 24.02 | 3.2% | 9.6% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.write_iops.mean` | 20 | 182.3 | 6.1% | 18.2% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.xact_commit.mean` | 20 | 7.6 | 2.9% | 8.8% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.events.duration_stats.mean` | 33 | 21.04 | 25.7% | 77.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.events.duration_stats.samples` | 33 | 1000 | 0.0% | 0.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.events.rps_stats.mean` | 33 | 47.78 | 1.5% | 4.4% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.ingress_at.rps_stats.mean` | 33 | 659 | 1.5% | 4.6% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.inventory_db.duration_stats.mean` | 33 | 20.37 | 26.2% | 78.7% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.inventory_db.duration_stats.samples` | 33 | 1000 | 0.0% | 0.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.inventory_db.rps_stats.mean` | 33 | 43.88 | 6.0% | 18.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.kafka.returning_messages.duration_stats.mean` | 33 | 21.04 | 25.7% | 77.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.kafka.returning_messages.duration_stats.samples` | 33 | 1000 | 0.0% | 0.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.kafka.returning_messages.rps_stats.mean` | 33 | 47.78 | 1.5% | 4.4% |

### `kessel-k6/investigator-conf.yaml` (`insights_perf_index_kessel_k6_apis`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `95percentile` | 24 | 1876 | 3.9% | 11.7% |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 24 | 1270 | 2.4% | 7.2% |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 24 | 0 | - | near zero |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `median_response_time` | 24 | 1347 | 2.7% | 8.1% |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `num_failures` | 24 | 0 | - | near zero |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `num_requests` | 24 | 8.158e+04 | 2.5% | 7.4% |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `total_rps` | 24 | 209.2 | 2.5% | 7.4% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `95percentile` | 24 | 718.2 | 6.8% | 20.3% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 24 | 267.3 | 4.4% | 13.2% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 24 | 0 | - | near zero |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `median_response_time` | 24 | 190.5 | 17.1% | 51.2% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `num_failures` | 24 | 0 | - | near zero |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `num_requests` | 24 | 3.871e+05 | 4.5% | 13.4% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `total_rps` | 24 | 992.6 | 4.5% | 13.4% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `95percentile` | 24 | 506.1 | 3.8% | 11.4% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 24 | 293.4 | 7.0% | 21.1% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 24 | 0 | - | near zero |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `median_response_time` | 24 | 299.5 | 8.2% | 24.5% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `num_failures` | 24 | 0 | - | near zero |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `num_requests` | 24 | 3.526e+05 | 7.0% | 21.1% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `total_rps` | 24 | 904.2 | 7.0% | 21.1% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `95percentile` | 24 | 2000 | 3.8% | 11.3% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 24 | 1398 | 3.4% | 10.3% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 24 | 0 | - | near zero |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `median_response_time` | 24 | 1450 | 3.0% | 8.9% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `num_failures` | 24 | 0 | - | near zero |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `num_requests` | 24 | 7.41e+04 | 3.4% | 10.2% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `total_rps` | 24 | 190 | 3.4% | 10.2% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `95percentile` | 26 | 718 | 4.9% | 14.7% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 26 | 268.2 | 5.4% | 16.1% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 26 | 0 | - | near zero |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `median_response_time` | 26 | 197 | 16.4% | 49.1% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `num_failures` | 26 | 0 | - | near zero |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `num_requests` | 26 | 3.859e+05 | 5.2% | 15.5% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `total_rps` | 26 | 989.4 | 5.2% | 15.5% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `95percentile` | 23 | 945.9 | 1.2% | 3.7% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 23 | 116.9 | 7.7% | 23.2% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 23 | 0 | - | near zero |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `median_response_time` | 23 | 5.211 | 9.6% | 28.7% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `num_failures` | 23 | 0 | - | near zero |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `num_requests` | 23 | 8.845e+05 | 7.5% | 22.6% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `total_rps` | 23 | 2268 | 7.5% | 22.6% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `95percentile` | 24 | 495.8 | 2.9% | 8.6% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `avg_response_time` | 24 | 271.9 | 4.1% | 12.2% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `fail_ratio` | 24 | 0 | - | near zero |
| scenario=checkself / transport=http / duration=300 / clients=300 | `median_response_time` | 24 | 278.9 | 4.4% | 13.1% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `num_failures` | 24 | 0 | - | near zero |
| scenario=checkself / transport=http / duration=300 / clients=300 | `num_requests` | 24 | 3.807e+05 | 4.2% | 12.5% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `total_rps` | 24 | 976.1 | 4.2% | 12.5% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `95percentile` | 23 | 501 | 2.5% | 7.6% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `avg_response_time` | 23 | 274.5 | 2.7% | 8.0% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `fail_ratio` | 23 | 0 | - | near zero |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `median_response_time` | 23 | 282.4 | 3.6% | 10.7% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `num_failures` | 23 | 0 | - | near zero |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `num_requests` | 23 | 3.768e+05 | 2.7% | 8.2% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `total_rps` | 23 | 966.1 | 2.7% | 8.2% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `95percentile` | 23 | 68.95 | 5.3% | 15.9% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `avg_response_time` | 23 | 25.58 | 4.8% | 14.4% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `fail_ratio` | 23 | 0.006085 | 27.3% | 81.9% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `median_response_time` | 23 | 17.89 | 4.6% | 13.7% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `num_failures` | 23 | 1217 | 27.3% | 81.9% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `num_requests` | 23 | 2e+05 | 0.0% | 0.0% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `total_rps` | 23 | 777.5 | 5.1% | 15.2% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `95percentile` | 24 | 1024 | 2.7% | 8.0% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `avg_response_time` | 24 | 508.3 | 2.6% | 7.9% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `fail_ratio` | 24 | 0 | - | near zero |
| scenario=objects / transport=stream / duration=300 / clients=300 | `median_response_time` | 24 | 498.5 | 2.7% | 8.1% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `num_failures` | 24 | 0 | - | near zero |
| scenario=objects / transport=stream / duration=300 / clients=300 | `num_requests` | 24 | 2.037e+05 | 2.6% | 7.7% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `total_rps` | 24 | 522.2 | 2.6% | 7.7% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `95percentile` | 23 | 2004 | 1.8% | 5.4% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 23 | 227.3 | 2.5% | 7.6% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 23 | 0.0001365 | 76.3% | 228.8% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `median_response_time` | 23 | 35.56 | 2.0% | 6.1% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `num_failures` | 23 | 62 | 76.5% | 229.6% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `num_requests` | 23 | 4.555e+05 | 2.5% | 7.4% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `total_rps` | 23 | 1168 | 2.5% | 7.4% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `95percentile` | 24 | 372.1 | 2.1% | 6.2% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `avg_response_time` | 24 | 147.7 | 2.5% | 7.5% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `fail_ratio` | 24 | 0 | - | near zero |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `median_response_time` | 24 | 117.8 | 4.1% | 12.2% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `num_failures` | 24 | 0 | - | near zero |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `num_requests` | 24 | 6.986e+05 | 2.5% | 7.4% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `total_rps` | 24 | 1791 | 2.5% | 7.4% |

### `playbook-dispatcher/investigator-conf.yaml` (`insights_perf_index_playbook_dispatcher_consumer`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| Playbook Dispatcher Consumer Load Test | `m.playbook-dispatcher-response-consumer.cpu.mean` | 5 | 0.002705 | 2.6% | 7.8% |
| Playbook Dispatcher Consumer Load Test | `m.playbook-dispatcher-response-consumer.memory.mean` | 5 | 2.631e+07 | 6.5% | 19.4% |
| Playbook Dispatcher Consumer Load Test | `results.updated_at.rps_stats.mean` | 5 | 34.19 | 1.7% | 5.2% |

