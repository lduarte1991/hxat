cription: Check the current API quota for the Harvard Bedrock LLM gateway — limit and remaining usage.
---

Run this command and report the results to the user:

```bash
R=$(curl -s 'https://go.apis.huit.harvard.edu/ais-bedrock-llm/apigee/quota' -H "Authorization: Bearer ${ANTHROPIC_API_KEY}" 2>/dev/null) && echo "$R" | jq -r '"API Quota — limit: \(.quota.limit) \(.quota.limit_unit)/\(.quota.interval) \(.quota.unit) | remaining: \(.remaining_limit) \(.quota.limit_unit)"' 2>/dev/null || echo "Failed to fetch quota"
```
