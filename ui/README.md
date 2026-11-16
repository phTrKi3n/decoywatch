# Enterprise SOC Console & Telegram Alert Preview (`ui/`)

Giao diện quản trị tĩnh tại [`index.html`](index.html) được thiết kế theo chuẩn [`21st-ui-build`](https://21st.dev/) (dựa trên bố cục **Framed Alert Panel** từ component `c-alert-14`) và nguyên tắc [`frontend-ui-engineering`](../README.md):

- **Không phụ thuộc CDN ngoài**: Chạy trực tiếp bằng cách mở file `ui/index.html` trên trình duyệt hoặc phục vụ cục bộ.
- **3 phân hệ giám sát**:
  1. **Sự cố & Telegram Card**: Lọc theo Rule ID (`#100110`, `#100112`, `#100115`, `#100120`), tìm kiếm theo IP/mã phiên, xem trước trực tiếp bản tin Telegram Enterprise `<pre>` + `<blockquote>` và sao chép HTML/JSON payload.
  2. **Ranh giới mạng & Cô lập**: Bảng đối chiếu kiểm chứng Host-only (`192.168.100.20`), NAT (`192.168.117.128`) và giới hạn UID `999` (`cowrie`).
  3. **Docker & Kiểm toán Bảo mật**: Tổng hợp các phát hiện đã khắc phục từ `/cloudflare-security-audit-defensive` (`audit/findings.json`) và kết quả chạy Docker hardened (`docker/compose.yaml`).
