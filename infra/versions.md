# Phiên bản đã triển khai

| Thành phần | Giá trị đã đọc từ lab |
|---|---|
| VMware Workstation | 17.6.4 build 24832109 |
| Ubuntu Server | 24.04.5 LTS, 4 vCPU, 8 GiB RAM, đĩa ảo 70 GB |
| open-vm-tools | 2:13.0.10-0ubuntu0.24.04.2 |
| nftables | 1.0.9-1ubuntu0.1 |
| Cowrie | 3.1.6 |
| Wazuh Manager, Indexer, Dashboard | 4.14.10-1 |
| Filebeat | 7.10.2-2 |
| VMnet1 Host-only | Windows 192.168.100.1, Ubuntu ens37 192.168.100.20/24 |
| VMnet8 NAT | Ubuntu ens33 DHCP, lúc kiểm là 192.168.117.128/24, gateway 192.168.117.2 |

Giữ mức RAM 8 GiB đã chạy được trên VM hiện tại. Mức 10 GiB trong dự toán ban đầu là giá trị tham khảo khi chuẩn bị máy. Phiên kiểm tài nguyên thấy khoảng 5,2 GiB khả dụng sau khi các dịch vụ khởi động. Khi demo dài, kiểm RAM và tốc độ tăng log.
