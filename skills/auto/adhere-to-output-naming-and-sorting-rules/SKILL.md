---
name: adhere-to-output-naming-and-sorting-rules
description: Use when transforming structured logs, standardizing service names, sorting records, and constructing top-level JSON schema headers.
---
1. Review all output field formatting rules, such as transforming service identifiers (lowercasing and replacing hyphens with underscores).
2. Ensure record collections are sorted precisely by the required multi-level keys in ascending order.
3. Include all mandatory top-level schema version numbers and generator identifiers in the root JSON object.
4. Verify record structures against schema constraints to ensure no required fields or naming conventions are missed.
5. Check: Are service names normalized, error logs sorted correctly by service and timestamp, and top-level schema headers complete?
