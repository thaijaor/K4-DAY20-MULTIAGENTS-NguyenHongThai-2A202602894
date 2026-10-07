# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin sinh viên và cấu hình

- Họ tên: Nguyễn Hồng Thái
- Mã sinh viên: 2A202602894

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `google_genai:gemini-3.5-flash-lite` (Google AI Studio); `LAB_TEMPERATURE=0` nhưng model dùng sampling cố định nên bỏ qua `temperature` (cảnh báo của `langchain-google-genai`); `recursion_limit=60` (mặc định).
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents 0.7.21`; máy chủ Windows 11, mọi lệnh (pytest, runner, curator) chạy trong Docker (`python:3.12-slim`, image từ `Dockerfile` của kho).
- Số lần chạy tác vụ đã dùng / ngân sách:
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

> Dự đoán điều kiện nào đạt điểm cao nhất trên **tác vụ đánh giá** và vì sao. Nêu căn cứ từ phân loại lỗi (mục 4) và từ tài liệu tham khảo. Điền cả ba dòng; `verify_freeze.py` kiểm tra điều này.

- H1 (subagents so với baseline): trên tác vụ đánh giá, `subagents` có điểm bằng `baseline` (±1 check) nhưng tốn khoảng 3 lần token. Căn cứ: ở tác vụ học hai điều kiện cùng 18/27, mọi lỗi thuộc nhóm E; giao việc không thêm được quy ước mà chính tác tử chính không biết; chi phí khớp mức tăng token của đa tác tử do Anthropic ghi nhận.
- H2 (skills-auto so với baseline): `skills-auto` không vượt `baseline` quá 1 check quy ước trên tác vụ đánh giá; check kỹ thuật giữ nguyên. Căn cứ: ở Phần 3.4 tác tử đọc 3/3 skill nhưng đạt 0 check `rule_` thêm, vì skill bỏ mất tên và giá trị cụ thể của quy ước; SkillsBench ghi nhận skill do mô hình tự sinh trung bình không có lợi.
- H3 (tác vụ học so với tác vụ đánh giá): ở cả ba điều kiện, check kỹ thuật gần như đạt hết trên cả hai vai trò, còn check quy ước gần 0. Quy ước mới chỉ có ở tác vụ đánh giá sẽ thất bại ở mọi điều kiện, vì không có phản hồi để học; không kỳ vọng thấy khoảng cách học/đánh giá do skill, vì skill chưa cải thiện được cả tác vụ học (SkillEvolBench: lợi ích trên tác vụ học thường không chuyển sang tác vụ mới).

## 3. Làm quen Deep Agents (Phần 0.3)

1. 9 công cụ: tệp `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`; shell `execute`; subagent `task`. Chỉ `execute` chạy được lệnh.
2. `general-purpose` dùng cho nghiên cứu, tìm kiếm và tác vụ nhiều bước, "has access to all tools as the main agent". Mỗi lần gọi là stateless: subagent chỉ thấy prompt mà tác tử chính gửi, không thấy hội thoại, và trả về một báo cáo cuối.
3. `task`: "Put full detail in the prompt and state exactly what it should return". `execute`: "Use read_file rather than cat/head/tail". Câu "Use absolute paths and avoid `cd`" của `execute` mâu thuẫn với quy ước đường dẫn tương đối trong `BASE_PROMPT`.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

> Chỉ dùng tác vụ học. Mỗi dòng là một check thất bại.

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

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Bạn đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác: lần chạy `skills-auto` code-learn đầu tiên ở Phần 3.4 dừng vì `GraphRecursionError` (giới hạn 60), vết rỗng; đã chạy lại một lần cùng cấu hình (6/10, `tests_not_modified` thất bại).
