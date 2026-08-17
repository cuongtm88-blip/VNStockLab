# VNStockLab

VNStockLab là không gian phân tích kỹ thuật cổ phiếu Việt Nam. Bản MVP hiện tại chạy
hoàn toàn cục bộ, có dữ liệu demo xác định và hỗ trợ tải lên dữ liệu OHLCV dạng CSV.

## Tính năng hiện có

- Dữ liệu OHLCV thị trường Việt Nam thực qua Vnstock 4, cache 15 phút.
- Đồng bộ thành phần VN30 và bộ sàng lọc tối đa 20 mã mỗi lượt.
- Biểu đồ nến Nhật, khối lượng, SMA20 và SMA50.
- Relative Strength 20/60 phiên so với VN-Index; OBV và CMF20 để phát hiện tích lũy/phân phối.
- ADX/DMI đo sức mạnh và hướng xu hướng; Bollinger–Keltner Squeeze phát hiện nén/giải phóng.
- Kế hoạch vị thế mua gồm giá vào tham chiếu, stop-loss ATR/vùng giá, mục tiêu và Risk/Reward.
- Market Breadth gồm Advance/Decline, A/D Line, tỷ lệ mã trên SMA20/50/200 và độ rộng khối lượng.
- Strategy Lab nhiều mã trên một quỹ vốn chung, có Exploration kiểu AmiBroker và xếp hạng tín hiệu.
- Portfolio Manager theo dõi sổ mua/bán, giá vốn, PnL, tỷ trọng, rủi ro tập trung và
  gợi ý tái cơ cấu theo điểm kỹ thuật.
- Alert Center quản lý watchlist, stop/target, quét thay đổi tín hiệu/xu hướng,
  breakout/breakdown và Market Breadth với nhật ký chống lặp sự kiện.
- SQLite lưu bền giao dịch danh mục, watchlist, snapshot tín hiệu và nhật ký cảnh báo;
  có thể đổi đường dẫn bằng biến môi trường `VNSTOCKLAB_DB_PATH`.
- Backtest dùng Breadth lịch sử, Relative Strength, cấu trúc giá, toàn bộ chỉ báo/xác nhận hiện có.
- Position sizing theo rủi ro, giới hạn tỷ trọng/vị thế, lô 100, phí, thuế, trượt giá,
  stop/target, trailing ATR và thời gian nắm giữ tối đa.
- Bar Replay tiến/lùi/phát tự động, che dữ liệu tương lai, tính lại toàn bộ phân tích và
  mô phỏng lệnh khớp ở giá mở cửa nến kế tiếp; có marker mua/bán, đường giá vốn/stop/target,
  phím tắt điều khiển, chọn ngày bắt đầu và báo cáo đánh giá phiên.
- RSI, MACD và MFI để tham khảo; ATR dùng nội bộ cho vùng giá và quản trị rủi ro.
- Hỗ trợ/kháng cự theo swing và ATR; biên 20 phiên chỉ là phương án dự phòng.
- Nhận diện mẫu nến Doji, Hammer, Shooting Star, Marubozu, Engulfing,
  Morning/Evening Star, Three White Soldiers và Three Black Crows.
- Chấm độ tin cậy mẫu nến theo xu hướng, vùng giá và khối lượng xác nhận.
- Ichimoku 9/26/52 với Kumo, Tenkan, Kijun, Chikou và xác nhận khung ngày/tuần.
- Swing high/low, vùng hỗ trợ–kháng cự theo ATR, độ mạnh, breakout và đổi vai.
- Cấu trúc Dow HH/HL/LH/LL, BOS/CHoCH và xác nhận ngắn hạn–trung hạn–tuần.
- Mẫu hình hai đỉnh/đáy, vai–đầu–vai, tam giác, nền chữ nhật và breakout/retest.
- Điểm tín hiệu 0–100 theo bảy nhóm có giới hạn, không cộng trùng các tín hiệu tương quan.
- Cổng thực thi tách điểm ứng viên khỏi khuyến nghị cuối: mua chỉ khi Risk/Reward ≥1,5R,
  không có breakdown, Dow trung hạn không giảm và Breadth không tiêu cực.
- Nhập CSV với các cột `date, open, high, low, close, volume`.

## Chạy ứng dụng

Yêu cầu `uv` và Python 3.13 trở lên.

```bash
uv sync
uv run streamlit run app.py
```

Mở địa chỉ Streamlit hiển thị trong terminal, mặc định là <http://localhost:8501>.

## Triển khai Streamlit Community Cloud

Entrypoint triển khai là `streamlit_app.py`. Streamlit Community Cloud cài các gói
từ `requirements.txt`; các thông tin nhạy cảm (nếu bổ sung sau này) phải được nhập
trong phần **Secrets** của ứng dụng và không được commit vào Git.

## Kiểm tra

```bash
uv run pytest
uv run ruff check .
uv run mypy
```

## Cấu trúc

```text
app.py                       Giao diện Streamlit
vnstocklab/analysis/         Chỉ báo và bộ máy tổng hợp tín hiệu
vnstocklab/data/             Adapter dữ liệu CSV và dữ liệu demo
vnstocklab/storage.py        Repository SQLite cho dữ liệu người dùng
tests/                       Kiểm thử logic độc lập với giao diện
```

## Lộ trình gần

1. Relative Strength theo ngành khi có nguồn phân ngành ổn định.
2. Lưu chuỗi lịch sử giá trị tài sản và báo cáo hiệu suất danh mục.
3. Bộ lập lịch cảnh báo nền và kênh gửi thông báo khi có dữ liệu realtime.
4. Adapter realtime FireAnt hoặc nhà cung cấp tương đương.

## Nguyên tắc chỉ báo

- Dow và Ichimoku cùng thuộc nhóm cấu trúc giá nên tổng điểm của nhóm không vượt 20.
- SMA20/SMA50 chỉ đánh giá chất lượng xu hướng; EMA chỉ dùng nội bộ để tính MACD.
- Breakout, mẫu hình giá và mẫu nến cạnh tranh trong một nhóm kích hoạt; chỉ tín hiệu mạnh nhất
  được tính điểm.
- OBV và CMF tham gia nhóm dòng tiền tối đa 15 điểm; MFI, RSI và MACD chỉ tham khảo.
- ADX/DMI chỉ tham gia nhóm chất lượng xu hướng; Squeeze release chỉ tham gia nhóm kích hoạt.
- ATR chỉ dùng để đặt mức vô hiệu và chấm chất lượng Risk/Reward, không tự tạo tín hiệu mua.
- Market Breadth chấm tối đa 10 điểm cho toàn bộ rổ; mọi mã trong cùng lượt sàng lọc dùng chung bối cảnh.
- Điểm từ 65 trở lên nhưng không vượt cổng thực thi được ghi là `CHỜ XÁC NHẬN`, không
  được Strategy Lab xem là ứng viên vào lệnh.
- Elliott Wave và Stochastic RSI không nằm trong phạm vi triển khai hiện tại.
- Các nhóm chưa triển khai (thị trường, sức mạnh tương đối, rủi ro) giữ điểm trung lập và được
  đánh dấu rõ trên giao diện.

## Nguồn dữ liệu

Ứng dụng dùng thư viện `vnstock` và Unified UI của Vnstock 4. Chế độ khách có giới hạn
request; bộ sàng lọc vì vậy tải tuần tự, giới hạn 20 mã và cache danh sách chỉ số trong
một giờ. Nếu nguồn trực tuyến lỗi, dữ liệu demo và tải CSV vẫn hoạt động độc lập.

Việc sử dụng Vnstock chịu điều khoản giấy phép của nhà cung cấp. Hãy kiểm tra quyền sử
dụng phù hợp trước khi triển khai VNStockLab cho mục đích thương mại.

> Công cụ phục vụ nghiên cứu và giáo dục, không phải khuyến nghị đầu tư.
