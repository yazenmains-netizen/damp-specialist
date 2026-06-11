import modal

app = modal.App("damp-specialist")

image = (
    modal.Image.debian_slim()
    .pip_install("fastapi", "httpx")
)

SPREADSHEET_SCRIPT_URL = "YOUR_APPS_SCRIPT_URL"  # replaced in Step 2 below
TO_EMAIL = "yazenmains@gmail.com"


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("damp-specialist-secrets")],
)
@modal.asgi_app()
def web():
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import os, smtplib, httpx
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from datetime import datetime

    fastapi_app = FastAPI()
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @fastapi_app.post("/submit")
    async def submit(request: Request):
        body         = await request.json()
        name         = body.get("from_name", "")
        email        = body.get("from_email", "")
        phone        = body.get("phone", "")
        postcode     = body.get("postcode", "")
        submitted_at = datetime.now().strftime("%d/%m/%Y %H:%M")

        # ── Email notification ───────────────────────────────────────────
        gmail_password = os.environ["GMAIL_APP_PASSWORD"]
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"New Survey Lead — {name} · {postcode}"
        msg["From"]    = TO_EMAIL
        msg["To"]      = TO_EMAIL

        html_body = f"""
        <div style="font-family:sans-serif;max-width:520px;margin:0 auto">
          <div style="background:#0d1f3c;padding:20px 24px;border-radius:8px 8px 0 0">
            <h2 style="color:#fff;margin:0;font-size:1.15rem">New Survey Request — Damp Specialist</h2>
          </div>
          <div style="background:#f7f8fa;padding:24px;border:1px solid #dde1e8;border-radius:0 0 8px 8px">
            <table style="width:100%;border-collapse:collapse">
              <tr><td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;font-weight:700;width:35%;color:#0d1f3c">Name</td>
                  <td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;color:#4f5e73">{name}</td></tr>
              <tr><td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;font-weight:700;color:#0d1f3c">Email</td>
                  <td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;color:#4f5e73">{email}</td></tr>
              <tr><td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;font-weight:700;color:#0d1f3c">Phone</td>
                  <td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;color:#4f5e73">{phone}</td></tr>
              <tr><td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;font-weight:700;color:#0d1f3c">Postcode</td>
                  <td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;color:#4f5e73">{postcode}</td></tr>
              <tr><td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;font-weight:700;color:#0d1f3c">Submitted</td>
                  <td style="padding:10px 14px;border:1px solid #dde1e8;background:#fff;color:#4f5e73">{submitted_at}</td></tr>
            </table>
          </div>
        </div>
        """

        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(TO_EMAIL, gmail_password)
            server.sendmail(TO_EMAIL, TO_EMAIL, msg.as_string())

        # ── Add row to Google Sheet via Apps Script ──────────────────────
        httpx.post(SPREADSHEET_SCRIPT_URL, json={
            "date": submitted_at,
            "name": name,
            "email": email,
            "phone": phone,
            "postcode": postcode,
        }, timeout=10)

        return JSONResponse({"status": "ok"})

    return fastapi_app
