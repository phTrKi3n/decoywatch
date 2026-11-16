# Cowrie Honeypot Lab | Wazuh SIEM & Telegram Alerts

**Tên đồ án** — Triển khai hệ thống bẫy Honeypot thế hệ mới kết hợp Wazuh SIEM & cảnh báo tấn công Real-time qua Telegram.

Đồ án An toàn mạng của nhóm ba người. Một VM Ubuntu trên VMware Workstation chạy firewall máy chủ, Cowrie và Wazuh. Windows kết nối qua WAN mô phỏng Host-only. VM dùng VMware NAT để gửi cảnh báo Telegram.

## Kết quả cần trình bày

- Từ máy khách trong lab, thực hiện một phiên SSH đã định trước với tài khoản thử nghiệm. Chỉ ra log Cowrie, cảnh báo Wazuh và tin nhắn Telegram của cùng phiên.
- Xác minh firewall ghi nhận kết nối thử bị chặn trên Host-only. Dùng log mẫu để kiểm tương quan nhiều cổng, rồi đối chiếu cảnh báo Wazuh với Telegram.
- Đo độ trễ từ sự kiện đủ điều kiện đến phản hồi thành công của Telegram Bot API. Kiểm VM ra Internet qua NAT và Cowrie bị giới hạn quyền.

## Dựng lab và nghiệm thu

1. [VMware và nftables](infra/README.md)
2. [Cowrie SSH](cowrie/README.md)
3. [Wazuh và tương quan firewall](wazuh/README.md)
4. [Cảnh báo Telegram](wazuh/telegram/README.md)
5. [Kết quả nghiệm thu trên VM chung](infra/demo.md)
6. [Đóng gói Docker](docker/README.md)
7. [Kiểm toán bảo mật](audit/README.md)
8. [Giao diện Web Enterprise SOC](ui/README.md)

## Bắt đầu

- **Cả nhóm** đọc [kế hoạch triển khai](docs/superpowers/plans/2026-11-12-honeypot-wazuh-telegram.md) để xem phân công, cấu hình mạng, các điểm bàn giao và cách nghiệm thu.
- **Khi làm việc chung** đọc [quy trình Git](CONTRIBUTING.md) để tạo nhánh, viết commit, mở PR và hoàn tác khi cần.
- **Agent** đọc [AGENTS.md](AGENTS.md) trước khi chỉnh file. Nếu công cụ không tự nạp file này, người giao việc có thể dùng lời nhắc bên dưới.

```text
Đọc AGENTS.md ở gốc repo và kế hoạch được liên kết trong file đó.
Bạn làm task <mã task> cho <tên thành viên>. Bắt đầu từ <nhánh/commit được bàn giao>.
Đối chiếu nhiệm vụ trên GitHub Issue hoặc dùng thông tin tôi cung cấp nếu bạn chưa có quyền truy cập.
Chỉ sửa các đường dẫn của task. Kiểm tra và đưa diff, bằng chứng, bước còn lại để tôi review.
```
