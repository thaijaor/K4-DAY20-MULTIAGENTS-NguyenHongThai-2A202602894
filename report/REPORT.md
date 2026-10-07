# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin sinh viên và cấu hình

- Họ tên: Nguyễn Hồng Thái
- Mã sinh viên: 2A202602894

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `google_genai:gemini-3.5-flash-lite` (Google AI Studio); `LAB_TEMPERATURE=0` nhưng model dùng sampling cố định nên bỏ qua `temperature` (cảnh báo của `langchain-google-genai`); `recursion_limit=60` (mặc định).
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents 0.7.21`; máy chủ Windows 11, mọi lệnh (pytest, runner, curator) chạy trong Docker (`python:3.12-slim`, image từ `Dockerfile` của kho).
- Số lần chạy tác vụ đã dùng / ngân sách: 32 lần chạy tác vụ (gợi ý 30) + 3 lần gọi curator; 10 lần là chạy lại do lỗi (xem mục 7). Endpoint: Google AI Studio cho mọi lần chạy đến khi hết quota miễn phí 500 request/ngày; 10 lần chạy chính thức còn lại dùng cùng model `gemini-3.5-flash-lite` qua Vertex AI (`GOOGLE_GENAI_USE_VERTEXAI=true`, service account).
- Commit của tag `freeze`: `c757b79` (commit `hypotheses`: `04a7ee7`).

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): trên tác vụ đánh giá, `subagents` có điểm bằng `baseline` (±1 check) nhưng tốn khoảng 3 lần token. Căn cứ: ở tác vụ học hai điều kiện cùng 18/27, mọi lỗi thuộc nhóm E; giao việc không thêm được quy ước mà chính tác tử chính không biết; chi phí khớp mức tăng token của đa tác tử do Anthropic ghi nhận.
- H2 (skills-auto so với baseline): `skills-auto` không vượt `baseline` quá 1 check quy ước trên tác vụ đánh giá; check kỹ thuật giữ nguyên. Căn cứ: ở Phần 3.4 tác tử đọc 3/3 skill nhưng đạt 0 check `rule_` thêm, vì skill bỏ mất tên và giá trị cụ thể của quy ước; SkillsBench ghi nhận skill do mô hình tự sinh trung bình không có lợi.
- H3 (tác vụ học so với tác vụ đánh giá): ở cả ba điều kiện, check kỹ thuật gần như đạt hết trên cả hai vai trò, còn check quy ước gần 0. Quy ước mới chỉ có ở tác vụ đánh giá sẽ thất bại ở mọi điều kiện, vì không có phản hồi để học; không kỳ vọng thấy khoảng cách học/đánh giá do skill, vì skill chưa cải thiện được cả tác vụ học (SkillEvolBench: lợi ích trên tác vụ học thường không chuyển sang tác vụ mới).

## 3. Làm quen Deep Agents (Phần 0.3)

1. 9 công cụ: tệp `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`; shell `execute`; subagent `task`. Chỉ `execute` chạy được lệnh.
2. `general-purpose` dùng cho nghiên cứu, tìm kiếm và tác vụ nhiều bước, "has access to all tools as the main agent". Mỗi lần gọi là stateless: subagent chỉ thấy prompt mà tác tử chính gửi, không thấy hội thoại, và trả về một báo cáo cuối.
3. `task`: "Put full detail in the prompt and state exactly what it should return". `execute`: "Use read_file rather than cat/head/tail". Câu "Use absolute paths and avoid `cd`" của `execute` mâu thuẫn với quy ước đường dẫn tương đối trong `BASE_PROMPT`.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | `rule_type_hints` | E | "every public function ... has type annotations on all parameters and on the return value" |
| code-learn | `rule_regression_tests` | E | "add tests/test_regressions.py with one test function per bug you fixed (at least 3)" |
| code-learn | `rule_changelog` | E | "record each fix in CHANGELOG.md under the heading '## Unreleased'" |
| data-learn | `rule_money_in_cents` | E | "money values in answer.json are integer cents" |
| data-learn | `rule_meta_block` | E | "answer.json has an object `meta` = {source, rows_in, rows_used}" |
| data-learn | `rule_clean_csv` | E | "write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents" |
| logs-learn | `rule_service_names` | E | "service names ... lower-case with '-' replaced by '_'" |
| logs-learn | `rule_sorted_errors` | E | "`errors` is sorted by service, then by timestamp_utc" |
| logs-learn | `rule_schema_header` | E | "top-level object has \"schema_version\": 2 and \"generated_by\"" |

Nhận xét: 9/9 check thất bại thuộc nhóm E; điều kiện `subagents` thất bại đúng 9 check này. Bằng chứng phủ định cho A-D (`check_breakdown.py`): check kỹ thuật đạt 18/18 ở cả `baseline` lẫn `subagents`, check quy ước đạt 0/9. Không có F: câu trả lời cuối chỉ nêu tệp có thật. Nguyên nhân chung: quy ước của Acme không có trong đề, nên tác tử không thể biết dù đọc kỹ README. Skill phòng ngừa được nhóm này trên tác vụ cùng loại, vì `detail` phát biểu trọn quy tắc, nhưng không giúp được quy ước mới chỉ có ở tác vụ đánh giá.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế): `explorer` (đọc đặc tả, mã, dữ liệu; không sửa), `implementer` (sửa và chạy kiểm chứng), `reviewer` (kiểm tra độc lập; không sửa). Tách đọc / làm / kiểm để nhắm vào nhóm lỗi A và B.
- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0): code-learn 10 (explorer 3, general-purpose 5, implementer 1, reviewer 1); data-learn 1 (explorer); logs-learn 2 (implementer). Không tác vụ nào bằng 0. Tác tử chính vẫn hay chọn `general-purpose` mặc định cho việc vặt như chạy pytest hay đọc README.
- Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc): lời giao việc chép lại yêu cầu của đề khá đầy đủ (data-learn trích nguyên câu "keep one row per order_id" và các định dạng ngày; logs-learn lần 2 liệt kê đủ khóa JSON). Báo cáo của subagent có được kiểm tra: ở logs-learn, sau implementer tác tử chính `read_file` lại `errors.json` rồi giao lần 2 để sửa cấu trúc. Thông tin thiếu là quy ước Acme, nhưng tác tử chính cũng không biết quy ước này nên giao việc không thể bù được.
- Ảnh hưởng đến token và thời gian: token trung bình 461.363 so với 147.417 của `baseline` (×3,1); code-learn ×4,3 (689.264 so với 160.179), 465 s so với 56 s. Điểm không đổi (18/27 cả hai điều kiện).

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do: 3 lần. Lần 1 và 2 không ghi skill nào do lỗi của harness: Gemini trả `content` dạng danh sách khối nội dung nên `parse_skill_blocks` không tìm thấy khối; đã sửa `curate_skills` đọc `.text` (commit "Curator: read reply text"). Lần 3 sinh 3 skill hợp lệ, không xóa skill nào, không chạy lại thêm.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `enforce-code-quality-rules` | Tổng quát quá mức: mỗi dòng ứng với một check `rule_` của code-learn nhưng bỏ mất tên tệp `tests/test_regressions.py`, tiêu đề `## Unreleased` và mẫu `- fix(<function name>):` mà quy ước yêu cầu. | Đúng nhưng không đủ: "the designated release or unreleased heading" không cho biết định dạng cụ thể. Không có chỉ dẫn gây hại. | 5 dòng, `description` nêu đúng tình huống (sửa mã, test, changelog). code-learn (lần chạy lại, `skills_read`=3) làm theo một phần: thêm `## Unreleased` vào CHANGELOG nhưng bullet không theo mẫu `fix(...)`, tạo `tests/test_regression.py` (sai tên so với `test_regressions.py`): 0/3 check quy ước. |
| `verify-data-schema-and-rules` | Tổng quát quá mức: nhắc tiền theo cent, `meta`, CSV sạch nhưng thiếu tên `clean.csv`, khóa `rows_in`/`rows_used`, header và định dạng thời gian. | Đúng về hướng; "convert ... to integer cents" là quy tắc thật. Thiếu thông tin nên tác tử không áp dụng được. | 5 dòng, `description` rộng (mọi tác vụ xử lý dữ liệu). data-learn đọc nhưng vẫn đạt 0/3 check quy ước. |
| `adhere-to-output-naming-and-sorting-rules` | Gần với logs-learn nhất: nêu đúng cách chuẩn hóa tên service và thứ tự sắp xếp, nhưng thiếu `schema_version: 2` và `generated_by`. | Đúng; câu 1 viết dạng "Review ... rules, such as ..." nên đọc như ví dụ chứ không như mệnh lệnh. | 5 dòng. logs-learn đọc skill đầu tiên rồi viết parser không đổi tên service: đọc nhưng không làm theo, 0/3 check quy ước. |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 7/10 |
| data-learn | 5/8 | 5/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 6/9 |
| code-eval | 6/11 | 7/11 | 6/11 |
| data-eval | 5/9 | 5/9 | 5/9 |
| logs-eval | 6/10 | 6/10 | 8/10 |
| **Mean score - learning tasks** | 0.66 | 0.66 | 0.66 |
| **Mean score - evaluation tasks** | 0.57 | 0.60 | 0.63 |
| **Mean tokens per run** | 149,190 | 371,173 | 206,016 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     17/18         0/12         150,962      0/3
baseline      learn    18/18         0/9          147,417      0/3
subagents     eval     18/18         0/12         280,983      0/3
subagents     learn    18/18         0/9          461,363      0/3
skills-auto   eval     17/18         2/12         214,758      3/3
skills-auto   learn    18/18         0/9          197,275      3/3
```

Lần chạy lỗi và cách xử lý (mọi lần chạy đều có `skills_modified = false`; `verify_freeze.py` báo `OK` khi chạy trong Docker):

- `GraphRecursionError` (giới hạn 60): `skills-auto` code-learn ở Phần 3.4, `baseline` code-eval, `skills-auto` code-eval. Mỗi lần chạy lại một lần cùng cấu hình; số trong bảng là lần chạy lại.
- `429 RESOURCE_EXHAUSTED` (hết quota miễn phí): `subagents` data-eval, logs-eval và cả 6 lần `skills-auto` sau đóng băng. Chạy lại trên Vertex AI, cùng model, cùng skill đã đóng băng.
- Endpoint theo lần chạy: AI Studio cho `baseline` và `subagents` trên tác vụ học, Phần 3.4, `baseline` data-eval và logs-eval, `subagents` code-eval; Vertex cho `baseline` code-eval, `subagents` data-eval và logs-eval, toàn bộ 6 lần `skills-auto` chính thức.

## 8. Phân tích

1. Tác vụ học: không điều kiện nào cải thiện (0,66 cả ba; từng tác vụ trùng điểm). Tác vụ đánh giá: `subagents` 0,60 và `skills-auto` 0,63 so với 0,57 của `baseline`, tức +1 check (code-eval) và +2 check (logs-eval). Không có điều kiện nào cải thiện tác vụ học mà không cải thiện tác vụ đánh giá, nên không thấy dấu hiệu quá khớp; ngược lại, mức tăng ở tác vụ đánh giá có cỡ bằng nhiễu (câu 6) nên chưa đủ kết luận.
2. Check kỹ thuật gần như bão hòa ở mọi điều kiện (17-18/18 mỗi vai trò), không còn chỗ cho skill giúp. Check quy ước: `baseline` và `subagents` 0/9 (học) và 0/12 (đánh giá); `skills-auto` 0/9 và 2/12. Toàn bộ chênh lệch của `skills-auto` nằm ở logs-eval (8/10 so với 6/10); skill `adhere-to-output-naming-and-sorting-rules` là skill duy nhất nêu cụ thể một phép biến đổi (chuẩn hóa tên service, sắp xếp nhiều khóa), nên đây là ứng viên giải thích hợp lý nhất. Vì không mở `run.json` của tác vụ đánh giá (quy tắc 1), không xác định được 2 check nào đạt, cũng không kiểm chứng được quy ước mới; chỉ suy ra rằng quy ước mới không thể nằm trong skill vì curator không thấy tác vụ đánh giá.
3. Không giúp, đọc nhưng không làm theo: logs-learn ở Phần 3.4 đọc 3 skill ngay đầu vết, sau đó viết `parse_log.py` giữ nguyên tên `payment-service`; câu "Review all output field formatting rules, such as ..." đọc như gợi ý. Giúp một phần nhưng thiếu thông tin: code-learn ở Phần 3.4 thêm mục `## Unreleased` vào CHANGELOG và tạo tệp regression test (theo câu 3-4 của `enforce-code-quality-rules`), nhưng tên tệp `test_regression.py` và bullet không theo mẫu `fix(<function name>):` vì skill không nêu, nên `rule_regression_tests` và `rule_changelog` vẫn thất bại. Không có check `rule_` nào ở tác vụ học được skill giúp đạt trọn.
4. Token trung bình mỗi lần chạy: `baseline` 149.190, `skills-auto` 206.016 (×1,38), `subagents` 371.173 (×2,49; ×3,1 trên tác vụ học). Điểm đánh giá trên 100 nghìn token: `baseline` 0,38, `skills-auto` 0,31, `subagents` 0,16. `baseline` hiệu quả nhất; đa tác tử không đáng chi phí ở đây vì điểm tác vụ học không đổi và mức tăng ở tác vụ đánh giá (+1 check) nằm trong nhiễu. Chi phí thêm của `skills-auto` đến từ việc đọc cả 3 skill ở mọi lần chạy (`skills_read` = 3 kể cả skill không liên quan) và vết dài hơn.
5. Không thấy rò rỉ: `validate_skill` từ chối mọi skill nhắc định danh của tác vụ đánh giá, curator chỉ đọc lần chạy có `role == "learn"` và bỏ qua thư mục `*-eval`, và 3 skill không chứa tên tệp hay số liệu riêng của tác vụ học. Quá khớp ở mức chủ đề: mỗi skill ứng với đúng một tác vụ học (mã / dữ liệu / log), và `description` đủ rộng để kích hoạt ở mọi tác vụ, nên tác tử đọc cả ba mỗi lần. Phòng tránh: không sửa tay skill, không mở dữ liệu tác vụ đánh giá, giả thuyết commit trước tag.
6. Cùng bộ skill, Phần 3.4 so với sau đóng băng: code-learn 6/10 → 7/10 (lần 3.4 trượt `tests_not_modified`), data-learn 5/8 → 5/8, logs-learn 6/9 → 6/9; tổng 17/27 → 18/27. Ngoài ra `baseline` code-eval lần đầu (dừng vì giới hạn đệ quy) đạt 7/11, lần chạy lại 6/11. Nhiễu cỡ ±1 check mỗi tác vụ, bằng đúng mức chênh của `subagents` (+1) và gần bằng mức chênh của `skills-auto` (+2) trên tác vụ đánh giá, nên các chênh lệch trong mục 7 chưa đáng tin nếu chỉ chạy một lần.

## 9. Hạn chế và tính hợp lệ

1. Mỗi vai trò chỉ 3 tác vụ và mỗi cấu hình chạy một lần: một check bằng 3-4 điểm phần trăm điểm trung bình, cùng cỡ với nhiễu ±1 check đo được, nên mọi chênh lệch giữa điều kiện chỉ là gợi ý.
2. Nhiễu của mô hình không kiểm soát được: `gemini-3.5-flash-lite` bỏ qua `temperature=0`, và 3 lần chạy chạm giới hạn đệ quy 60 phải chạy lại, nên điểm tác vụ mã phụ thuộc cả độ dài vết.
3. Đổi endpoint giữa chừng (AI Studio sang Vertex, cùng model) do hết quota: toàn bộ `skills-auto` chính thức chạy trên Vertex còn phần lớn `baseline` chạy trên AI Studio, nên khác biệt hạ tầng lẫn vào so sánh.
4. Một mô hình nhỏ duy nhất và tác vụ do giảng viên thiết kế sẵn quy ước: check kỹ thuật đã bão hòa, nên thí nghiệm chỉ đo khả năng học quy ước, không đo được skill giúp kỹ năng kỹ thuật; kết quả có thể khác với mô hình khác.
5. Curator chạy hiệu quả một lần (hai lần đầu mất do lỗi đọc `content` dạng danh sách): chất lượng skill là một mẫu duy nhất của một quá trình ngẫu nhiên.

## 10. Kết luận

Với `gemini-3.5-flash-lite`, mọi lỗi ở tác vụ học là quy ước tổ chức (nhóm E); check kỹ thuật gần như luôn đạt. Subagent không cải thiện tác vụ học và tốn khoảng 2,5 lần token. Skill do curator sinh được đọc ở mọi lần chạy nhưng quá chung chung nên không giúp đạt check quy ước nào ở tác vụ học; mức +2 check quy ước ở tác vụ đánh giá nằm trong biên nhiễu, khớp H1-H3 và kết quả SkillsBench. Đề xuất: sửa prompt curator để giữ nguyên tên và giá trị mà quy ước yêu cầu (tên tệp, khóa JSON, mẫu bullet), rồi chạy lặp mỗi điều kiện ít nhất 3 lần để tách tác dụng khỏi nhiễu.

## Phụ lục

- Lệnh đã chạy (theo thứ tự; mọi lệnh trong Docker: `docker run --rm -v <repo>:/lab lab-deepagents ...`, thêm `-v vertex-sa.json:/secrets/vertex-sa.json:ro` khi dùng Vertex):
  1. `pytest tests` (32 passed)
  2. `python scripts/tour.py`
  3. `python -m lab.runner --condition baseline --tasks data-learn`, rồi `--tasks code-learn logs-learn`
  4. `python -m lab.runner --condition subagents --tasks learn`
  5. `python -m lab.curator` (3 lần, xem mục 6)
  6. `python -m lab.runner --condition skills-auto --tasks learn`, chạy lại code-learn; `mv results/skills-auto results/skills-auto-dev`
  7. commit `hypotheses`, `git commit --allow-empty -m "freeze skills" && git tag freeze`
  8. `python -m lab.runner --condition baseline --tasks eval`, `--condition subagents --tasks eval`, `--condition skills-auto --tasks all`; chạy lại các lần lỗi (mục 7)
  9. `python scripts/verify_freeze.py` (OK; chạy trong Docker có `git`, vì trên Windows `hash_dir` dùng dấu `\` trong đường dẫn nên hash không khớp)
  10. `python -m lab.compare > report/table.md`, `python scripts/check_breakdown.py`
- Thử thách mở rộng (nếu có): không thực hiện.
- Ghi chú khác: lần chạy `skills-auto` code-learn đầu tiên ở Phần 3.4 dừng vì `GraphRecursionError` (giới hạn 60), vết rỗng; đã chạy lại một lần cùng cấu hình (6/10, `tests_not_modified` thất bại).
