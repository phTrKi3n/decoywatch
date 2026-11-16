# Wazuh và tương quan firewall

Cài Wazuh 4.14.10 all-in-one trên VM đã áp [firewall](../infra/README.md). Xem [Wazuh Quickstart](https://documentation.wazuh.com/current/quickstart.html). Installer dòng 4.14 do Wazuh phát hành tại `https://packages.wazuh.com/4.14/wazuh-install.sh`. Trước khi dùng, kiểm phiên bản của bộ cài và đối chiếu [bảng phiên bản](../infra/versions.md). Nếu chạy bản vá khác, chạy lại đầy đủ phép kiểm bên dưới. Trên lab, dùng chế độ all-in-one và kiểm phiên bản gói sau khi trình cài đặt hoàn tất. URL theo dòng 4.14 có thể phục vụ bản vá mới hơn.

```sh
curl --fail --show-error --location --remote-name https://packages.wazuh.com/4.14/wazuh-install.sh
sudo bash wazuh-install.sh -a
dpkg-query -W wazuh-manager wazuh-indexer wazuh-dashboard filebeat
```

Giữ thư mục và gói tài khoản do installer tạo ngoài repo.

## Thu log và rule

Chạy trên Ubuntu từ thư mục gốc repo. Bước này giả định Cowrie đã tạo log theo [C01](../cowrie/README.md).

```sh
sudo install -d -m 0755 /usr/local/lib/cowrie-lab
sudo install -m 0644 wazuh/firewall/firewall.py /usr/local/lib/cowrie-lab/firewall.py
sudo install -d -m 0750 /var/log/cowrie-lab
sudo touch /var/log/cowrie-lab/firewall.json
sudo chmod 0640 /var/log/cowrie-lab/firewall.json
sudo install -m 0644 wazuh/firewall/cowrie-firewall-events.service /etc/systemd/system/cowrie-firewall-events.service
sudo install -o root -g wazuh -m 0640 wazuh/rules/cowrie_lab.xml /var/ossec/etc/rules/cowrie_lab.xml
sudo cp -an /var/ossec/etc/ossec.conf /var/ossec/etc/ossec.conf.before-cowrie
```

Chép hai khối `localfile` từ [mẫu XML](localfiles.xml) vào một khối `ossec_config` hiện có trong `/var/ossec/etc/ossec.conf`, mỗi đường dẫn một lần. Trên VM chung, API bind `127.0.0.1` trong `/var/ossec/api/configuration/api.yaml` với `host: ['127.0.0.1']`. Giữ Indexer tại localhost. Dashboard bind `192.168.100.20` bằng `server.host` tại `/etc/wazuh-dashboard/opensearch_dashboards.yml`. Tạo drop-in cho Dashboard với `Wants=network-online.target` và `After=network-online.target` trong mục `[Unit]` để card Host-only sẵn sàng khi khởi động.

```sh
sudo /var/ossec/bin/wazuh-analysisd -t
sudo /var/ossec/bin/wazuh-logcollector -t
sudo systemctl daemon-reload
sudo systemctl enable --now cowrie-firewall-events
sudo systemctl restart wazuh-manager wazuh-dashboard
sudo systemctl is-active cowrie-firewall-events wazuh-manager wazuh-indexer wazuh-dashboard filebeat
```

Bộ gom giữ file output mở trong khi chạy. Khi xoay log bằng cách đổi tên file, khởi động lại bộ gom để mở file mới và kiểm Wazuh vẫn thu được sự kiện.

## Kiểm thử

- Chạy `python3 wazuh/firewall/firewall.py --check`. Bộ gom lọc tiền tố kernel, card, IP đích và TCP. Nó đếm 5 cổng đích phân biệt trong 30 giây theo cặp nguồn/đích, với tối đa một cảnh báo mỗi 30 giây cho cặp đó.
- Đưa từng dòng từ [Cowrie](../cowrie/fixtures/events.ndjson) và [firewall JSON](fixtures/firewall-event.ndjson) vào `sudo /var/ossec/bin/wazuh-logtest`. SSH thành công khớp `100110`; chuỗi 5 lần `cowrie.login.failed` cùng `src_ip` trong 60 giây khớp `100111` rồi nâng lên `100112`; `cowrie.command.input` và `cowrie.session.file_download` khớp `100115`; firewall JSON khớp `100120`. [Mẫu nftables](fixtures/nftables-block.log) là đầu vào của bộ gom Python. Wazuh đọc JSON đã chuẩn hóa. Một block đơn lẻ không đạt ngưỡng tương quan.
- [Bốn mẫu cảnh báo cho W02](fixtures/telegram-alerts.ndjson) giữ các trường theo hợp đồng Telegram (`100110`, `100112`, `100115`, `100120`). Chúng dùng địa chỉ tài liệu ở nguồn và dữ liệu tổng hợp. Kiểm cảnh báo thực tế trong `/var/ossec/logs/alerts/alerts.json` theo mã phiên hoặc ID sự kiện. Khi ghi bằng chứng chỉ trích các trường cần thiết.
- Nếu sửa interface hoặc IP, cập nhật đồng thời Netplan, nftables, Cowrie, bộ gom và địa chỉ bind Dashboard. Kiểm firewall, rule và các quyền trước khi bật lại. Khi rollback, dùng config Wazuh đã sao lưu và khởi động lại Manager.
