# AI Data Analyst Dashboard — Sales Analytics Portfolio

Dashboard phân tích dữ liệu bán hàng được xây dựng bằng Python, Pandas, Streamlit và Plotly. Mục tiêu là thể hiện quy trình Data Analyst: kiểm tra chất lượng dữ liệu, phân tích KPI, tìm insight, trình bày trực quan và xuất báo cáo.

## Tính năng chính

- Nạp dữ liệu CSV và nhận diện một số alias tên cột phổ biến.
- Lọc dữ liệu theo ngày/nhân viên; tổng quan KPI doanh thu, đơn hàng, AOV.
- Phân tích xu hướng doanh thu theo ngày và so sánh kỳ.
- Phân tích hiệu suất nhân viên và sản phẩm.
- Theo dõi KPI mục tiêu và tốc độ doanh thu dự kiến cuối kỳ (ngoại suy tuyến tính, cần nêu rõ giả định).
- Pareto 80/20: xếp hạng sản phẩm theo tỷ trọng và tỷ trọng lũy kế; loại doanh thu không dương khỏi cơ cấu bán hàng dương.
- Sàng lọc ngày doanh thu bất thường bằng robust z-score (MAD), dự phòng bằng IQR khi MAD bằng 0.
- Phân tích chất lượng dữ liệu, xem trước xử lý và xuất kết quả.
- Các hàm phân tích Pareto và bất thường được tách thành `analytics_core.py` để kiểm thử độc lập.

## Công nghệ

- Python 3.10+
- Streamlit
- Pandas
- Plotly
- Requests
- unittest (đi kèm Python)

## Cài đặt và chạy

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run dashboard.py
```

Mặc định dashboard mở tại `http://localhost:8501`.

## Chạy kiểm thử

```bash
python -m unittest discover -s tests -v
python -m py_compile dashboard.py analytics_core.py
```

## Định nghĩa và giới hạn phân tích

- **AOV**: doanh thu chia cho số đơn hàng trong phạm vi dữ liệu đã lọc; kết quả phụ thuộc cách nhận diện cột đơn hàng và cách dữ liệu ghi nhận đơn.
- **KPI mục tiêu**: mục tiêu là đầu vào do người dùng đặt, không phải dữ liệu thực tế.
- **Dự kiến cuối kỳ**: doanh thu hiện tại / số ngày đã quan sát × số ngày của kỳ. Đây là baseline đơn giản, không điều chỉnh mùa vụ, ngày nghỉ hoặc chiến dịch.
- **Pareto**: tính trên doanh thu dương; các khoản hoàn trả/điều chỉnh âm nên phân tích riêng.
- **Cảnh báo bất thường**: chỉ tạo danh sách cần kiểm tra, không tự kết luận sai dữ liệu hay quan hệ nhân quả. Ngày không xuất hiện trong dữ liệu không mặc định có doanh thu bằng 0.
- Kết quả phụ thuộc chất lượng dữ liệu nguồn; cần đối chiếu với hệ thống bán hàng trước khi dùng cho quyết định kinh doanh thực tế.

## Gợi ý trình bày trong phỏng vấn

1. **Business question**: Sản phẩm nào đóng góp phần lớn doanh thu? Ngày nào cần được điều tra? Doanh thu có đang chạy đủ tốc độ để đạt mục tiêu?
2. **Data preparation**: kiểm tra kiểu dữ liệu, giá trị thiếu, bản ghi trùng và các giá trị doanh thu không hợp lệ.
3. **Analysis**: so sánh kỳ, phân tích KPI, Pareto, phát hiện điểm bất thường.
4. **Insight → action**: nêu phát hiện, số liệu bằng chứng, hành động đề xuất và cách xác minh sau hành động.
5. **Limitations**: nói rõ giả định, dữ liệu thiếu và lý do cảnh báo không đồng nghĩa nguyên nhân.

## Cấu trúc

```text
.
├── dashboard.py
├── analytics_core.py
├── requirements.txt
├── README_PORTFOLIO.md
└── tests/
    └── test_analytics_core.py
```

## Lưu ý

Dữ liệu demo không nhất thiết đại diện cho dữ liệu sản xuất. Không đưa dữ liệu khách hàng nhạy cảm hoặc thông tin định danh vào repository công khai. Chưa nên khẳng định ứng dụng đã được kiểm thử end-to-end trên mọi môi trường; hãy kiểm thử lại giao diện với file CSV thực tế trước khi demo.
