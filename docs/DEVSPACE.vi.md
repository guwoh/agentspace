# Hướng dẫn kết nối AgentSpace với DevSpace

[English](DEVSPACE.md) · [DevSpace upstream](https://github.com/Waishnav/devspace/blob/main/docs/setup.md)

**AgentSpace** quản lý bộ nhớ dự án, skill và prompt. **DevSpace** là MCP server độc lập cho phép AI được cấp quyền đọc/sửa file và chạy công cụ trên máy. AgentSpace tích hợp GUI hỗ trợ cấu hình DevSpace, không đóng gói server, không tự tạo tunnel và không tự kết nối tài khoản.

## Bước 1 — Cài trên laptop

Cần Git, Bash, Python 3.8+ có Tkinter và Node/npm tương thích DevSpace. Tại thời điểm kiểm tra, upstream yêu cầu Node >=22.19 và <27; xem [hướng dẫn chính thức](https://github.com/Waishnav/devspace/blob/main/docs/setup.md) nếu có thay đổi. Trên Ubuntu, cài python3-tk nếu thiếu. Windows dùng hướng dẫn Git Bash/WSL của upstream; nút khởi động lại bằng systemd chỉ dành cho Linux.

```bash
git clone https://github.com/guwoh/agentspace.git
cd agentspace
python3 scripts/agentspace.py init ~/work/agentspace-private
npm install -g @waishnav/devspace
devspace init
devspace doctor
```

Trong setup DevSpace, chọn dùng MCP host, cấp quyền cho thư mục AgentSpace riêng và các dự án cần dùng. Không chọn cả thư mục home nếu không cần. Không chạy server bằng root. Nếu đã có DevSpace, kiểm tra cấu hình trước khi thay đổi.

## Bước 2 — Tạo kết nối HTTPS

Dùng tunnel do bạn quản lý, ví dụ [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) hoặc [Tailscale Funnel](https://tailscale.com/kb/1223/funnel), trỏ vào port DevSpace đã cấu hình (thường 7676). Làm theo tài liệu nhà cung cấp. Không tắt OAuth, không mở trực tiếp port không cần thiết. URL tunnel tạm có thể thay đổi.

Chạy server trong terminal nếu chưa có tiến trình chạy:

```bash
devspace serve
```

Giữ server và tunnel hoạt động. Nếu đã cấu hình user service Linux, có thể xem `systemctl --user status devspace.service`. GUI không tự cài systemd service. Nếu chạy foreground, dừng và khởi động lại thủ công sau khi lưu cấu hình.

## Bước 3 — Dùng DevSpace GUI

Mở AgentSpace:

```bash
python3 -B scripts/desktop.py --workspace ~/work/agentspace-private
```

Vào **Connect → Open DevSpace GUI**. Hoặc mở trực tiếp bằng `python3 -B scripts/devspace_gui.py`. Trên Windows dùng `python` và chọn đường dẫn riêng phù hợp.

1. Nhập URL HTTPS của tunnel, có thể kèm /mcp.
2. Thêm thư mục AgentSpace và project cần truy cập; bỏ thư mục không cần.
3. Bấm **Lưu cấu hình** và xác nhận. Bản sao cấu hình được lưu local, không đưa lên Git.
4. Nếu dùng Linux user service đã có, bấm **Khởi động lại (systemd)** và xác nhận. Không restart giữa lúc AI đang chạy task. Nếu chạy bằng terminal thì tự restart.
5. Bấm **Kiểm tra kết nối**. HTTP 401 có challenge Bearer/OAuth có thể là trạng thái bình thường trước xác thực; chưa phải kết nối thành công.
6. Chọn ChatGPT hoặc Claude, **Sao chép URL MCP**, rồi **Mở thiết lập**.
7. Chỉ dùng **Sao chép mật khẩu** khi cần dán vào đúng trang Owner approval của DevSpace. Không gửi qua chat hoặc chụp màn hình chứa mật khẩu. GUI cố xóa clipboard sau 60 giây khi vẫn đang chạy, nhưng clipboard manager vẫn có thể lưu lịch sử.

## Bước 4 — Thiết lập tài khoản AI

Trên web của ChatGPT hoặc Claude, mở phần quản lý plugin/app/connector, thêm custom MCP server, dán URL và chọn OAuth nếu có. Claude thường nằm ở Settings/Customize → Connectors → Add custom connector. Tên menu và khả năng sử dụng phụ thuộc tài khoản, phiên bản client; đối chiếu tài liệu upstream. Xác nhận trang Owner approval đúng domain của tunnel của mình, duyệt quyền cần thiết. Không giả định tất cả gói/tài khoản hoặc app điện thoại hỗ trợ custom MCP.

## Bước 5 — Thử tiếp quản

Trong AgentSpace chọn project → Copy resume prompt. Dán vào cuộc chat đã bật DevSpace. Yêu cầu AI đọc AGENTS.md, INDEX, BRIEF và Feature Map của đúng dự án, báo trạng thái nhưng không sửa gì. Thử trên dự án giả lập trước. Nếu sử dụng Try demo, thư mục tạm chỉ tồn tại khi app đang chạy.

Sau khi làm việc, yêu cầu save context rõ ràng. Khi chuyển sang chat/AI khác đã cấp quyền, gửi prompt tiếp quản mới. Chỉ hồ sơ đã lưu được chuyển tiếp, không tự lấy toàn bộ lịch sử chat.

## Bước 6 — Làm việc từ điện thoại

Laptop phải bật, không sleep, có mạng; server và tunnel còn hoạt động. Thiết lập connector trên web được hỗ trợ trước. Trên điện thoại đăng nhập tài khoản AI đã được cấp quyền, mở chat và bật DevSpace nếu client có hỗ trợ. Thử yêu cầu đọc trạng thái trước khi sửa code. Nếu app mobile không có connector, dùng client web tương thích. Không cần cài AgentSpace trên điện thoại để dùng quy trình này.

## Xử lý lỗi

| Vấn đề | Kiểm tra |
|---|---|
| Không thấy devspace | Kiểm tra Node/npm, PATH và cài đặt upstream |
| Không đọc cấu hình | Chạy devspace init rồi Nạp lại |
| Local không phản hồi | Kiểm tra server và port bằng devspace doctor |
| HTTPS không phản hồi | Kiểm tra tunnel, URL, port đích |
| OAuth/callback lỗi | URL cấu hình phải khớp URL public đang hoạt động; kết nối lại connector cũ nếu cần |
| AI không thấy project | Kiểm tra quyền thư mục và đường dẫn project; không mở toàn bộ máy |
| Điện thoại không có connector | Dùng web/client hỗ trợ custom MCP |

**An toàn:** DevSpace thực thi lệnh với quyền người dùng local; allowed roots không phải sandbox shell. Dữ liệu AI đọc có thể đi vào cuộc hội thoại cloud. Thu hẹp quyền, kiểm tra yêu cầu thao tác, thu hồi kết nối không dùng và tắt tunnel khi không cần. Không publish config, auth.json, backup cấu hình hay token.

GUI đi kèm đã được phát triển từ bản Linux DevSpace 1.0.8. Chưa xác minh schema mọi phiên bản mới hơn, GUI Windows/macOS, tunnel mới và kết nối điện thoại thực tế của người dùng mới. Server DevSpace là dự án độc lập, cài riêng.
