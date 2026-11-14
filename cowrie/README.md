# Cowrie SSH

## Tài khoản và firewall

Chạy trên VM Ubuntu chuyên dụng. Tạo người dùng hệ thống riêng, rồi áp [firewall](../infra/README.md) trước khi bật dịch vụ. Tài khoản quản trị Ubuntu tiếp tục dùng console VMware.

```sh
getent passwd cowrie >/dev/null || sudo useradd --system --user-group --home-dir /var/lib/cowrie --shell /usr/sbin/nologin cowrie
sudo install -d -o cowrie -g cowrie -m 0750 /var/lib/cowrie
```

## Cài và chạy

```sh
sudo apt-get install python3-venv openssl
sudo python3 -m venv /opt/cowrie/venv
sudo /opt/cowrie/venv/bin/pip install 'cowrie==3.1.6'
cd /var/lib/cowrie
sudo -u cowrie /opt/cowrie/venv/bin/cowrie init
```

Quay về thư mục gốc repo để cài cấu hình. Tạo mật khẩu ngẫu nhiên cho tài khoản bẫy `labdemo`, lưu riêng với quyền chỉ đọc cho root và tài khoản dịch vụ. Dùng mật khẩu này khi nghiệm thu Cowrie qua SSH. OpenSSH quản trị là dịch vụ riêng.

```sh
sudo install -o root -g cowrie -m 0640 cowrie/cowrie.cfg /var/lib/cowrie/etc/cowrie.cfg
sudo bash -euc 'umask 077; p=$(openssl rand -hex 16); printf "labdemo:x:%s\n" "$p" > /var/lib/cowrie/etc/userdb.txt; chown root:cowrie /var/lib/cowrie/etc/userdb.txt; chmod 0640 /var/lib/cowrie/etc/userdb.txt'
sudo install -m 0644 cowrie/cowrie-lab.service /etc/systemd/system/cowrie-lab.service
sudo systemctl daemon-reload
sudo systemctl enable --now cowrie-lab
sudo ss -ltn 'sport = :2222'
```

Unit giới hạn Cowrie được ghi trong `/var/lib/cowrie` và dùng thư mục tạm riêng. Cowrie không có Linux capabilities, hệ thống file được bảo vệ và nftables giới hạn lưu lượng theo UID. Giữ quyền quản trị và dịch vụ SIEM riêng với tài khoản Cowrie. nftables áp giới hạn cho socket IP. Socket Unix vẫn được phép trong unit, vì vậy không cấp quyền truy cập Docker socket, socket quản trị hay dịch vụ chuyển tiếp cục bộ cho Cowrie. Mô hình một VM dùng chung kernel.

## Nghiệm thu và log

- Windows thực hiện một phiên SSH đã định trước với tài khoản thử nghiệm. Ghi mã phiên từ log `/var/lib/cowrie/var/log/cowrie/cowrie.json`, rồi đối chiếu rule `100110` trong Wazuh. [Mẫu sự kiện tổng hợp](fixtures/events.ndjson) gồm đăng nhập SSH thành công, thất bại và mẫu Telnet.
- Log gốc Cowrie và dữ liệu Wazuh nội bộ có thể chứa thông tin đã nhập vào bẫy. Chỉ dùng tài khoản lab. Khi bàn giao, giữ trường đã chọn và thay địa chỉ nguồn bằng địa chỉ tài liệu.
- Sau reboot kiểm `systemctl is-active nftables cowrie-lab`, thử lại SSH và xác nhận UID Cowrie bị chặn kết nối mới. Khi tích hợp Telegram đã bật, xác minh `sudo -u cowrie test -r /var/ossec/etc/cowrie-telegram.json` trả mã khác 0.
