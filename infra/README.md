# VMware và nftables

P00 chốt một VM Ubuntu theo lựa chọn của chủ lab. Giảng viên cho phép nhóm tự chọn kiến trúc theo đề tài và yêu cầu bảo mật. Cowrie được giới hạn quyền bằng systemd và nftables. Cowrie và SIEM vẫn dùng chung kernel. Host-only là WAN mô phỏng cho lưu lượng đến VM.

## Tạo mạng

1. Tạo một VM Ubuntu Server với thông số trong [phiên bản lab](versions.md). Trong VMware, dùng VMnet8 NAT cho card `ens33` và VMnet1 Host-only cho `ens37`. Bật Connected và Connect at power on cho cả hai card. Đặt VMnet1 là `192.168.100.0/24`, Windows là `192.168.100.1` và để trống default gateway trên adapter này. Kiểm subnet trên Windows bằng `route print -4`. Tránh trùng với NAT, mạng nhà và VPN.
2. Dùng console VMware. Chạy `ip -br link` để kiểm tên card, sau đó đặt [mẫu Netplan](90-cowrie-lab.yaml) ở `/etc/netplan/90-cowrie-lab.yaml` với quyền `0600`. Giữ DHCP IPv4 trên card NAT của cấu hình Ubuntu. Chạy `sudo netplan try` và kiểm `ip -4 route show default`. Gateway mặc định chỉ đi qua ens33.
3. Tạo tài khoản dịch vụ theo [hướng dẫn Cowrie](../cowrie/README.md), rồi áp firewall bên dưới trước khi khởi chạy Cowrie hoặc Wazuh. Giữ VMnet8 không có port forwarding và giữ cả hai card ở mạng ảo VMware.

## Áp firewall

Chạy từ checkout trên Ubuntu. Mẫu này thay toàn bộ ruleset, dùng cho VM chuyên dụng của lab. Chụp snapshot trước khi áp và giữ console VMware để phục hồi. Các bước giả định Ubuntu đã nhận Internet qua NAT.

```sh
sudo apt-get install nftables open-vm-tools
cowrie_uid=$(id -u cowrie)
test -n "$cowrie_uid" || exit 1
sed "s/@COWRIE_UID@/$cowrie_uid/g" infra/nftables.conf > /tmp/cowrie-lab.nft
sudo nft -c -f /tmp/cowrie-lab.nft || exit 1
sudo cp -an /etc/nftables.conf /etc/nftables.conf.before-cowrie
sudo install -m 0755 /tmp/cowrie-lab.nft /etc/nftables.conf
sudo systemctl enable nftables
sudo systemctl restart nftables
printf "%s\n" "net.ipv4.ip_forward = 0" "net.ipv6.conf.all.forwarding = 0" | sudo tee /etc/sysctl.d/90-cowrie-lab.conf >/dev/null
sudo sysctl -p /etc/sysctl.d/90-cowrie-lab.conf
```

Sau reboot, kiểm cả hai giá trị bằng 0 với `sysctl net.ipv4.ip_forward net.ipv6.conf.all.forwarding`. Nếu áp lại firewall trên lab đang chạy, khởi động lại Cowrie và bộ gom firewall sau khi nftables lên.

## Kiểm lại

- Windows mở Cowrie ở `192.168.100.20:2222` và Dashboard qua HTTPS ở `192.168.100.20`. Dashboard chỉ cho IP Windows quản trị `192.168.100.1`. Kiểm firewall bằng một kết nối TCP định trước tới cổng đóng của VM và xem tiền tố `LAB_WAN_BLOCK` trong `sudo journalctl -k`.
- Kiểm `sudo nft list table inet cowrie_lab`. Quy tắc output của UID Cowrie chỉ cho trả lời phiên đã thiết lập từ cổng 2222 qua Host-only. Quy tắc tiếp theo chặn mọi kết nối khác của UID, gồm qua NAT, loopback và IPv6. Inbound mặc định drop. Dịch vụ cùng VM dùng đường nội bộ.
- Dùng `timedatectl show -p NTPSynchronized` và kiểm HTTPS từ Ubuntu trước khi đo. Kiểm NAT IP của VM không phục vụ Dashboard hoặc Cowrie bằng `ss -ltn` và bảng lọc.
- Khôi phục từ snapshot hoặc dùng VMware console để chép lại `/etc/nftables.conf.before-cowrie` và nạp lại firewall.
