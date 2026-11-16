# Graph Report - honeypot-wazuh-telegram  (2026-11-16)

## Corpus Check
- Corpus is ~13,631 words - fits in a single context window. You may not need a graph.

## Summary
- 101 nodes · 183 edges · 7 communities (4 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `08fa770`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Lab Isolation, Audit & SOC Console
- Docker Compose Hardening Spec
- Container Detector Self-Test Runner
- Telegram Tests & Data Minimization
- Firewall Port-Scan Correlator
- Netplan Host-Only NIC Config

## God Nodes (most connected - your core abstractions)
1. `soc-detector` - 11 edges
2. `TelegramTests` - 9 edges
3. `Project Overview (README.md)` - 8 edges
4. `Cowrie 3.1.6 SSH Trap (192.168.100.20:2222, Telnet Off, UID 999)` - 8 edges
5. `run_self_test()` - 7 edges
6. `E2E Verification & Acceptance Log (infra/demo.md)` - 7 edges
7. `Wazuh Detection Rules 100110-100120 (Login, Brute 100112, Post-Exploit 100115, Scan 100120)` - 7 edges
8. `Zero-CDN Framed Enterprise SOC Console (ui/index.html)` - 7 edges
9. `ens37` - 6 edges
10. `event()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Dual-NIC Boundary: VMnet1 Host-only (ens37 192.168.100.20) vs VMnet8 NAT (ens33)` --complements--> `Wazuh API (127.0.0.1:55000) & Indexer Localhost Binding`  [INFERRED]
  infra/README.md → wazuh/README.md
- `Zero-CDN Framed Enterprise SOC Console (ui/index.html)` --displays_posture_of--> `Container Hardening: UID 10001, read_only, cap_drop ALL, network_mode none`  [INFERRED]
  ui/index.html → docker/README.md
- `Container Hardening: UID 10001, read_only, cap_drop ALL, network_mode none` --enforced_by--> `user`  [EXTRACTED]
  docker/README.md → docker/compose.yaml
- `Container Hardening: UID 10001, read_only, cap_drop ALL, network_mode none` --enforced_by--> `read_only`  [EXTRACTED]
  docker/README.md → docker/compose.yaml
- `Container Hardening: UID 10001, read_only, cap_drop ALL, network_mode none` --enforced_by--> `cap_drop`  [EXTRACTED]
  docker/README.md → docker/compose.yaml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Verification & Security Assurance Suite** — concept_audit_findings, concept_audit_coverage_ledger, wazuh_telegram_test_telegram, docker_entrypoint_run_self_test, doc_infra_demo [EXTRACTED 1.00]
- **End-to-End Defense Pipeline (Cowrie -> Wazuh -> Telegram -> SOC UI)** — concept_cowrie_ssh_trap, wazuh_firewall_firewall, concept_wazuh_rules_suite, wazuh_telegram_custom_cowrie_telegram, concept_soc_console_ui [EXTRACTED 1.00]
- **Defense-in-Depth Isolation Layer (NICs + nftables + Systemd + Localhost Bind)** — concept_hostonly_nat_boundary, concept_nftables_egress_drop, rationale_cowrie_systemd_hardening, concept_wazuh_localhost_bind, rationale_docker_hardening [EXTRACTED 1.00]

## Communities (7 total, 3 thin omitted)

### Community 0 - "Lab Isolation, Audit & SOC Console"
Cohesion: 0.14
Nodes (22): Cloudflare Coverage Ledger (4 Audited Lab Units), Validated Security Findings (Systemd Sandboxing & Strict IPv4/v6 Validation Fixed), Cowrie 3.1.6 SSH Trap (192.168.100.20:2222, Telnet Off, UID 999), Host Benchmark VM ON vs OFF (2.45 vs 6.79 GiB Free RAM, ~22ms HTTPS Delta), Dual-NIC Boundary: VMnet1 Host-only (ens37 192.168.100.20) vs VMnet8 NAT (ens33), nftables Inbound/Forward Drop & UID 999 Egress Drop (LAB_WAN_BLOCK), Zero-CDN Framed Enterprise SOC Console (ui/index.html), Interactive Incident Explorer & Telegram HTML Preview (INCIDENTS / buildPreText) (+14 more)

### Community 1 - "Docker Compose Hardening Spec"
Cohesion: 0.15
Nodes (15): Hardened Offline SOC Detector Container Docs (docker/README.md), context, dockerfile, services, soc-detector, build, cap_drop, command (+7 more)

### Community 2 - "Container Detector Self-Test Runner"
Cohesion: 0.18
Nodes (3): load_firewall(), main(), run_self_test()

### Community 6 - "Netplan Host-Only NIC Config"
Cohesion: 0.25
Nodes (7): accept-ra, dhcp4, dhcp6, ens37, network, ethernets, version

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Container Hardening: UID 10001, read_only, cap_drop ALL, network_mode none` connect `Docker Compose Hardening Spec` to `Lab Isolation, Audit & SOC Console`?**
  _High betweenness centrality (0.219) - this node is a cross-community bridge._
- **Should `Lab Isolation, Audit & SOC Console` be split into smaller, more focused modules?**
  _Cohesion score 0.13666666666666666 - nodes in this community are weakly interconnected._
- **Why does `E2E Verification & Acceptance Log (infra/demo.md)` connect `Lab Isolation, Audit & SOC Console` to `Telegram Bot Alert Formatter`, `Firewall Port-Scan Correlator`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Should `Docker Compose Hardening Spec` be split into smaller, more focused modules?**
  _Cohesion score 0.14705882352941177 - nodes in this community are weakly interconnected._