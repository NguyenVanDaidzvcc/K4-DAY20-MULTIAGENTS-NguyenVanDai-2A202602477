# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Văn Đại | 2A202602477 | Harness, subagents, self-evolving skills, thực nghiệm và báo cáo; có sử dụng Codex để hỗ trợ rà soát và cải tiến mã nguồn. |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `LAB_MODEL=openai:gpt-4.1`, `LAB_TEMPERATURE=0`, các lần chạy chính dùng `recursion_limit=40`; một số lần debug dùng `60`.
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: Deep Agents `0.7.21`, Python `3.11`, Windows, chạy trực tiếp trong `.venv`, không dùng Docker cho thực nghiệm chính.
- Số lần chạy tác vụ đã dùng / ngân sách: trong quá trình phát triển có nhiều lần rerun để xử lý recursion, rate limit và cải tiến skill; chưa theo dõi chính xác tổng ngân sách token toàn bộ quá trình. Các run cuối được dùng cho bảng so sánh lấy từ `results/`.
- Commit của tag `freeze`: chưa có thông tin commit hash trong dữ liệu hiện tại; cần điền hash sau khi chạy `git rev-parse freeze`.

Kết quả unit test cuối cùng:

```text
test_01_provided.py : 12 passed
test_02_agent.py    :  9 passed
test_03_runner.py   :  6 passed
test_04_curator.py  :  2 passed
--------------------------------
TOTAL               : 29 passed
```

Để tránh lỗi thư mục tạm của pytest trên Windows:

```powershell
New-Item -ItemType Directory -Force D:\AI\pytest-temp | Out-Null
$env:TEMP="D:\AI\pytest-temp"
$env:TMP="D:\AI\pytest-temp"
pytest tests -v --basetemp=D:\AI\pytest-temp\run
```

Kết quả cuối:

```text
29 passed
```

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): subagents có thể giảm bỏ sót nhờ tách vai trò khám phá, triển khai và kiểm tra, nhưng sẽ tốn nhiều token/tool calls hơn. Tôi kỳ vọng lợi ích rõ nhất ở tác vụ cần nhiều bước phối hợp.
- H2 (skills-auto so với baseline): skills-auto có thể cải thiện mạnh các check quy ước như schema, metadata, định dạng JSON/CSV, timezone, chuẩn hóa category và đơn vị tiền tệ vì curator học từ failure evidence của learning tasks.
- H3 (tác vụ học so với tác vụ đánh giá): điểm trên learning tasks có thể cao hơn evaluation tasks vì skill được sinh trực tiếp từ lỗi của learning; nếu learning tăng nhưng eval không tăng tương ứng thì đó là dấu hiệu overfitting hoặc khả năng tổng quát hóa còn hạn chế.

Ghi chú về quy trình: trong quá trình phát triển, một số kết quả evaluation đã được quan sát trước khi quy trình freeze hoàn thiện hoàn toàn. Vì vậy báo cáo công khai sai lệch này thay vì coi đây là preregistration tuyệt đối.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Công cụ file và shell cùng thao tác trên sandbox/workspace của task. Agent có thể đọc, ghi, chỉnh sửa file và chạy lệnh shell để hoàn thành yêu cầu.
2. Skill được khám phá qua `name` và `description`; agent cần đọc `SKILL.md` trước khi áp dụng. Runner ghi nhận việc đọc skill qua trường `skills_read`.
3. Tool `task` hỗ trợ giao việc cho subagent. Trace của agent chính không nhất thiết chứa toàn bộ bước nội bộ của subagent; runner tổng hợp token/tool usage từ quá trình thực thi.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

Chỉ sử dụng learning tasks để phân loại lỗi baseline.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | `tests_not_modified` | G | Agent từng sửa test gốc thay vì chỉ sửa implementation. |
| code-learn | `rule_type_hints` | E | Thiếu annotation ở public functions. |
| code-learn | `rule_regression_tests` | E | Không đáp ứng convention về regression tests. |
| code-learn | `rule_changelog` | E | Không đáp ứng quy tắc changelog. |
| data-learn | `top_region` | G | Kết quả vùng đứng đầu chưa đúng ở run baseline dùng để so sánh. |
| data-learn | `rule_money_in_cents` | E | Giá trị tiền trong JSON chưa dùng integer cents. |
| data-learn | `rule_meta_block` | E | Metadata chưa đúng cấu trúc yêu cầu. |
| data-learn | `rule_clean_csv` | E | Clean CSV chưa đúng schema/convention. |
| logs-learn | `rule_service_names` | E | Service name chưa chuẩn hóa. |
| logs-learn | `rule_sorted_errors` | E | Danh sách lỗi chưa đúng thứ tự. |
| logs-learn | `rule_schema_header` | E | Thiếu hoặc sai schema/header. |

Nhận xét: nhóm E (quy ước) chiếm đa số các check fail. Đây là nhóm lỗi phù hợp để phòng ngừa bằng skill vì chúng có thể được mô tả thành quy trình và checklist tái sử dụng.

Kết quả baseline learning cuối dùng trong bảng so sánh:

```text
baseline code-learn score=6/10 tokens=63946 calls=16
baseline data-learn score=4/8  tokens=29774 calls=6
baseline logs-learn score=6/9  tokens=55671 calls=8
```

Mean learning score:

```text
0.59
```

Mean tokens per run:

```text
49,797
```

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
  - `explorer`: đọc task, README/spec và file liên quan; tập trung thu thập yêu cầu, hạn chế chỉnh sửa.
  - `implementer`: thực hiện thay đổi cần thiết và tạo artifact/output.
  - `reviewer`: kiểm tra độc lập output, test và convention trước khi kết thúc.
  - Lý do thiết kế: tách luồng `khám phá → triển khai → kiểm tra` để giảm bỏ sót và tạo kiểm tra chéo.

- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0):
  - Dữ liệu ảnh hiện tại chỉ cung cấp tổng `calls`, không đủ để suy ra chính xác `subagent_calls`. Cần lấy trực tiếp trường `subagent_calls` trong từng `results/subagents/*/run.json` trước khi nộp nếu rubric yêu cầu số cụ thể.
  - Không được coi `calls` là `subagent_calls`.

- Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc):
  - Subagent cần nhận đủ task context, đường dẫn file và mục tiêu cụ thể. Nếu giao việc quá chung, reviewer/implementer có thể lặp lại khám phá của agent chính.
  - Trace chính không luôn hiển thị toàn bộ thao tác nội bộ của subagent nên việc đánh giá chất lượng handoff cần dựa trên `run.json` và trace có liên quan.

- Ảnh hưởng đến token và thời gian:

| Tác vụ eval | Điểm | Tokens | Tool calls |
|---|---:|---:|---:|
| `code-eval` | 6/11 | 69,168 | 17 |
| `data-eval` | 4/9 | 50,081 | 8 |
| `logs-eval` | 6/10 | 51,779 | 8 |

Mean evaluation score:

```text
0.53
```

Mean tokens per run:

```text
57,009
```

Kết quả cho thấy subagents có chi phí token cao hơn baseline learning mean, nhưng trong bộ kết quả hiện tại chưa có đủ `subagents *-learn` trong bảng `lab.compare` để so sánh learning một cách đầy đủ.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do:
  - Curator đã được chạy lại nhiều lần trong quá trình phát triển để xử lý skill quá chung, thiếu domain data/log, và cải thiện activation. Không có log đầy đủ để đếm chính xác số lần rerun.
  - Một số skill cũ bị xóa vì quá thiên về code hoặc không bao phủ đúng ba domain cần thiết.
  - Đây là sai lệch so với quy trình lý tưởng nếu GUIDE giới hạn số lần rerun curator; báo cáo công khai thay vì che giấu.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `code-repair-and-conventions` | Khá tổng quát cho code repair | Bao phủ spec/docstring, không sửa test gốc, regression test và convention. Tuy nhiên `code-learn` cuối giảm từ 6/10 xuống 4/10, nên hiệu quả chưa ổn định. | Description bắt đầu `Use when ...`; final skills-auto runs đều có đọc skill. |
| `tabular-data-and-reporting` | Tổng quát cho CSV/tabular | Đúng hướng cho deduplication, metadata, cleaned CSV, timestamp và money. Một run phát triển tăng `data-learn` từ 5/8 lên 7/8 sau khi `skills_read` từ 0 lên 1. Vẫn từng fail `rule_money_in_cents`. | Khoảng 10–16 bước; description kích hoạt cho CSV/tabular; final `skills_read` được ghi nhận. |
| `log-triage-and-reporting` | Tổng quát cho log analysis | Hiệu quả tốt nhất: `logs-learn` đạt 9/9 và `logs-eval` đạt 9/10. | Description kích hoạt cho multiline log, repeat marker, traceback, timestamp và structured output; final runs có đọc skill. |

Final comparison ghi:

```text
Runs that read a skill: 6/6
```

cho condition `skills-auto`.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Nội dung `report/table.md` hiện tại:

```text
| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 6/10 | - | 4/10 |
| data-learn | 4/8 | - | 7/8 |
| logs-learn | 6/9 | - | 9/9 |
| code-eval | - | 6/11 | 6/11 |
| data-eval | - | 4/9 | 3/9 |
| logs-eval | - | 6/10 | 9/10 |
| **Mean score - learning tasks** | **0.59** | **-** | **0.76** |
| **Mean score - evaluation tasks** | **-** | **0.53** | **0.59** |
| **Mean tokens per run** | **49,797** | **57,009** | **55,188** |
| **Runs that read a skill** | **0/3** | **0/3** | **6/6** |
```

Kết quả chi tiết của skills-auto:

```text
skills-auto code-learn score=4/10 tokens=70948 calls=14
skills-auto data-learn score=7/8  tokens=38926 calls=7
skills-auto logs-learn score=9/9  tokens=53948 calls=8

skills-auto code-eval  score=6/11 tokens=92234 calls=20
skills-auto data-eval  score=3/9  tokens=44069 calls=7
skills-auto logs-eval  score=9/10 tokens=30948 calls=6
```

Subagents evaluation:

```text
subagents code-eval score=6/11 tokens=69168 calls=17
subagents data-eval score=4/9  tokens=50081 calls=8
subagents logs-eval score=6/10 tokens=51779 calls=8
```

Một lần baseline evaluation hoàn chỉnh trước đó:

```text
baseline code-eval = 6/11
baseline data-eval = 5/9
baseline logs-eval = 1/10
```

Các số baseline-eval trên không được trộn trực tiếp vào bảng `lab.compare` hiện tại vì final results directory dùng để sinh bảng chưa chứa đủ ba baseline eval run tương ứng.

Kết quả `python scripts/check_breakdown.py` cần được dán nguyên vào phần này nếu rubric yêu cầu output chính xác của script.

Các run lỗi do `429 rate_limit_exceeded`, `GraphRecursionError` hoặc lỗi thư mục temp của pytest không được dùng làm kết quả cuối. Final skills-auto comparison có `skills_read=6/6`.

## 8. Phân tích

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?

   Learning mean:
   ```text
   baseline     = 0.59
   skills-auto  = 0.76
   ```
   Skills-auto tăng `+0.17`.

   Theo từng learning task:
   ```text
   code-learn: 6/10 → 4/10
   data-learn: 4/8  → 7/8
   logs-learn: 6/9  → 9/9
   ```

   Skills-auto cải thiện data và logs nhưng giảm ở code.

   Evaluation:
   ```text
   subagents    = 0.53
   skills-auto  = 0.59
   ```

   Theo task:
   ```text
   code-eval: 6/11 → 6/11
   data-eval: 4/9  → 3/9
   logs-eval: 6/10 → 9/10
   ```

   Data là ví dụ rõ về learning tăng nhưng eval không tăng: `data-learn=7/8` trong khi `data-eval=3/9`. Đây là dấu hiệu khả năng tổng quát hóa hạn chế hoặc overfitting vào convention của learning task.

2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?

   Baseline cho thấy phần lớn lỗi quan sát được thuộc nhóm `rule_`, đặc biệt ở data và logs. Skill giúp rõ nhất ở log conventions như service normalization, ordering, schema và structured output. Ở data, skill giúp `rule_meta_block` và `rule_clean_csv` trong một run 7/8 nhưng vẫn từng fail `rule_money_in_cents`. Điều này cho thấy skill có thể truyền convention đã học nhưng không bảo đảm thực hiện mọi quy tắc mới trên eval.

3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).

   - Skill giúp: ở `data-learn`, sau khi activation được cải thiện, `skills_read` tăng từ 0 lên 1 và `rule_meta_block`, `rule_clean_csv` chuyển sang PASS.
   - Skill không giúp hoàn toàn: `rule_money_in_cents` vẫn từng FAIL dù skill đã được đọc. Điều này chứng minh `skills_read > 0` không đồng nghĩa agent tuân thủ toàn bộ skill.

4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?

   Mean tokens:
   ```text
   baseline     = 49,797
   subagents    = 57,009
   skills-auto  = 55,188
   ```

   So với baseline, subagents tăng khoảng 14%, skills-auto tăng khoảng 11%. Skills-auto có learning mean cao nhất và token trung bình thấp hơn subagents. Trong mẫu hiện tại, subagents chưa thể hiện improvement đủ lớn để chứng minh chi phí bổ sung luôn đáng giá.

5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?

   Curator chỉ đọc run có `role == "learn"` và validator chặn marker liên quan eval. Skill được viết theo quy trình tổng quát thay vì hard-code expected answers. Tuy nhiên `data-learn=7/8` nhưng `data-eval=3/9` cho thấy dấu hiệu overfitting hoặc chuyển giao yếu. Ngoài ra một số evaluation result đã được nhìn thấy trong quá trình phát triển trước khi freeze hoàn chỉnh, nên evaluation không hoàn toàn blind.

6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

   Trong quá trình phát triển, `data-learn` từng có các mức `0/8`, `5/8`, `7/8`; logs cũng thay đổi giữa các lần chạy. Một phần khác biệt đến từ thay đổi harness/skill, một phần đến từ nondeterminism của model/tool-use. Vì vậy một run duy nhất có độ tin cậy hạn chế; thực nghiệm tốt hơn cần chạy nhiều lần với cấu hình cố định và báo cáo mean ± standard deviation.

## 9. Hạn chế và tính hợp lệ

1. **Số lượng task nhỏ.** Chỉ vài task cho mỗi domain nên một check PASS/FAIL có thể làm thay đổi mạnh điểm trung bình; kết luận không thể mở rộng trực tiếp sang mọi agentic system.
2. **Mỗi cấu hình chưa được lặp nhiều lần với cùng điều kiện.** Model/tool-use có nhiễu; một run duy nhất chưa đủ để ước lượng hiệu năng kỳ vọng.
3. **Quy trình phát triển thay đổi harness/skill và recursion limit.** Một số lần dùng 40, một số lần debug dùng 60; vì vậy chỉ nên so sánh các run nằm trong bộ kết quả cuối.
4. **Rate limit và lỗi hạ tầng.** Đã gặp `429 rate_limit_exceeded`, `GraphRecursionError` và lỗi thư mục temp của pytest; các run lỗi này không phản ánh trực tiếp chất lượng agent và không được dùng làm kết quả cuối.
5. **Nguy cơ overfitting skill.** Curator học trực tiếp từ failure evidence của learning tasks. Kết quả `data-learn=7/8` nhưng `data-eval=3/9` cho thấy khả năng tổng quát hóa của skill data còn hạn chế.
6. **Evaluation leakage.** Một số eval result đã được quan sát trước khi freeze hoàn thiện, nên evaluation không hoàn toàn blind.
7. **Thiếu thống kê nhiều lần chạy.** Chưa có mean/std từ nhiều seed hoặc nhiều lần lặp cho từng condition.

## 10. Kết luận

Self-evolving skills cải thiện learning mean từ `0.59` lên `0.76`, nhưng improvement không đồng đều giữa các domain. Lợi ích rõ nhất xuất hiện ở log analysis với `logs-learn=9/9` và `logs-eval=9/10`, trong khi data skill tăng learning nhưng không tổng quát tốt sang eval. Subagents đạt evaluation mean `0.53` nhưng dùng token trung bình cao hơn baseline và skills-auto. Kết quả cho thấy reusable skills hữu ích với lỗi procedural/convention-based, nhưng cần activation tốt, validation cuối và skill đủ tổng quát. Hướng cải tiến tiếp theo là freeze cấu hình trước eval, chạy nhiều lần và báo cáo mean ± standard deviation trên nhiều task độc lập hơn.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):

```powershell
.\.venv\Scripts\Activate.ps1

New-Item -ItemType Directory -Force D:\AI\pytest-temp | Out-Null
$env:TEMP="D:\AI\pytest-temp"
$env:TMP="D:\AI\pytest-temp"

pytest tests -v --basetemp=D:\AI\pytest-temp\run

python -m lab.runner --condition baseline --tasks learn --recursion-limit 40
python -m lab.runner --condition baseline --tasks eval --recursion-limit 40

python -m lab.runner --condition subagents --tasks eval --recursion-limit 40

python -m lab.curator

python -m lab.runner --condition skills-auto --tasks learn --recursion-limit 40
python -m lab.runner --condition skills-auto --tasks all --recursion-limit 40

python -m lab.compare > report\table.md
python scripts/check_breakdown.py
python scripts/verify_freeze.py
```

- Thử thách mở rộng (nếu có): không thực hiện thử thách mở rộng có đánh giá riêng.
- Ghi chú khác:
  - Không commit `.env`, `.venv`, cache hoặc API key.
  - Nếu API key đã từng xuất hiện trong ảnh/log, phải revoke key cũ và tạo key mới.
  - `report/table.md` nên được sinh lại từ final `results/` ngay trước khi nộp.
