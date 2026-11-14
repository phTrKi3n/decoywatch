# W02 – Telegram

Wazuh Integrator chạy script Python 3 khi rule `100110` hoặc `100120` phát cảnh báo. Script gửi văn bản qua Telegram Bot API, dùng trường đã xác thực và giới hạn cho từng rule. Tin firewall tổng hợp có nhãn `[MẪU KIỂM THỬ]`. Telegram chỉ dùng để nhận cảnh báo.

## Kiểm trước khi áp

Từ repo, chạy `python3 wazuh/telegram/test_telegram.py`. Bộ kiểm dùng dữ liệu mẫu và phản hồi API giả lập. Hợp đồng đầu vào của W01 nằm trong `wazuh/fixtures/telegram-alerts.ndjson` trên bản W01 đã bàn giao.

## Bật trên VM

Từ gốc repo trên Ubuntu:

```sh
sudo install -o root -g wazuh -m 0750 wazuh/telegram/custom-cowrie-telegram /var/ossec/integrations/custom-cowrie-telegram
sudo install -o root -g wazuh -m 0640 /duong-dan-ngoai-repo/telegram-bot.local.json /var/ossec/etc/cowrie-telegram.json
sudo cp -an /var/ossec/etc/ossec.conf /var/ossec/etc/ossec.conf.before-telegram
```

File JSON thật theo `config.example.json`, chứa token của bot và ID chat đã mở bằng Start. Điền trên bản cục bộ ngoài Git. Nếu VM đã cấu hình, dùng tiếp file hiện có. Giữ quyền `0640 root:wazuh` và kiểm tài khoản Cowrie không đọc được.

Chép khối `integration` từ `integration.xml` vào một khối `ossec_config` hiện có trong `/var/ossec/etc/ossec.conf`. Nếu đã cấu hình `custom-cowrie-telegram`, giữ một khối duy nhất. Sau đó:

```sh
sudo /var/ossec/bin/wazuh-integratord -t
sudo systemctl restart wazuh-manager
sudo /var/ossec/bin/wazuh-control status
sudo journalctl -t cowrie-telegram -o cat
```

Thực hiện một phiên SSH đã định trước tới Cowrie và dùng fixture được đánh dấu cho phần firewall. So mã phiên hoặc ID trong log Wazuh với nhật ký Telegram. Mỗi lượt thành công ghi ID, UTC gọi API, UTC nhận phản hồi `ok` và thời gian gọi API đo bằng đồng hồ đơn điệu. Khi lỗi, nhật ký chỉ ghi loại lỗi. Đối chiếu tin thực tế trong chat demo.

Nếu phải hoàn tác, khôi phục script và `ossec.conf` từ bản sao trước thay đổi, kiểm cấu hình rồi khởi động lại Manager. Giữ token ngoài repo và ngoài ảnh báo cáo.

## Bàn giao và kết quả demo

W02 bắt đầu từ `adb787e` trên `origin/test`. Giao diện W01 đối chiếu với `666bd0c`. Codex viết bộ kiểm, kiểm cấu hình và áp script lên VM chung. Antigravity CLI 1.5.9 dùng Gemini 3.8 Flash Low để review hợp đồng đã lược bỏ dữ liệu riêng. Phiên review `d450cd8a-ec3e-49fa-9134-2813bcdfa777` đề xuất ca lọc trường dư, từ chối dữ liệu sai và xử lý lỗi API an toàn. Kiểm thử yêu cầu từ chối nhãn quá dài hoặc chứa ký tự điều khiển, tránh cắt nhãn làm đổi nội dung.

| Luồng | Bằng chứng | Từ lúc ghi sự kiện đến Bot API trả ok |
|---|---|---|
| Windows → Cowrie → Wazuh → Telegram | SSH thật, mã phiên `30457db5f882`, `a9c6eb2bb484`, `602de9d89efc` | 2,080 s, 2,540 s, 3,698 s |
| nftables | Một kết nối tới cổng đóng, lấy được log `LAB_WAN_BLOCK` | Một block không đạt ngưỡng |
| Firewall → Wazuh → Telegram | Ba sự kiện tổng hợp được gắn nhãn mẫu | 2,105 s, 2,739 s, 3,055 s |

Đồng hồ VM đã đồng bộ khi đo. Windows truy cập được cổng Dashboard trên Host-only. Cả sáu ID có trong Wazuh Indexer; chưa đối chiếu từng ID qua giao diện Dashboard. Bộ thử tương quan firewall đạt. Hash SHA-256 của script áp lên VM trùng file bàn giao. Các số đo kết thúc lúc Bot API chấp nhận tin. Phần firewall dùng dữ liệu mẫu để kiểm ngưỡng và gửi Telegram.
