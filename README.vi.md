# AgentSpace

![AgentSpace — không gian làm việc AI do bạn quản lý](docs/assets/agentspace-banner.svg)

**Đổi AI, giữ nguyên tiến độ.**

AgentSpace là không gian làm việc giúp lưu kiến thức, tiến độ và cách làm việc của từng dự án trên máy tính, để tiếp tục từ phần đã lưu khi chuyển sang phiên AI khác.

[English](README.md) · [Desktop](docs/DESKTOP.md) · [DevSpace](docs/DEVSPACE.md) · [Changelog](CHANGELOG.md)

> Nhánh phát triển v0.3.0-dev bổ sung demo tương tác. Bản public đầu tiên là [v0.2.0](https://github.com/guwoh/agentspace/releases/tag/v0.2.0). Chưa xác nhận bộ cài, DPI nhiều màn hình và chuyển giao giữa các client thực tế.

## AgentSpace giải quyết vấn đề gì?

Khi đổi chat, model hoặc tài khoản AI được cấp quyền, bạn không muốn giải thích lại toàn bộ dự án. AgentSpace lưu quyết định, kết quả, nhiệm vụ, bằng chứng và hướng làm tiếp trong các file Markdown riêng trên máy.

Ứng dụng desktop giúp chọn dự án, xem lịch sử và tạo prompt; AI có công cụ đọc/ghi file được cấp quyền mới thực hiện việc tiếp quản và lưu context. Bạn quyết định thời điểm lưu.

## Ví dụ thực tế

Bạn đang thiết kế robot với ChatGPT. Khi kết thúc phiên, yêu cầu AI lưu quyết định thiết kế, kết quả đã kiểm tra và việc còn dở vào AgentSpace. Khi chuyển sang Claude hoặc một AI khác có quyền đọc file, chọn dự án robot và sao chép prompt tiếp quản. AI mới đọc hồ sơ đã lưu thay vì yêu cầu bạn kể lại mọi việc. Tin nhắn chưa lưu không được chuyển tự động.

## Trải nghiệm nhanh

Cần Git, Python 3.8+ và Tkinter.

```bash
git clone https://github.com/guwoh/agentspace.git
cd agentspace
python3 -B scripts/desktop.py
```

Ấn **Try demo**, rồi **Start project** để xem dự án robot giả lập, context, lịch sử và prompt. Không cần tài khoản AI hay kết nối DevSpace để thử giao diện. Demo nằm trong thư mục tạm, được dọn khi đóng app bình thường. Ấn **Exit demo** để quay lại.

## Bắt đầu với dự án thật

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
| Projects | Tìm kiếm, chọn dự án và sao chép prompt tiếp quản một lần bấm |
| Feature Map | Tra chức năng, đường dẫn nguồn, phụ thuộc và sinh prompt tập trung |
| Prompt Studio | Tiếp quản, lưu, tổng quan, bàn giao, cập nhật skill và dự án mới |
| Context & History | Đọc brief, context đầy đủ và snapshot |
| Skills | Tạo, sửa skill Markdown riêng |
| Connections | Mở AI client, kiểm tra executable DevSpace |
| Backup & Settings | Sao lưu/phục hồi hồ sơ văn bản, chỉnh cỡ chữ bằng nút hoặc phím tắt |
| CLI | Khởi tạo, liệt kê, kiểm tra, sinh prompt |

## Cơ chế lưu và tiếp quản

AI đọc BRIEF trước, mở CURRENT và bằng chứng liên quan khi thiếu thông tin. Khi lưu theo yêu cầu rõ ràng, AI tạo snapshot đầy đủ, cập nhật CURRENT, sinh BRIEF và đồng bộ INDEX. Không khôi phục được tin nhắn chưa từng lưu. Không để nhiều AI đồng thời ghi cùng hồ sơ.

Xem [quy trình](protocol/WORKFLOW.md), [mẫu đầy đủ](protocol/HANDOFF_TEMPLATE.md), [mẫu brief](protocol/BRIEF_TEMPLATE.md) và [ví dụ hư cấu](examples/BRIEF.md).

## Làm việc từ xa với DevSpace

Vào Connect → Open DevSpace GUI để cấu hình server DevSpace đã cài riêng, chọn thư mục, kiểm tra endpoint và kết nối AI. Xem [hướng dẫn tiếng Việt chi tiết](docs/DEVSPACE.vi.md). Khi laptop và tunnel hoạt động, có thể dùng AI client hỗ trợ trên điện thoại để làm việc từ xa.

## Định tuyến context theo chức năng

`FEATURE_MAP.md` là mục lục nhỏ đặt cạnh BRIEF, lưu ID chức năng, từ khóa, nguồn, phụ thuộc và trạng thái. AI đối chiếu phiên nguồn với INDEX, đọc đúng nguồn cần thiết; chỉ mở CURRENT/lịch sử khi thiếu hoặc cần đối chiếu. Tab Feature map hỗ trợ tìm kiếm, kiểm tra và sao chép prompt chỉ đọc. Xem [mẫu](protocol/FEATURE_MAP_TEMPLATE.md) và [hướng dẫn CLI](README.md#focused-context-routing). Chưa đo mức tiết kiệm token thực tế; kiểm tra đường dẫn không đồng nghĩa kiểm chứng nội dung.

## Dữ liệu và giới hạn

AgentSpace không tự gửi prompt, không kết nối MCP thay người dùng và không cần AI API key. AI đám mây có thể nhận dữ liệu bạn cấp quyền đọc. Giữ context thật, đường dẫn nội bộ, token, transcript và ảnh riêng ngoài checkout công khai. Gói backup không mã hóa. Xem [quy định riêng tư](docs/PRIVACY.md).

Xem [hướng dẫn desktop](docs/DESKTOP.md), [kiểm thử](docs/TESTING.md) và [hướng dẫn CLI](README.md#cli-usage). Native build, DPI nhiều màn hình và handoff giữa tài khoản vẫn cần kiểm thử thực tế.

## Đóng góp

Hoan nghênh issue và PR có bước tái hiện rõ ràng, dùng dữ liệu giả hoặc đã loại bỏ thông tin riêng. Kiểm tra danh sách file và chạy test trước khi gửi.

Giấy phép [MIT](LICENSE).
