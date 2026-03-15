import os
import requests

_notified_leads: set = set()


def notify_team_line(lead_summary: str) -> dict:
    """Send lead summary to the team LINE group.

    Args:
        lead_summary: Formatted text summary of the collected lead information.

    Returns:
        Dictionary with status of the notification.
    """
    lead_hash = hash(lead_summary.strip())
    if lead_hash in _notified_leads:
        print(f"[SKIP] notify_team_line — duplicate detected, already sent.")
        return {"status": "already_sent", "message": "Lead already notified. Skipped duplicate."}
    
    group_id = os.getenv("LINE_GROUP_ID")
    access_token = os.getenv("CHANNEL_ACCESS_TOKEN")

    if not group_id or group_id == "YOUR_LINE_GROUP_ID":
        print(f"[SKIP] notify_team_line — LINE_GROUP_ID not configured. Summary:\n{lead_summary}")
        return {
            "status": "skipped",
            "message": "LINE_GROUP_ID is not configured. Lead summary printed to console.",
            "lead_summary": lead_summary,
        }

    if not access_token or access_token == "YOUR_CHANNEL_ACCESS_TOKEN":
        print("[ERROR] notify_team_line — CHANNEL_ACCESS_TOKEN not configured.")
        return {
            "status": "error",
            "message": "CHANNEL_ACCESS_TOKEN is not configured.",
        }

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "to": group_id,
        "messages": [
            {
                "type": "text",
                "text": lead_summary,
            }
        ],
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            _notified_leads.add(lead_hash)
            print("[OK] notify_team_line — Lead sent to team LINE group.")
            return {"status": "success", "message": "Lead sent to team LINE group."}
        else:
            print(f"[ERROR] notify_team_line — LINE API {response.status_code}: {response.text}")
            return {
                "status": "error",
                "message": f"LINE API error: {response.status_code} {response.text}",
            }
    except Exception as e:
        print(f"[ERROR] notify_team_line — Failed to send: {str(e)}")
        return {"status": "error", "message": f"Failed to send: {str(e)}"}
