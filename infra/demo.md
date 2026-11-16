# Nghiệm thu trên VM chung

| Luồng | Nguồn kiểm | Kết quả |
|---|---|---|
| Windows → Cowrie → Wazuh → Telegram | Ba phiên SSH thật từ Windows trong Host-only | Rule 100110, ba phản hồi ok từ Bot API. Một mã phiên đối chiếu là fb9a4ec7f1e9. |
| Windows → nftables | Một kết nối có kiểm soát tới cổng đóng trên VM | Luật chặn ghi log thật trên ens37 với cổng đích 2223. |
| Bộ gom → Wazuh → Telegram | Bộ gom kiểm bằng log giả lập. Ba bản ghi JSON đã gắn nhãn mẫu đi qua Wazuh và Telegram | Rule 100120, ba phản hồi ok từ Bot API. Mẫu không đại diện cho ba lượt dò quét trực tiếp. |

Thời gian tính từ timestamp sự kiện đến khi Bot API trả ok. SSH thật lần lượt là 2,813 s, 3,331 s và 2,508 s. Bản ghi firewall mẫu là 3,428 s, 3,241 s và 3,449 s. Điểm cuối đo nằm tại Bot API. Có thể đối chiếu ID với `journalctl -t cowrie-telegram` trên VM.

Sau khi siết systemd và bật Telegram, VM đã qua một lượt khởi động lại. Cowrie giành lại listener ở Host-only, egress Internet bị chặn và tài khoản dịch vụ không đọc được bí mật bot. Phiên SSH mới 26693baa3e74 đã đi qua Wazuh và được Bot API chấp nhận. Windows kết nối Host-only cổng 443 thành công, còn cổng 443 và 55000 trên IP NAT không kết nối được. Một lượt kiểm riêng xác nhận tài khoản Cowrie không sửa được rule hay log firewall. Chưa đo ảnh hưởng tốc độ Internet của Windows và chưa lưu ảnh nghiệm thu.
