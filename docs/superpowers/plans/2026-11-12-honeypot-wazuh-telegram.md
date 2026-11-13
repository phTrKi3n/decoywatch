# Triển khai hệ thống bẫy Honeypot thế hệ mới kết hợp Wazuh SIEM & cảnh báo tấn công Real-time qua Telegram

**Trạng thái** — Bản nháp local 14/11/2026, chờ chủ repo duyệt trước lần push đầu. [README](../../../README.md) · [Quy tắc cho agent](../../../AGENTS.md).

## Mục tiêu và phạm vi

Một VM Ubuntu trên VMware nhận kết nối từ Windows qua **WAN mô phỏng Host-only**. Wazuh gửi hai loại thông báo độc lập qua Telegram: hoạt động đăng nhập vào bẫy SSH Cowrie và dấu hiệu dò nhiều cổng trên chính VM. Chỉ gửi tóm tắt đã lọc. Log gốc dùng để kiểm chứng nội bộ.

WAN mô phỏng là mạng thử nghiệm giữa Windows và VM. Bản demo quan sát lưu lượng tới VM trên card này. Đường ra Internet của VM đi qua card VMware NAT để gửi Telegram. Windows vẫn dùng gateway hiện tại cho Internet.

## Kiến trúc và ranh giới mạng

| Thành phần | Thiết lập dự kiến |
|---|---|
| Windows host | Máy khách thử nghiệm trên VMnet Host-only. Adapter này dùng `192.168.100.10/24`, để trống gateway. |
| Ubuntu Server 24.04 LTS | **4 vCPU, 10 GiB RAM, 70 GB đĩa động**. Card Host-only dùng `192.168.100.20/24`. Card NAT dùng gateway mặc định và DNS cho Ubuntu. Xác nhận subnet không trùng mạng nhà, VPN hoặc NAT. |
| Ubuntu firewall | Dùng nftables làm firewall máy chủ, chặn mặc định inbound, giới hạn dịch vụ theo interface. Cowrie TCP `2222` phục vụ phía Host-only. Ghi log kết nối TCP mới bị chặn tới IP Host-only, gồm interface, nguồn, đích và cổng đích. Tách ngoại lệ Dashboard chỉ cho Windows quản trị. |
| Cowrie | Cài trực tiếp, phiên bản cố định, chạy shell giả lập bằng tài khoản dịch vụ riêng. Dùng UID riêng không có quyền quản trị. Trong nftables, áp chính sách output theo UID socket (`meta skuid`) cho IPv4 và IPv6. Chỉ cho UID này trả lời phiên TCP Cowrie đã được phép qua card Host-only, ở chiều reply và từ cổng dịch vụ. Chặn kết nối mới do UID này khởi tạo, kể cả qua NAT và loopback. Quy tắc giới hạn UID phải có hiệu lực trước mọi luật output cho phép rộng. |
| Wazuh | Manager, Indexer và Dashboard trên cùng VM. Manager đọc file log cục bộ qua `localfile`. Dashboard truy cập từ Windows quản trị. API và Indexer chỉ phục vụ nội bộ VM. |
| Telegram | Wazuh Integrator gọi script qua HTTPS. Token và chat ID trong file cấu hình cục bộ chỉ tài khoản vận hành được đọc. |

Giữ inbound trên NAT ở mặc định chặn, không mở VMware NAT port-forward hoặc bridge vào mạng vật lý. Tắt định tuyến giữa hai NIC. Với IPv6, áp và kiểm chính sách tương đương hoặc dùng lab IPv4. Cowrie và Wazuh dùng chung OS, nên kiểm rõ Cowrie không đọc được bí mật bot hay sửa được log firewall và rule Wazuh. Wazuh Quickstart khuyến nghị 8 GiB RAM cho bộ trung tâm. Mức 10 GiB là dự toán ban đầu cho cả VM. Chỉ thử 12 GiB nếu Windows còn đủ RAM khi chạy cùng các ứng dụng demo. Chốt sau khi kiểm RAM khả dụng, paging và độ ổn định.

## Giao diện dữ liệu và cảnh báo

| Luồng | Đầu vào và điều kiện | Đầu ra |
|---|---|---|
| **Cowrie** | JSON từng dòng, có `eventid`, `protocol`, `timestamp`, `src_ip`, `session`. Rule dự kiến `100110` khớp `cowrie.login.success` qua SSH. | **“Cowrie ghi nhận đăng nhập SSH vào bẫy”**, UTC, IP nguồn, mã phiên. |
| **Firewall** | Chỉ nhận log chặn TCP mới của firewall trên card và IP Host-only. Theo cặp IP nguồn/đích, ghi nhận ít nhất **5 cổng đích phân biệt trong 30 giây**. Cổng lặp không tăng số cổng. | **“Phát hiện dấu hiệu dò quét vào WAN mô phỏng”**, UTC, IP nguồn/đích, số cổng, ID sự kiện. Rule dự kiến `100120`. |

W01 chịu trách nhiệm đếm cổng phân biệt. Dùng tương quan Wazuh sẵn có nếu kiểm thử chứng minh đúng ngưỡng, đúng cửa sổ và đúng ca cổng lặp xen kẽ. Nếu không đạt, dùng bộ gom sự kiện phòng thủ cục bộ đọc log firewall và xuất một dòng JSON đã chuẩn hóa cho Wazuh khi vượt ngưỡng. Dùng thời điểm nhận theo đồng hồ đơn điệu cho cửa sổ khi đọc trực tiếp, UTC cho sự kiện xuất ra. Giới hạn trạng thái theo thời gian và dung lượng. Mỗi cặp chỉ sinh một sự kiện trong cửa sổ chống lặp 30 giây. W02 dùng fixture alert có cùng trường đầu ra cho cả hai cách.

C đọc nhãn từ `rule.description` của hai rule đã duyệt. Kiểm chuỗi một dòng, giới hạn 120 ký tự, loại ký tự điều khiển và gửi dưới dạng văn bản thuần. B sở hữu nhãn trong rule và fixture. C kiểm định dạng và các trường của thông báo. Không gửi mật khẩu, token, dòng log thô hoặc lệnh nhập trong shell. Dùng dữ liệu tổng hợp hoặc đã làm sạch trong Git. Cowrie và Wazuh dùng chung đồng hồ VM. Đồng bộ Ubuntu qua NIC NAT theo dịch vụ giờ đã chọn. Với NTP thông thường, xác nhận UDP 123 tới nguồn upstream được phép cho dịch vụ đồng bộ giờ. Kiểm nguồn giờ đang hoạt động trước khi đo.

## Phân công và thứ tự

| Task | Chủ sở hữu | File và kết quả |
|---|---|---|
| P00 — Chốt bản nháp | A — Bạn | Duyệt tài liệu, kiểm tài nguyên host, subnet và phiên bản. Lần push đầu thực hiện sau khi chủ repo duyệt. |
| I01 — VMware và firewall | A — Windows chủ lab | `infra/README.md`, `infra/versions.md`. Hai NIC, chính sách inbound, log chặn và Internet qua NAT. |
| C01 — Cowrie | A — Windows chủ lab | `cowrie/README.md`, `cowrie/fixtures/events.ndjson`. Phiên SSH thật và mẫu thành công/thất bại đã làm sạch. |
| W01 — Wazuh và phát hiện | B — Windows thứ hai | `wazuh/README.md`, `wazuh/rules/`, `wazuh/fixtures/`, `wazuh/firewall/` nếu cần bộ gom. B có thể dùng Wazuh Manager cùng phiên bản trong lab riêng. Bàn giao hai alert mẫu cho C. |
| W02 — Telegram | C — macOS | `wazuh/telegram/`. Script, cấu hình mẫu và test với alert giả, có thể làm trước khi lab chung sẵn sàng. |
| D01 — Nghiệm thu | A điều phối, B và C hỗ trợ | `infra/demo.md`. Cùng commit, hai luồng, số đo và ảnh đã làm sạch. |

Mỗi task có một chủ sở hữu, một phiên agent chỉnh sửa tại một thời điểm và nhánh riêng. B review fixture Cowrie và log firewall của A. C review schema đầu ra của B. B review tích hợp của C. A là người áp cấu hình lên VM chung. Ghi commit gốc và commit bàn giao khi đổi agent. Thay đổi schema, rule ID hoặc IP phải cập nhật trong plan và kiểm lại bên nhận. Sau lần push đầu, dùng PR có review để cập nhật `main`.

## Checklist nghiệm thu

- [ ] **P00.** Ghi quyết định đã chốt là **một VM Ubuntu**. Xác nhận với yêu cầu môn học rằng bản demo dùng firewall trên VM và WAN mô phỏng. Ghi RAM, subnet và phiên bản đã chọn. Nếu môn học yêu cầu router phân vùng riêng, cập nhật kiến trúc trước khi triển khai.

- [ ] **I01.** Windows vào được Cowrie qua Host-only. VM tới được Bot API qua NAT. Windows giữ default route vật lý. Kiểm cổng quản trị trên NAT bị chặn và một phép thử kết nối đã định trước sinh log block trên Host-only.
- [ ] **C01.** Cowrie tạo JSON có mã phiên. Bàn giao fixture dương và âm. Kiểm bằng tài khoản Cowrie rằng một kết nối mới tới dịch vụ kiểm thử và đường ra NAT bị chặn. Xác nhận phiên SSH vào Cowrie vẫn trả lời, Wazuh vẫn gửi được Telegram và tài khoản Cowrie không đọc được bí mật bot. Lặp kiểm sau khi khởi động lại VM.
- [ ] **W01.** Manager đọc được log Cowrie và firewall thật. Dùng một bản ghi nftables đã làm sạch để kiểm decoder trên phiên bản Wazuh đã chọn. Nếu decoder hiện có thiếu interface, action, IP nguồn/đích hoặc cổng đích, chuẩn hóa các trường trong bộ gom hoặc viết decoder nhỏ trước khi kiểm ngưỡng. Kiểm rule Cowrie bằng `wazuh-logtest`. Với firewall, kiểm một block, 4 cổng phân biệt, 5 cổng phân biệt, cổng lặp xen kẽ, IP nguồn hoặc đích khác, interface khác, và ngoài 30 giây. Kiểm một sự kiện trong cửa sổ chống lặp. Dùng fixture để kiểm ngưỡng và dữ liệu trực tiếp có kiểm soát để xác nhận đường thu log. Đối chiếu hai alert thật với fixture trước khi ghép.
- [ ] **W02.** Chỉ nhận hai rule đã chốt. Kiểm loại alert lạ, nhãn quá dài hoặc nhiều dòng, thiếu trường, IP sai, dữ liệu nhạy cảm dư, timeout và lỗi API. Ghi mã phiên hoặc ID, UTC trước và sau khi API trả `ok`, và thời gian gọi API đo bằng đồng hồ đơn điệu. Giữ token ngoài log, fixture và repo.
- [ ] **D01.** Chạy một phiên SSH đã định trước để nối cùng mã phiên qua Cowrie, Dashboard và Telegram. Với firewall, dùng phép kiểm chính sách có kiểm soát, chỉ tới IP Host-only của VM do nhóm quản lý. Đối chiếu block thật và kiểm tương quan bằng bộ log mẫu trên đầu vào thử nghiệm. Ghi rõ nguồn và phần đã kiểm trực tiếp. Đo ba lượt mỗi loại từ sự kiện đủ điều kiện đến khi Bot API trả `ok`. Nếu kiểm tốc độ, so Internet của Windows khi lab tắt và khi lab đang demo, đồng thời ghi tình trạng RAM và CPU. Kết quả đó phản ánh ảnh hưởng của lab lên host.

## Tài liệu tham chiếu

- [VMware Virtual Network Editor](https://knowledge.broadcom.com/external/article/339371/using-the-virtual-network-editor-in-vmwa.html) · [Firewall Ubuntu](https://ubuntu.com/server/docs/how-to/security/firewalls/) · [nftables lọc theo UID socket](https://wiki.nftables.org/wiki-nftables/index.php/Matching_packet_metainformation#Matching_by_socket_UID_/_GID)
- [Cài đặt Cowrie](https://docs.cowrie.org/en/stable/INSTALL.html) · [Sự kiện Cowrie](https://docs.cowrie.org/en/stable/OUTPUT.html)
- [Wazuh Quickstart](https://documentation.wazuh.com/current/quickstart.html) · [Thu log local](https://documentation.wazuh.com/current/user-manual/reference/ossec-conf/localfile.html) · [Kiểm rule](https://documentation.wazuh.com/current/user-manual/ruleset/testing.html)
- [Wazuh Integrator](https://documentation.wazuh.com/current/user-manual/manager/integration-with-external-apis.html) · [Telegram Bot API](https://core.telegram.org/bots/api#sendmessage)
