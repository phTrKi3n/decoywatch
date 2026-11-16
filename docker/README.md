# Đóng gói bộ phát hiện & báo cáo SOC trong Docker

Thư mục này đóng gói bộ tương quan firewall ([`firewall.py`](../wazuh/firewall/firewall.py)) và bộ định dạng cảnh báo SOC Telegram ([`custom-cowrie-telegram`](../wazuh/telegram/custom-cowrie-telegram)) vào container hardened chạy không đặc quyền (`UID 10001`), root filesystem chỉ đọc (`read_only: true`), bỏ toàn bộ Linux capabilities (`cap_drop: [ALL]`), `no-new-privileges:true` và không truy cập mạng (`network_mode: "none"`) ở chế độ kiểm chứng cục bộ.

## Chạy kiểm chứng container

```sh
docker compose -f docker/compose.yaml up --build --abort-on-container-exit
```

Container thực hiện:
1. Chạy tự kiểm tra logic đếm cổng phân biệt và cửa sổ 30 giây trong `firewall.py --check`.
2. Kiểm tra `wazuh/fixtures/nftables-block.log` (một block đơn lẻ không kích hoạt ngưỡng `100120`) và mô phỏng chuỗi 5 cổng phân biệt qua `firewall.event()` rồi định dạng thành cảnh báo SOC `100120`.
3. Định dạng toàn bộ 4 rule SOC (`100110`, `100112`, `100115`, `100120`) từ `wazuh/fixtures/telegram-alerts.ndjson` và kiểm chứng ẩn hoàn toàn mật khẩu, lệnh shell thô hay URL tải tệp.
