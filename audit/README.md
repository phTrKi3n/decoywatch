# Kiểm toán bảo mật phòng thủ (`/cloudflare-security-audit-defensive`)

Thư mục này lưu báo cáo kiểm toán mã nguồn và cấu hình theo chuẩn schema của `cloudflare-security-audit-defensive`:

- [`findings.json`](findings.json): Danh sách phát hiện bảo mật (đã xác nhận và khắc phục trực tiếp trong repo).
- [`coverage-ledger.json`](coverage-ledger.json): Sổ cái bao phủ kiểm toán theo từng ranh giới bảo mật (`cowrie-systemd`, `infra-nftables`, `wazuh-firewall`, `wazuh-telegram`).

## Tóm tắt phát hiện và khắc phục

1. **`wazuh-firewall-service-missing-systemd-sandboxing`** (`medium`, đã khắc phục): Unit [`cowrie-firewall-events.service`](../wazuh/firewall/cowrie-firewall-events.service) trước đó thiếu `ProtectSystem=strict`, `PrivateNetwork=true`, `RestrictAddressFamilies=AF_UNIX`, `CapabilityBoundingSet=` và `ReadWritePaths=/var/log/cowrie-lab`. Đã bổ sung đầy đủ chỉ thị cô lập.
2. **`wazuh-telegram-ip-type-confusion`** (`low`, đã khắc phục): [`custom-cowrie-telegram`](../wazuh/telegram/custom-cowrie-telegram) trước đó gọi trực tiếp `ipaddress.ip_address(...)` nên chấp nhận `bool` (`True` → `0.0.0.1`) và `int`. Đã thay bằng `parse_ip()` kiểm tra `isinstance(value, str)` và kiểm kiểu chặt chẽ cho `rule.level`, `port_count`, `timestamp`, `session`.

## Lệnh kiểm định trong Docker (cô lập mạng, chỉ đọc)

Chạy từ thư mục gốc repo trên PowerShell:

```powershell
$skillDir = Join-Path $env:USERPROFILE '.gemini\config\plugins\shared-workflow-tools\skills\cloudflare-security-audit-defensive'
$reportDir = Join-Path (Get-Location).Path 'audit'
docker run --rm --network none --read-only --mount "type=bind,source=$skillDir,target=/skill,readonly" --mount "type=bind,source=$reportDir,target=/report,readonly" node:22-bookworm-slim node /skill/validate-findings.cjs /report/findings.json
docker run --rm --network none --read-only --mount "type=bind,source=$skillDir,target=/skill,readonly" --mount "type=bind,source=$reportDir,target=/report,readonly" node:22-bookworm-slim node /skill/validate-coverage-ledger.cjs /report/coverage-ledger.json
```
