"""WhatsApp launching — Contacts lookup + whatsapp:// send via AppleScript."""

import re
import urllib.parse

from .applescript import run_applescript


def send_whatsapp_message(contact_name: str, message: str) -> str:
    """Look up contact in macOS Contacts, then open WhatsApp with message pre-filled."""
    safe_name = contact_name.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        f'tell application "Contacts"\n'
        f'  set matched to (every person whose name contains "{safe_name}")\n'
        f'  if (count of matched) = 0 then\n'
        f'    return "NOT_FOUND"\n'
        f'  end if\n'
        f'  set p to item 1 of matched\n'
        f'  set phoneList to phones of p\n'
        f'  if (count of phoneList) = 0 then\n'
        f'    return "NO_PHONE"\n'
        f'  end if\n'
        f'  return value of item 1 of phoneList\n'
        f'end tell\n'
    )
    try:
        result = run_applescript(script, timeout=30)
        phone = result.stdout.strip()
    except Exception as exc:
        print(f"[error] Contacts lookup: {exc}")
        return f"Couldn't look up {contact_name} in Contacts. Make sure Terminal has Contacts permission in System Settings → Privacy & Security → Contacts."

    if phone == "NOT_FOUND":
        return f"I couldn't find {contact_name} in your Contacts."
    if phone == "NO_PHONE":
        return f"{contact_name} has no phone number saved in Contacts."

    # Strip everything except digits; WhatsApp URL needs plain digits with country code
    cleaned = re.sub(r"[^\d]", "", phone)
    encoded = urllib.parse.quote(message)
    url = f"whatsapp://send?phone={cleaned}&text={encoded}"
    send_script = (
        f'open location "{url}"\n'
        f'delay 2\n'
        f'tell application "System Events"\n'
        f'  tell process "WhatsApp"\n'
        f'    keystroke return\n'
        f'  end tell\n'
        f'end tell\n'
    )
    try:
        result = run_applescript(send_script, timeout=15)
        if result.returncode != 0:
            if "1002" in result.stderr or "not allowed to send keystrokes" in result.stderr:
                return "I need Accessibility permission to send keystrokes. Go to System Settings → Privacy & Security → Accessibility and enable Terminal."
            print(f"[error] WhatsApp send: {result.stderr.strip()}")
            return f"Couldn't send message to {contact_name}."
        return f"Message sent to {contact_name}."
    except Exception as exc:
        print(f"[error] WhatsApp send: {exc}")
        return f"Couldn't send message to {contact_name}."
