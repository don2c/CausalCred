# Table 5: Per-operation cost, median [interquartile range] over 100 runs

| Operation | Cost | Peak RSS | Status |
| --- | --- | --- | --- |
| Issue, t_I = 1 | 4.6 [4.4-4.9] ms | 21 MiB | reported_summary |
| Issue, t_I = 3 | 12.1 [11.7-12.8] ms | 26 MiB | reported_summary |
| Attest, t_T = 1 | 5.2 [5.0-5.5] ms | 24 MiB | reported_summary |
| Delegate (one edge) | 1.4 [1.3-1.5] ms | 12 MiB | reported_summary |
| Observe (one event) | 0.42 [0.40-0.45] ms | 38 MiB | reported_summary |
| Head | 0.61 [0.59-0.65] ms | 38 MiB | reported_summary |
| Prove | 8.42 [8.19-8.71] s | 412 MiB | reported_summary |
| Verify | 0.38 [0.37-0.40] s | 96 MiB | reported_summary |
| Revoke (epoch update) | 63 [61-67] ms | 44 MiB | reported_summary |
| Proof size \|π\| | 4.83 MiB |  | reported_summary |
| Statement size \|x\| | 1184 B |  | reported_summary |
| End-to-end action latency | 9.65 s |  | reported_summary |
| Capability profile, b = 16 (amortised) | 0.92 s |  | reported_summary |
