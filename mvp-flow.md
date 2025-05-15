# MVP Flow Test Script

This document outlines a basic way to manually test the MVP content-digest flow.

---

## ✅ Goal

Send a URL or PDF via email → Agent processes it → Summary returned by email.

---

## 📨 Step 1: Simulate Incoming Email (POST to Gateway)

```bash
curl -X POST http://localhost:8000/api/v1/gateway/email   -H "Content-Type: application/json"   -d '{
    "from": "ariel@example.com",
    "to": "digest@bluelabel.ai",
    "subject": "Summarize this please",
    "body": "https://www.example.com/article-to-process"
  }'
```

Expected response:
```json
{ "status": "queued", "task_id": "task_xyz" }
```

---

## 🧠 Step 2: Agent Processing

This step is automatic once events are routed.

Monitor logs:

```bash
docker logs -f bluelabel_agent_runner
```

---

## 📬 Step 3: Output via Digest Agent

- Summary is sent via the same email thread.
- Alternatively, poll: `GET /digests/{user_id}`

---

## 🔁 Troubleshooting

- Redis must be running
- Logs: `/logs/agent.log`
- Status: `GET /tasks/{task_id}`
