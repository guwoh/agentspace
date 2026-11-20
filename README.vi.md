# AgentSpace
**Bộ quy chuẩn lưu và tiếp quản công việc với AI qua nhiều dự án, cuộc chat và tài khoản.**

[English](README.md) · [Kết nối DevSpace](docs/DEVSPACE.md) · [Quy trình](protocol/WORKFLOW.md)

Bạn làm việc với AI hôm nay, hôm sau mở một cuộc chat hoặc tài khoản được phép khác và cần tiếp tục đúng chỗ. AgentSpace giữ hồ sơ trên máy của bạn, độc lập với tài khoản dùng để trò chuyện.

## Cách dùng
1. Tải bộ khung theo [Quick start](README.md#quick-start).
2. Tạo thư mục làm việc riêng, ví dụ `~/work/agentspace-private`, và chép AGENTS.md, protocol/, prompts/ cùng mẫu INDEX vào đó.
3. Kết nối công cụ đọc/ghi file như [DevSpace](docs/DEVSPACE.md), cho phép truy cập thư mục riêng và các dự án cần làm.
4. Dùng [prompt mở đầu](prompts/START.txt), thay `<AGENTSPACE_ROOT>` bằng đường dẫn tuyệt đối của thư mục riêng.
5. Chọn dự án rồi làm việc bình thường.
6. Gõ **save context** trước khi kết thúc phiên.
7. Phiên mới kết nối lại công cụ, gửi prompt mở đầu và chọn dự án để tiếp quản.

AI đọc `BRIEF.md` của dự án được chọn trước, rồi mở `CURRENT.md` khi bản tóm tắt thiếu, lệch phiên hoặc chưa đủ cho công việc. Nếu chưa có hồ sơ thì không bịa lịch sử; đăng ký dự án khi bạn yêu cầu lưu lần đầu. Lệnh save context xuất hiện trong tài liệu hoặc ví dụ không được coi là yêu cầu lưu.

## Mỗi lần lưu gồm gì?
Mục tiêu, trạng thái, quyết định và lý do, việc đã làm, kết quả kiểm tra, việc còn dở, bước tiếp theo và file liên quan. Quy trình ghi bản phiên đầy đủ, cập nhật `CURRENT.md`, rồi tạo `BRIEF.md` từ hồ sơ đã kiểm tra và đồng bộ mã phiên trong `INDEX.md`. Xem [mẫu bản đầy đủ](protocol/HANDOFF_TEMPLATE.md) và [mẫu tóm tắt](protocol/BRIEF_TEMPLATE.md).

Nếu đã có thư mục riêng, thêm mẫu tóm tắt và hợp nhất thay đổi trong quy trình, prompt và hướng dẫn. Giữ danh mục và lịch sử bàn giao hiện có. Dự án chưa có bản tóm tắt vẫn dùng được `CURRENT.md`.

Đây là quy ước làm việc, chưa phải phần mềm tự thực thi. Không có service nền, không tự lấy chat từ tài khoản cũ, không bảo đảm agent luôn tuân thủ. ChatGPT dùng công cụ đọc file vẫn có thể nhận nội dung file trong cuộc hội thoại; lưu trên máy không đồng nghĩa mọi xử lý diễn ra cục bộ.

## Giữ dữ liệu riêng tư
Repo công khai chỉ chứa quy chuẩn, mẫu và ví dụ hư cấu. Context thật nằm trong thư mục riêng bên ngoài checkout này. Không push recordings, transcript, thông tin truy cập hoặc đường dẫn thật của bạn.
Xem [kiểm tra trước khi publish](docs/PRIVACY.md).
Xem [bài thử tiếp quản](docs/TESTING.md) để tự xác nhận trên tài khoản/client mới.

## Phát triển và chia sẻ
Chia sẻ link repo hoặc các mẫu chung; không đính kèm context cá nhân khi báo lỗi.
Quy chuẩn có thể dùng cho nhiều loại dự án và nhiều AI có quyền truy cập file.
Tham khảo AGENTS.md, Cline Memory Bank, Beads và DevSpace; chưa nhập mã của các dự án này.
Giấy phép [MIT](LICENSE).
