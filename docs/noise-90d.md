# CPT metric noise, last 90 days

Generated 2026-11-17 19:14 UTC by `tools/measure_noise.py` from golden PASS/FAIL runs (PR-image runs excluded), groups with >= 5 runs.

`band needed` = 3 x robust CV: the +/- band a robust 3-sigma rule needs for this metric. `near zero` = median is 0, needs an absolute limit.

## Summary per config

| Config | Groups | Metric series | band <= 5% | band 5-10% | band 10-20% | band > 20% | near zero |
|---|---:|---:|---:|---:|---:|---:|---:|
| `advisor/advisor_backend/investigator-conf.yaml` | 1 | 7 | 0 | 0 | 2 | 4 | 1 |
| `ccx/investigator-conf.yaml` | 1 | 3 | 0 | 0 | 0 | 2 | 1 |
| `engine/investigator-conf.yaml` | 1 | 9 | 1 | 1 | 1 | 4 | 2 |
| `hbiperftest/investigator-conf.yaml` | 1 | 24 | 2 | 1 | 3 | 12 | 6 |
| `inventory/export/investigator-conf.yaml` | 1 | 6 | 0 | 1 | 1 | 4 | 0 |
| `inventory/hbi-inventory-views/investigator-conf.yaml` | 1 | 11 | 4 | 0 | 1 | 4 | 2 |
| `inventory/investigator-conf.yaml` | 1 | 29 | 4 | 0 | 2 | 18 | 5 |
| `kessel-k6/investigator-conf.yaml` | 12 | 84 | 1 | 3 | 30 | 30 | 20 |
| `playbook-dispatcher/investigator-conf.yaml` | 1 | 3 | 0 | 1 | 1 | 1 | 0 |
| **All** | | **176** | **12** | **7** | **41** | **79** | **37** |

## Configs without enough data

- `chrome/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `compliance/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `content-sources/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `cyndi/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `digital-roadmap/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `dvo/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `front-end/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `hbiperftest/xjoinless/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `ingress/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `kessel/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 2 PR runs dropped)
- `kessel-migration/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `notifications/investigator-conf.yaml`: 16 runs, but no `sets` metric has >= 5 numeric values (461 PR runs dropped)
- `patchman/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `rbac/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `receptor/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `remediations/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `ros/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `sources/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `tally/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `tally/metering/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `yupana/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)
- `yuptoo/investigator-conf.yaml`: no comparable group with >= 5 runs in 90 days (0 runs, 0 PR runs dropped)

## Detail

### `advisor/advisor_backend/investigator-conf.yaml` (`insights_perf_index_advisor_backend`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| Insights Advisor Backend perf test | `m.advisor-backend-service.cpu.max` | 82 | 1.265 | 4.4% | 13.1% |
| Insights Advisor Backend perf test | `m.advisor-backend-service.cpu.mean` | 82 | 1.227 | 4.0% | 11.9% |
| Insights Advisor Backend perf test | `m.advisor-backend-service.memory.max` | 82 | 4.808e+08 | 15.6% | 46.7% |
| Insights Advisor Backend perf test | `m.advisor-backend-service.memory.mean` | 82 | 4.021e+08 | 13.7% | 41.2% |
| Insights Advisor Backend perf test | `m.advisor-backend-service.restarts.mean` | 82 | 0 | - | near zero |
| Insights Advisor Backend perf test | `results.created_at.duration_stats.mean` | 76 | 0.09637 | 106.4% | 319.2% |
| Insights Advisor Backend perf test | `results.created_at.rps_stats.mean` | 76 | 32.26 | 26.5% | 79.4% |

### `ccx/investigator-conf.yaml` (`insights_perf_index_ccx`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| CCX memory monitoring test | `m.insights-operator.cpu.mean` | 41 | 0.01656 | 56.9% | 170.6% |
| CCX memory monitoring test | `m.insights-operator.memory.mean` | 41 | 4.016e+08 | 33.6% | 100.7% |
| CCX memory monitoring test | `m.insights-operator.restarts.mean` | 41 | 0 | - | near zero |

### `engine/investigator-conf.yaml` (`insights_perf_index_engine`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| engine CPT test | `m.engine-processor.cpu.max` | 28 | 0.002462 | 9.9% | 29.8% |
| engine CPT test | `m.engine-processor.cpu.mean` | 28 | 0.002412 | 10.8% | 32.3% |
| engine CPT test | `m.engine-processor.memory.max` | 28 | 2.203e+08 | 15.8% | 47.5% |
| engine CPT test | `m.engine-processor.memory.mean` | 28 | 1.791e+08 | 14.4% | 43.1% |
| engine CPT test | `m.engine-processor.restarts.max` | 28 | 0 | - | near zero |
| engine CPT test | `m.engine-processor.restarts.min` | 28 | 0 | - | near zero |
| engine CPT test | `results.created_at.duration_stats.mean` | 28 | 17.03 | 3.5% | 10.4% |
| engine CPT test | `results.created_at.rps_stats.mean` | 28 | 1.302 | 2.8% | 8.3% |
| engine CPT test | `results.kafka.consumed_platform_engine.results` | 28 | 50 | 0.0% | 0.0% |

### `hbiperftest/investigator-conf.yaml` (`insights_perf_index_inventory`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| duration=300 / clients=10 | `m.host-inventory-mq-p1.count_ready.mean` | 134 | 1 | 0.0% | 0.0% |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.cpu.mean` | 134 | 0.003077 | 4.0% | 11.9% |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.memory.mean` | 134 | 2.114e+08 | 3.2% | 9.7% |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.network_drop.mean` | 134 | 0 | - | near zero |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.network_throughput.mean` | 134 | 1.524e+04 | 6.7% | 20.2% |
| duration=300 / clients=10 | `m.host-inventory-mq-p1.restarts.range` | 134 | 0 | - | near zero |
| duration=300 / clients=10 | `m.host-inventory.rds.cpu_utilization.mean` | 51 | 0.4083 | 13.4% | 40.2% |
| duration=300 / clients=10 | `m.host-inventory.rds.load_average_minute.mean` | 51 | 0.138 | 48.9% | 146.6% |
| duration=300 / clients=10 | `m.host-inventory.rds.memory_active.mean` | 51 | 5.458e+07 | 4.6% | 13.7% |
| duration=300 / clients=10 | `m.host-inventory.rds.network_rx.mean` | 51 | 2.753e+05 | 29.3% | 87.8% |
| duration=300 / clients=10 | `m.host-inventory.rds.network_tx.mean` | 51 | 4.04e+05 | 19.7% | 59.2% |
| duration=300 / clients=10 | `m.host-inventory.rds.read_iops.mean` | 51 | 0.047 | 34.5% | 103.5% |
| duration=300 / clients=10 | `m.host-inventory.rds.temp_bytes.range` | 51 | 0 | - | near zero |
| duration=300 / clients=10 | `m.host-inventory.rds.temp_files.mean` | 51 | 0 | - | near zero |
| duration=300 / clients=10 | `m.host-inventory.rds.tup_fetched.mean` | 51 | 1342 | 27.8% | 83.3% |
| duration=300 / clients=10 | `m.host-inventory.rds.tup_inserted.mean` | 51 | 70.29 | 19.3% | 58.0% |
| duration=300 / clients=10 | `m.host-inventory.rds.tup_updated.mean` | 51 | 13.65 | 23.8% | 71.5% |
| duration=300 / clients=10 | `m.host-inventory.rds.write_iops.mean` | 51 | 140.1 | 53.5% | 160.6% |
| duration=300 / clients=10 | `m.host-inventory.rds.xact_commit.mean` | 51 | 8.55 | 3.7% | 11.1% |
| duration=300 / clients=10 | `avg_content_length` | 134 | 57 | 0.0% | 0.0% |
| duration=300 / clients=10 | `fail_ratio` | 134 | 0 | - | near zero |
| duration=300 / clients=10 | `median_response_time` | 134 | 76.67 | 12.9% | 38.6% |
| duration=300 / clients=10 | `num_failures` | 134 | 0 | - | near zero |
| duration=300 / clients=10 | `total_rps` | 134 | 132.7 | 7.4% | 22.3% |

### `inventory/export/investigator-conf.yaml` (`insights_perf_index_export_inventory`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| Insights Inventory Export perf test | `m.export-service-service.cpu.mean` | 45 | 0.00641 | 4.2% | 12.6% |
| Insights Inventory Export perf test | `m.export-service-service.memory.mean` | 45 | 9.839e+07 | 14.7% | 44.2% |
| Insights Inventory Export perf test | `m.host-inventory-export-service.cpu.mean` | 45 | 0.005239 | 7.5% | 22.4% |
| Insights Inventory Export perf test | `m.host-inventory-export-service.memory.mean` | 45 | 3.333e+08 | 2.3% | 6.8% |
| Insights Inventory Export perf test | `results.done_at.duration_stats.mean` | 45 | 0.9014 | 15.3% | 45.9% |
| Insights Inventory Export perf test | `results.done_at.rps_stats.mean` | 45 | 4.745 | 14.8% | 44.5% |

### `inventory/hbi-inventory-views/investigator-conf.yaml` (`insights_perf_index_inventory`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| duration=300 / clients=10 | `m.host-inventory-service.count_ready.mean` | 15 | 5 | 0.0% | 0.0% |
| duration=300 / clients=10 | `m.host-inventory-service.cpu.mean` | 15 | 0.009017 | 16.0% | 48.0% |
| duration=300 / clients=10 | `m.host-inventory-service.memory.mean` | 15 | 1.748e+07 | 6.3% | 18.8% |
| duration=300 / clients=10 | `m.host-inventory.rds.cpu_utilization.mean` | 18 | 0.4 | 10.8% | 32.4% |
| duration=300 / clients=10 | `m.host-inventory.rds.read_iops.mean` | 18 | 0.04452 | 48.3% | 145.0% |
| duration=300 / clients=10 | `m.host-inventory.rds.write_iops.mean` | 18 | 118.1 | 9.6% | 28.7% |
| duration=300 / clients=10 | `avg_content_length` | 18 | 1.343e+05 | 0.8% | 2.5% |
| duration=300 / clients=10 | `fail_ratio` | 18 | 0 | - | near zero |
| duration=300 / clients=10 | `median_response_time` | 18 | 110 | 0.0% | 0.0% |
| duration=300 / clients=10 | `num_failures` | 18 | 0 | - | near zero |
| duration=300 / clients=10 | `total_rps` | 18 | 79.38 | 1.2% | 3.7% |

### `inventory/investigator-conf.yaml` (`insights_perf_index_inventory`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.count_ready.mean` | 76 | 5 | 44.5% | 133.4% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.cpu.mean` | 77 | 0.01194 | 53.8% | 161.5% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.memory.mean` | 77 | 7.502e+08 | 46.8% | 140.5% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.network_drop.mean` | 72 | 0 | - | near zero |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.network_throughput.mean` | 72 | 2.134e+04 | 53.6% | 160.7% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory-mq-pmin.restarts.range` | 65 | 0 | - | near zero |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.cpu_utilization.mean` | 40 | 0.7 | 42.4% | 127.1% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.load_average_minute.mean` | 40 | 0.17 | 58.9% | 176.6% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.memory_active.mean` | 41 | 5.255e+07 | 15.3% | 45.9% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.network_rx.mean` | 43 | 5415 | 114.8% | 344.5% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.network_tx.mean` | 43 | 1.179e+05 | 55.4% | 166.2% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.read_iops.mean` | 43 | 0.065 | 125.5% | 376.4% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.temp_bytes.range` | 45 | 0 | - | near zero |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.temp_files.mean` | 45 | 0 | - | near zero |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.tup_fetched.mean` | 43 | 1374 | 28.7% | 86.2% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.tup_inserted.mean` | 43 | 0 | - | near zero |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.tup_updated.mean` | 43 | 23.5 | 4.0% | 12.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.write_iops.mean` | 43 | 182.1 | 14.9% | 44.7% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `m.host-inventory.rds.xact_commit.mean` | 43 | 7.583 | 3.6% | 10.8% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.events.duration_stats.mean` | 77 | 14.09 | 85.0% | 255.1% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.events.duration_stats.samples` | 77 | 1000 | 0.0% | 0.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.events.rps_stats.mean` | 77 | 88.51 | 67.8% | 203.4% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.ingress_at.rps_stats.mean` | 77 | 658.8 | 1.6% | 4.8% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.inventory_db.duration_stats.mean` | 77 | 13.41 | 89.5% | 268.5% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.inventory_db.duration_stats.samples` | 77 | 1000 | 0.0% | 0.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.inventory_db.rps_stats.mean` | 77 | 69.76 | 59.1% | 177.3% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.kafka.returning_messages.duration_stats.mean` | 77 | 14.09 | 85.0% | 255.1% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.kafka.returning_messages.duration_stats.samples` | 77 | 1000 | 0.0% | 0.0% |
| Insights Inventory with RHSM Conduit messages perf test, new hosts | `results.kafka.returning_messages.rps_stats.mean` | 77 | 88.51 | 67.8% | 203.4% |

### `kessel-k6/investigator-conf.yaml` (`insights_perf_index_kessel_k6_apis`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `95percentile` | 170 | 2013 | 7.9% | 23.6% |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 170 | 1354 | 7.0% | 21.0% |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 170 | 0 | - | near zero |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `median_response_time` | 170 | 1434 | 6.8% | 20.3% |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `num_failures` | 170 | 0 | - | near zero |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `num_requests` | 170 | 7.651e+04 | 7.1% | 21.2% |
| scenario=check_bulk / transport=grpc / duration=300 / clients=300 | `total_rps` | 170 | 196.2 | 7.1% | 21.2% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `95percentile` | 170 | 688 | 8.8% | 26.4% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 170 | 281.5 | 5.2% | 15.7% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 170 | 0 | - | near zero |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `median_response_time` | 170 | 239.7 | 18.2% | 54.7% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `num_failures` | 170 | 0 | - | near zero |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `num_requests` | 170 | 3.677e+05 | 5.1% | 15.4% |
| scenario=check_delete / transport=grpc / duration=300 / clients=300 | `total_rps` | 170 | 942.7 | 5.1% | 15.4% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `95percentile` | 169 | 528.1 | 5.8% | 17.5% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 169 | 301.9 | 7.3% | 21.9% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 169 | 0 | - | near zero |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `median_response_time` | 169 | 306.7 | 7.9% | 23.8% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `num_failures` | 169 | 0 | - | near zero |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `num_requests` | 169 | 3.427e+05 | 7.0% | 21.1% |
| scenario=check_for_update / transport=grpc / duration=300 / clients=300 | `total_rps` | 169 | 878.8 | 7.0% | 21.1% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `95percentile` | 168 | 2116 | 5.7% | 17.0% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 168 | 1455 | 4.9% | 14.6% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 168 | 0 | - | near zero |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `median_response_time` | 168 | 1511 | 4.9% | 14.6% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `num_failures` | 168 | 0 | - | near zero |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `num_requests` | 168 | 7.119e+04 | 5.0% | 15.0% |
| scenario=check_for_update_bulk / transport=grpc / duration=300 / clients=300 | `total_rps` | 168 | 182.5 | 5.0% | 15.0% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `95percentile` | 171 | 683.8 | 8.7% | 26.1% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 171 | 280.7 | 5.6% | 16.9% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 171 | 0 | - | near zero |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `median_response_time` | 171 | 233.3 | 21.4% | 64.2% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `num_failures` | 171 | 0 | - | near zero |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `num_requests` | 171 | 3.687e+05 | 5.9% | 17.6% |
| scenario=check_view / transport=grpc / duration=300 / clients=300 | `total_rps` | 171 | 945.3 | 5.9% | 17.6% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `95percentile` | 290 | 911.7 | 5.0% | 15.0% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 290 | 122.6 | 11.0% | 32.9% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 290 | 0 | - | near zero |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `median_response_time` | 290 | 5.925 | 15.0% | 44.9% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `num_failures` | 290 | 0 | - | near zero |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `num_requests` | 290 | 8.435e+05 | 10.6% | 31.8% |
| scenario=check_workspace / transport=grpc / duration=300 / clients=300 | `total_rps` | 290 | 2163 | 10.6% | 31.8% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `95percentile` | 170 | 517.6 | 5.0% | 14.9% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `avg_response_time` | 170 | 283.1 | 5.0% | 15.1% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `fail_ratio` | 170 | 0 | - | near zero |
| scenario=checkself / transport=http / duration=300 / clients=300 | `median_response_time` | 170 | 288.2 | 4.8% | 14.5% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `num_failures` | 170 | 0 | - | near zero |
| scenario=checkself / transport=http / duration=300 / clients=300 | `num_requests` | 170 | 3.655e+05 | 5.1% | 15.3% |
| scenario=checkself / transport=http / duration=300 / clients=300 | `total_rps` | 170 | 937.3 | 5.1% | 15.3% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `95percentile` | 166 | 535.1 | 5.6% | 16.9% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `avg_response_time` | 166 | 296.4 | 6.2% | 18.5% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `fail_ratio` | 166 | 0 | - | near zero |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `median_response_time` | 166 | 303.1 | 6.3% | 19.0% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `num_failures` | 166 | 0 | - | near zero |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `num_requests` | 166 | 3.491e+05 | 6.2% | 18.7% |
| scenario=checkselfbulk / transport=http / duration=300 / clients=300 | `total_rps` | 166 | 895.1 | 6.2% | 18.7% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `95percentile` | 166 | 64.96 | 8.2% | 24.7% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `avg_response_time` | 166 | 23.76 | 8.3% | 24.9% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `fail_ratio` | 166 | 0.002917 | 72.2% | 216.5% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `median_response_time` | 166 | 16.13 | 8.6% | 25.9% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `num_failures` | 166 | 583.5 | 72.2% | 216.5% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `num_requests` | 166 | 2e+05 | 0.0% | 0.0% |
| scenario=delete_resource / transport=grpc / duration=300 / clients=20 | `total_rps` | 166 | 837 | 8.4% | 25.2% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `95percentile` | 163 | 1014 | 2.9% | 8.7% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `avg_response_time` | 163 | 513.1 | 2.9% | 8.6% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `fail_ratio` | 163 | 0 | - | near zero |
| scenario=objects / transport=stream / duration=300 / clients=300 | `median_response_time` | 163 | 504.9 | 3.3% | 10.0% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `num_failures` | 163 | 0 | - | near zero |
| scenario=objects / transport=stream / duration=300 / clients=300 | `num_requests` | 163 | 1.991e+05 | 4.8% | 14.3% |
| scenario=objects / transport=stream / duration=300 / clients=300 | `total_rps` | 163 | 510.6 | 4.8% | 14.3% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `95percentile` | 168 | 1923 | 6.8% | 20.4% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `avg_response_time` | 168 | 219 | 6.5% | 19.5% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `fail_ratio` | 168 | 0.0002385 | 128.5% | 385.4% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `median_response_time` | 168 | 33.63 | 8.9% | 26.8% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `num_failures` | 168 | 119 | 122.1% | 366.3% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `num_requests` | 168 | 4.728e+05 | 6.5% | 19.4% |
| scenario=report_resource / transport=grpc / duration=300 / clients=300 | `total_rps` | 168 | 1212 | 6.5% | 19.4% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `95percentile` | 169 | 396.7 | 4.8% | 14.5% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `avg_response_time` | 169 | 159.6 | 6.0% | 18.0% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `fail_ratio` | 169 | 0 | - | near zero |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `median_response_time` | 169 | 128.2 | 8.2% | 24.5% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `num_failures` | 169 | 0 | - | near zero |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `num_requests` | 169 | 6.439e+05 | 7.2% | 21.5% |
| scenario=subjects / transport=stream / duration=300 / clients=300 | `total_rps` | 169 | 1649 | 7.3% | 22.0% |

### `playbook-dispatcher/investigator-conf.yaml` (`insights_perf_index_playbook_dispatcher_consumer`)

| Group | Metric | Runs | Median | Robust CV | Band needed |
|---|---|---:|---:|---:|---:|
| Playbook Dispatcher Consumer Load Test | `m.playbook-dispatcher-response-consumer.cpu.mean` | 36 | 0.002611 | 5.0% | 14.9% |
| Playbook Dispatcher Consumer Load Test | `m.playbook-dispatcher-response-consumer.memory.mean` | 36 | 2.734e+07 | 14.0% | 42.1% |
| Playbook Dispatcher Consumer Load Test | `results.updated_at.rps_stats.mean` | 36 | 34.4 | 2.5% | 7.6% |

