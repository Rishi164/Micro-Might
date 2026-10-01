import asyncio
import ipaddress
import logging
import os
import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ["EMERGENT_EMAIL_KEY"]
EMAIL_FROM_NAME = os.environ["EMAIL_FROM_NAME"]
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")
OWNER_EMAIL = os.environ["OWNER_EMAIL"]
APP_URL = os.environ["APP_URL"].rstrip("/")

_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "reply with the code", "send your password", "cvv", "send us your password", "enter your password below", "confirm your card number", "your full card number", "seed phrase", "recovery phrase", "verify your card", "social security number", "confirm your bank details")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == shortener or host.endswith("." + shortener) for shortener in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags: set[str] = set()
        self.urls: list[str] = []
        self.anchors: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [value for key, value in attrs if key.lower() in ("href", "src") and value]
        if tag.lower() == "a":
            self._href = dict((key.lower(), value) for key, value in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan()
    scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email")
    body = f"{subject}\n{html}".lower()
    for phrase in _CRED_ASK:
        if phrase in body:
            raise ValueError("Email contains prohibited credential language")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError("Email links must use absolute HTTPS URLs")
        parsed = urlparse(low)
        host = parsed.hostname or ""
        if not _host_ok(host) or parsed.username is not None:
            raise ValueError("Email contains an unsafe URL")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for match in _HOSTISH.finditer(text):
            if not _same_site(match.group(1).lower(), real):
                raise ValueError("Email link text does not match its destination")


async def send_email(*, to: str, subject: str, html: str) -> str | None:
    _assert_safe_email(subject, html)
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if EMAIL_REPLY_TO:
        payload["contact_email"] = EMAIL_REPLY_TO
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{EMAIL_BASE_URL}/api/v1/email/send",
            headers={"X-Email-Key": EMAIL_KEY},
            json=payload,
        )
    response.raise_for_status()
    return response.json().get("id")


def _order_rows(order: dict) -> str:
    return "".join(
        f'<tr><td style="padding:8px 0;border-bottom:1px solid #e5e3db">{escape(item["name"])} — {escape(item["variety"])}<br><span style="color:#666">{escape(item["weight"])} · {escape(item["plan"].upper())} · Qty {item["quantity"]}</span></td><td style="padding:8px 0;border-bottom:1px solid #e5e3db;text-align:right">₹{item["line_total"]}</td></tr>'
        for item in order["items"]
    )


def _email_shell(content: str) -> str:
    return f'<table role="presentation" width="100%" style="background:#faf9f6"><tr><td align="center" style="padding:32px 16px"><table role="presentation" width="100%" style="max-width:620px;background:#fff;border:1px solid #e5e3db"><tr><td style="padding:32px;font-family:Arial,sans-serif;color:#143621"><p style="font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#4a7c59">Micro Might</p>{content}<p style="margin-top:28px;padding-top:20px;border-top:1px solid #e5e3db;font-size:12px;color:#777">From Our Trays To Your Plates · FSSAI Lic. No. 21226010004732<br>We never ask for passwords or card details by email.</p></td></tr></table></td></tr></table>'


async def send_new_order_notifications(order: dict) -> dict[str, str]:
    rows = _order_rows(order)
    customer_html = _email_shell(
        f'<h1 style="font-size:28px">We received order {escape(order["order_number"])}</h1>'
        f'<p>Hi {escape(order["customer_name"])}, thank you for choosing Micro Might. Your order is awaiting delivery-fee review and confirmation.</p>'
        f'<table role="presentation" width="100%">{rows}</table>'
        f'<p><strong>Current estimate: ₹{order["total"]}</strong></p>'
        f'<p>Requested delivery date: <strong>{escape(str(order.get("preferred_delivery_date") or "Not provided"))}</strong></p>'
        f'<p>Delivery is free within 5 km. Beyond 5 km, the ₹9/km delivery fee is approved by our team before confirmation.</p>'
        f'<p><a href="{APP_URL}/contact">Contact Micro Might</a></p>'
    )
    owner_html = _email_shell(
        f'<h1 style="font-size:28px">New order {escape(order["order_number"])}</h1>'
        f'<p><strong>{escape(order["customer_name"])}</strong><br>{escape(order["customer_email"])} · {escape(order["customer_phone"])}</p>'
        f'<p>{escape(order["delivery_address"])}, {escape(order["pincode"])}</p>'
        f'<table role="presentation" width="100%">{rows}</table>'
        f'<p><strong>Estimated total: ₹{order["total"]}</strong> · {escape(order["payment_method"].upper())}</p>'
        f'<p>Customer requested delivery: <strong>{escape(str(order.get("preferred_delivery_date") or "Not provided"))}</strong></p>'
        f'<p><a href="{APP_URL}/admin">Review this order in the admin dashboard</a></p>'
    )
    results = await asyncio.gather(
        send_email(to=order["customer_email"], subject=f"Micro Might order {order['order_number']} received", html=customer_html),
        send_email(to=OWNER_EMAIL, subject=f"New Micro Might order {order['order_number']}", html=owner_html),
        return_exceptions=True,
    )
    return {
        "customer": "sent" if not isinstance(results[0], Exception) else "failed",
        "owner": "sent" if not isinstance(results[1], Exception) else "failed",
    }


async def send_order_status_notification(order: dict) -> str:
    status_label = "confirmed" if order["status"] == "confirmed" else "cancelled"
    content = _email_shell(
        f'<h1 style="font-size:28px">Order {escape(order["order_number"])} is {status_label}</h1>'
        f'<p>Hi {escape(order["customer_name"])}, your Micro Might order has been {status_label}.</p>'
        f'<p><strong>Final total: ₹{order["total"]}</strong><br>Approved delivery fee: ₹{order.get("approved_delivery_fee") or 0}</p>'
        f'<p>Harvest date: <strong>{escape(str(order.get("approved_harvest_date") or "To be confirmed"))}</strong><br>Delivery date: <strong>{escape(str(order.get("approved_delivery_date") or "To be confirmed"))}</strong></p>'
        f'<p><a href="{APP_URL}/contact">Contact Micro Might</a> if you have a question about this update.</p>'
    )
    await send_email(to=order["customer_email"], subject=f"Micro Might order {order['order_number']} {status_label}", html=content)
    return "sent"