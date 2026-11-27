# AgentSpace

![AgentSpace — không gian làm việc AI do bạn quản lý](docs/assets/agentspace-banner.svg)

**Không gian làm việc AI lưu cục bộ: quản lý context dự án, tạo prompt và bàn giao giữa các phiên AI.**

[English](README.md) · [Desktop](docs/DESKTOP.md) · [DevSpace](docs/DEVSPACE.md) · [Changelog](CHANGELOG.md)

> Bản phát hành đầu tiên v0.2.0 — Developer Preview. Đã đạt 22 kiểm thử tự động và kiểm thử GUI cơ bản trên Ubuntu; chưa xác nhận bộ cài, DPI nhiều màn hình và chuyển giao giữa các client thực tế.

## AgentSpace giải quyết vấn đề gì?

Khi đổi chat, model hoặc tài khoản AI được cấp quyền, bạn không muốn giải thích lại toàn bộ dự án. AgentSpace lưu quyết định, kết quả, nhiệm vụ, bằng chứng và hướng làm tiếp trong các file Markdown riêng trên máy.

Ứng dụng desktop giúp chọn dự án, xem lịch sử và tạo prompt; AI có công cụ đọc/ghi file được cấp quyền mới thực hiện việc tiếp quản và lưu context. Bạn quyết định thời điểm lưu.

## Bắt đầu

Cần Git, Python 3.8+ và Tkinter nếu sử dụng giao diện desktop.

```bash
git clone https://github.com/guwoh/agentspace.git
cd agentspace
python3 scripts/agentspace.py init ~/work/agentspace-private
python3 -B scripts/desktop.py --workspace ~/work/agentspace-private
```

Trên Windows dùng `python` và chọn thư mục riêng, ví dụ `../agentspace-private`. Lệnh init không ghi đè file đã có.

Chọn dự án (hoặc tạo prompt cho dự án mới), chọn Resume, ấn Generate & copy rồi dán vào AI đã kết nối công cụ file, chẳng hạn [DevSpace](docs/DEVSPACE.md). Khi cần bàn giao, chọn Save context hoặc yêu cầu AI lưu context rõ ràng.

## Chức năng

| Module | Công dụng |
| --- | --- |
| Projects | Danh mục và lựa chọn dự án |
| Prompt Studio | Tiếp quản, lưu, tổng quan, bàn giao, cập nhật skill và dự án mới |
| Context & History | Đọc brief, context đầy đủ và snapshot |
| Skills | Tạo, sửa skill Markdown riêng |
| Connections | Mở AI client, kiểm tra executable DevSpace |
| Backup & Settings | Sao lưu/phục hồi hồ sơ văn bản, chỉnh cỡ chữ |
| CLI | Khởi tạo, liệt kê, kiểm tra, sinh prompt |

## Cơ chế lưu và tiếp quản

AI đọc BRIEF trước, mở CURRENT và bằng chứng liên quan khi thiếu thông tin. Khi lưu theo yêu cầu rõ ràng, AI tạo snapshot đầy đủ, cập nhật CURRENT, sinh BRIEF và đồng bộ INDEX. Không khôi phục được tin nhắn chưa từng lưu. Không để nhiều AI đồng thời ghi cùng hồ sơ.

Xem [quy trình](protocol/WORKFLOW.md), [mẫu đầy đủ](protocol/HANDOFF_TEMPLATE.md), [mẫu brief](protocol/BRIEF_TEMPLATE.md) và [ví dụ hư cấu](examples/BRIEF.md).

## Dữ liệu và giới hạn

AgentSpace không tự gửi prompt, không kết nối MCP thay người dùng và không cần AI API key. AI đám mây có thể nhận dữ liệu bạn cấp quyền đọc. Giữ context thật, đường dẫn nội bộ, token, transcript và ảnh riêng ngoài checkout công khai. Gói backup không mã hóa. Xem [quy định riêng tư](docs/PRIVACY.md).

Xem [hướng dẫn desktop](docs/DESKTOP.md), [kiểm thử](docs/TESTING.md) và [hướng dẫn CLI](README.md#cli-usage). Native build, DPI nhiều màn hình và handoff giữa tài khoản vẫn cần kiểm thử thực tế.

## Đóng góp

Hoan nghênh issue và PR có bước tái hiện rõ ràng, dùng dữ liệu giả hoặc đã loại bỏ thông tin riêng. Kiểm tra danh sách file và chạy test trước khi gửi.

Giấy phép [MIT](LICENSE).
