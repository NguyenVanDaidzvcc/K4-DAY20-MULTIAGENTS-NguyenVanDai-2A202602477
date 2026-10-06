# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin và cấu hình

| Họ tên | Mã sinh viên | Phần thực hiện |
|---|---|---|
| Nguyễn Văn Đại | 2A202602477 | Harness, subagents, skill, thực nghiệm và báo cáo; có hỗ trợ của Codex. |

Cấu hình hiện tại: LAB_MODEL=openai:gpt-4.1-mini, LAB_TEMPERATURE=0; Deep Agents 0.7.21 theo pyproject.toml, Python 3.11, Windows, .venv, không Docker. Bản ghi chưa lưu model từng lần chạy nên không xác nhận được mọi lần thử dùng cùng model. Báo cáo chính dùng 6 bản chạy learning mới nhất với recursion_limit=60; tổng ngân sách phát triển chưa được theo dõi đầy đủ. Chưa có tag freeze. Kết quả unit tests khi đóng gói nằm trong [test-results.txt](test-results.txt).

## 2. Giả thuyết và trạng thái quy trình

Các giả thuyết dưới đây được ghi sau khi đã quan sát kết quả, không phải đăng ký trước. Không tạo tag hồi tố để che khuất thứ tự thực nghiệm.

- H1 (subagents so với baseline): phân công khám phá, triển khai và kiểm tra có thể giảm bỏ sót nhưng tăng token; chưa có dữ liệu subagents để kiểm chứng.
- H2 (skills-auto so với baseline): skill có thể cải thiện check quy ước, nhưng đọc skill không bảo đảm làm đúng.
- H3 (học so với đánh giá): cải thiện learning không bảo đảm chuyển giao sang eval; chưa có so sánh eval hợp lệ sau freeze.

## 3. Làm quen Deep Agents

1. Công cụ file và shell cùng dùng sandbox; dữ liệu nằm trong workspace/.
2. Skill được khám phá qua tên/description; agent cần đọc SKILL.md. Runner đếm skills_read từ tool calls.
3. Tool task hỗ trợ giao việc; trace chính không chứa toàn bộ bước bên trong subagent. Callback cộng token qua các lần gọi model.

## 4. Đường cơ sở và phân loại lỗi

Chỉ dùng baseline learning mới. E là quy ước tổ chức; G dùng khi detail chưa đủ chứng minh nguyên nhân A–D.

| Tác vụ | Check thất bại | Nhóm | Bằng chứng trong run.json |
|---|---|---|---|
| code-learn | tests_not_modified | G | Agent sửa test gốc. |
| code-learn | rule_type_hints | E | Thiếu annotation hàm public. |
| code-learn | rule_regression_tests | E | Không đạt yêu cầu test_regressions.py. |
| code-learn | rule_changelog | E | Không đạt quy tắc ghi fix dưới Unreleased. |
| data-learn | top_region | G | Kết quả South không đúng. |
| data-learn | rule_money_in_cents | E | Tiền JSON không đúng integer cents. |
| data-learn | rule_meta_block | E | Metadata không đạt quy tắc. |
| data-learn | rule_clean_csv | E | CSV không đạt yêu cầu. |
| logs-learn | rule_service_names | E | Tên service không chuẩn hóa đúng. |
| logs-learn | rule_sorted_errors | E | Danh sách lỗi không đúng thứ tự. |
| logs-learn | rule_schema_header | E | Thiếu/sai schema_version và generated_by. |

Nhóm E chiếm 9/11 check thất bại. Skill có thể truyền đạt quy ước nhưng vẫn cần kiểm chứng đầu ra.

## 5. Điều kiện subagents

Đã định nghĩa explorer (đọc yêu cầu, không sửa), implementer (triển khai và kiểm tra), reviewer (kiểm tra độc lập). Chưa có bản chạy điều kiện subagents nên chưa có số liệu chi phí, số lần giao việc hoặc chất lượng giao việc. Không suy luận số lần giao việc bằng 0 từ việc thiếu dữ liệu.

## 6. Skill do curator sinh

Có 3 skill tự sinh, không sửa tay nội dung. Curator đã được chạy lại nhiều lần vì lỗi định dạng, quy tắc quá chung và validator từ chối; không có nhật ký đầy đủ để đếm chính xác. Việc thử vượt mức tối đa 2 lần chạy lại trong GUIDE là sai lệch quy trình cần công khai.

| Skill | Phạm vi và nhận xét |
|---|---|
| code-repair-and-conventions | Type hints, hồi quy, changelog, không sửa test gốc; code-learn vẫn trượt các mục này dù đọc skill. |
| tabular-data-and-reporting | Parse ngày, loại trùng, cent, metadata, CSV; data-learn vẫn 0/8 dù đọc skill. |
| log-triage-and-reporting | Tên service, UTC, repeats, thứ tự và schema; logs-learn đạt 9/9. |

Description bắt đầu bằng Use when, thân skill khoảng 10–12 bước. Một số ví dụ mang đặc trưng bài học; khả năng tổng quát chưa được xác nhận bằng đánh giá độc lập.

## 7. Kết quả so sánh

Nguồn: results/<condition>/<task>/run.json và trace.md. Bảng tạo bằng lab.compare.build_table; xem [table.md](table.md).

| Task | baseline | skills-auto |
|---|---|---|
| code-learn | 6/10 | 6/10 |
| data-learn | 4/8 | 0/8 |
| logs-learn | 6/9 | 9/9 |
| Mean score - learning tasks | 0.59 | 0.53 |
| Mean score - evaluation tasks | Chưa đo hợp lệ | Chưa đo hợp lệ |
| Mean tokens per run | 49,797 | 77,599 |
| Runs that read a skill | 0/3 | 3/3 |

| Điều kiện | Kỹ thuật | Quy ước | Token trung bình | Đọc skill |
|---|---:|---:|---:|---:|
| baseline | 16/18 | 0/9 | 49,797 | 0/3 |
| skills-auto | 12/18 | 3/9 | 77,599 | 3/3 |

Phân loại theo tiền tố rule_, giống check_breakdown.py. Cả sáu bản ghi có error=null và skills_modified=false; điều này không bảo đảm đầu ra đúng. Data-learn đạt 0/8 dù kết thúc bình thường. Eval baseline đã xem trước freeze không được trộn vào bảng này.

## 8. Phân tích

1. Điểm trung bình giảm từ 58.89% xuống 53.33%, tức 5.56 điểm phần trăm. Code giữ 6/10, logs tăng 6/9 lên 9/9, data giảm 4/8 xuống 0/8. Không có cơ sở kết luận skill cải thiện toàn hệ thống hoặc eval.
2. Check kỹ thuật giảm 16/18 xuống 12/18, quy ước tăng 0/9 lên 3/9. Lợi ích tập trung ở logs. Chưa biết hiệu quả với quy ước mới của eval.
3. rule_service_names ở logs chuyển fail sang pass khi đọc skill. rule_type_hints ở code vẫn fail dù skills_read=3. Đọc skill không đồng nghĩa tuân thủ.
4. Token trung bình tăng khoảng 55.83%, từ 49,797 lên 77,599. Điểm trung bình trên 1.000 token giảm từ khoảng 0.0118 xuống 0.0069. Baseline hiệu quả hơn theo thước đo này trong mẫu hiện tại; chưa đo chi phí subagents.
5. Curator chỉ lấy role=learn và dùng validate_skill để chặn định danh eval. Tuy nhiên eval đã được quan sát trước freeze và harness đã đổi; đây không phải kiểm chứng độc lập trên dữ liệu chưa thấy.
6. Các lần phát triển data-learn từng đạt 8/8 rồi giảm ở lần khác. Có thay đổi harness/skill nên không quy toàn bộ chênh lệch cho nhiễu thuần túy. Cần chạy lặp cùng cấu hình; không chọn riêng lần tốt nhất làm đại diện.

## 9. Hạn chế và tính hợp lệ

1. Chỉ 3 tác vụ học và một bản chạy chính mỗi điều kiện; độ tin cậy thống kê thấp.
2. Thiếu subagents và eval sau freeze; ma trận thực nghiệm chưa hoàn chỉnh theo GUIDE.
3. Runner thêm hướng dẫn thực thi chung và nhắc đọc skill; đây là biến thể harness, không hoàn toàn baseline gốc của giáo trình.
4. Ổ C từng đầy và agent từng chạm recursion limit. Sandbox Windows đã chuyển sang ổ dự án; pytest cần TEMP/TMP còn dung lượng.
5. Unit tests của harness không bảo đảm model tính đúng hoặc tuân thủ quy ước.
6. Thiếu tổng ngân sách và số lần curator; thứ tự freeze/eval không đúng quy trình. Không xác nhận bài tuân thủ đầy đủ rubric.

## 10. Kết luận

Skill giúp logs-learn đạt 9/9 nhưng không cải thiện code và làm data giảm điểm trong bộ chạy này. Điểm trung bình thấp hơn baseline trong khi token cao hơn. Chưa đủ bằng chứng về eval hoặc subagents. Bước tiếp theo là cố định cấu hình, kiểm tra validation và chạy lặp trên dữ liệu độc lập.

## Phụ lục

```powershell
python -m pytest tests -v
python -m lab.runner --condition baseline --tasks learn --results results-harness-v2 --recursion-limit 60
python -m lab.runner --condition skills-auto --tasks learn --results results-harness-v2 --recursion-limit 60
python -m lab.compare --results results
```

Khi đóng gói, 6 bản chạy results-harness-v2 chuyển vào results/; run.json không đổi. Bản thử cũ giữ ngoài repo trong thư mục anh em day20-submission-archive-20261006. Không đưa .env, .venv, cache và bản thử lặp lên GitHub. Không thực hiện thử thách mở rộng có đánh giá riêng.
