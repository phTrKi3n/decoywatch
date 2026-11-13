# Quy trình Git của nhóm

## Nhánh và review

| Nhánh | Mục đích | Cách đưa thay đổi vào |
|---|---|---|
| `main` | Bản nhóm đã nghiệm thu | Chủ repo ghép PR từ `test` sau khi một thành viên khác review đúng diff hiện tại. |
| `test` | Tích hợp và chạy thử trước demo | Người phụ trách ghép PR từ nhánh công việc đã review. |
| `codex/<task>-<mo-ta>` | Một task của một thành viên hoặc agent | Push đúng nhánh được giao. Dùng checkout riêng nếu có nhiều agent trên một máy. |

Bắt đầu khi checkout sạch. Cập nhật remote, rồi tạo nhánh mới. Thay mã task và tên nhánh theo việc được giao.

```sh
git status --short --branch
git fetch origin
git switch -c codex/w02-telegram origin/test
```

Mỗi PR ghi mã task, phạm vi file, lệnh kiểm, kết quả và phần còn chờ kiểm. Một thành viên khác kiểm diff. Commit thêm sau review cần được xem lại. Giữ nguyên lịch sử đã chia sẻ. Agent chỉ dùng quyền ghi cần cho nhánh công việc, còn quyền quản trị repo do chủ repo giữ.

## Commit

Dùng dạng `type(scope): mô tả ngắn`. Một commit giải quyết một thay đổi có thể review và hoàn tác độc lập. Scope theo phần việc, ví dụ `infra`, `cowrie`, `wazuh`, `telegram` hoặc `repo`.

| Type | Dùng cho |
|---|---|
| `feat` | Chức năng mới |
| `fix` | Sửa hành vi sai |
| `docs` | Kế hoạch, tài liệu hoặc quy tắc |
| `test` | Test hoặc fixture đã làm sạch |
| `chore` | Bảo trì cấu hình repo hoặc công cụ |
| `revert` | Hoàn tác commit đã chia sẻ |

Ví dụ `feat(telegram): format Cowrie alerts`, `fix(wazuh): ignore repeated destination ports`, `docs(repo): define branch and commit workflow`. Nếu cần, phần thân ghi lý do hoặc mã task.

Trước khi commit, chạy phép kiểm của task. Stage đường dẫn cụ thể và xem cả danh sách file lẫn nội dung diff. Dùng cấu hình mẫu và fixture đã làm sạch.

```sh
git status --short
git add -- <file-da-review>
git diff --cached --check
git diff --cached
git commit -m "docs(repo): define branch and commit workflow"
```

## Hoàn tác khi sai

- **Chưa commit.** Xem `git diff` trước. Nếu stage nhầm, dùng `git restore --staged -- <file>` để giữ nội dung sửa trong working tree.
- **Đã chia sẻ commit.** Tạo nhánh sửa từ nhánh bị ảnh hưởng, dùng `git revert <sha>`, chạy kiểm tra và mở PR về đúng nhánh đó. Nếu commit đã vào cả `main` và `test`, sửa qua `test` rồi đưa bản đã kiểm lên `main`. Với merge commit, xem diff và chọn đúng parent trước khi revert, hoặc dùng chức năng Revert PR của GitHub nếu có.
- **Lộ bí mật.** Báo chủ repo và thu hồi hoặc đổi token ngay. Revert sửa nội dung hiện tại nhưng lịch sử Git vẫn có thể chứa bí mật. Chủ repo quyết định xử lý lịch sử nếu cần.

Giữ lịch sử các nhánh đã chia sẻ. Tránh force-push, xóa nhánh chung, `git reset --hard` và `git clean` trong checkout dùng chung.

## Bảo vệ main trên GitHub

Khi gói repo hỗ trợ, bật ruleset chỉ nhắm `main`: yêu cầu PR, ít nhất một review, bỏ hiệu lực review cũ khi có commit mới, giải quyết hội thoại, chặn force-push và xóa nhánh, áp dụng cả với admin. Chỉ đặt status check bắt buộc khi nhóm đã có CI ổn định. Cho đến khi GitHub hiển thị ruleset đang được thực thi, quy trình này dựa vào quyền truy cập và review của nhóm. [Tài liệu GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
