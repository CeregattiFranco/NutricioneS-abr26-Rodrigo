import requests
import json
from datetime import datetime
from nutriciones.core import config, get_base_logger
from nutriciones.models.fathom import FathomCall

logger = get_base_logger("NSS-FATHOM")

class FathomClient:
    def __init__(self, api_key: str = config.FATHOM_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.fathom.ai/external/v1"
        self.headers = {"X-Api-Key": self.api_key, "Accept": "application/json"}

    def listar_chamadas(self, limit: int = 50, next_page_token: str = None) -> dict:
        url = f"{self.base_url}/meetings"
        params = {"limit": limit}
        if next_page_token: params["next_page_token"] = next_page_token
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            logger.error(f"Erro ao listar: {e}")
            return {}

    def buscar_detalhes(self, meeting_id: str) -> dict:
        url = f"{self.base_url}/meetings/{meeting_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes {meeting_id}: {e}")
            return {}

    def listar_todas_as_chamadas(self) -> list:
        all_meetings = []
        next_token = None
        while True:
            data = self.listar_chamadas(limit=100, next_page_token=next_token)
            items = data.get("items", [])
            all_meetings.extend(items)
            next_token = data.get("next_page_token")
            if not next_token: break
        return all_meetings

def map_fathom_to_model(m: dict) -> FathomCall:
    parts = m.get("invitees", [])
    def get_inv(idx):
        if idx < len(parts):
            p = parts[idx]
            email = p.get("email", "")
            return {
                "n": p.get("name", ""), "e": email, "d": email.split('@')[-1] if '@' in email else "",
                "ex": "one_or_more_external" if p.get("is_external") else "FALSO",
                "s": p.get("matched_speaker_display_name", "") or p.get("name", "")
            }
        return {"n": "", "e": "", "d": "", "ex": "FALSO", "s": ""}

    i1, i2, i3 = get_inv(0), get_inv(1), get_inv(2)
    extras = ", ".join([f"{p.get('name')} ({p.get('email')})" for p in parts[3:]]) if len(parts) > 3 else ""
    rb = m.get("recorded_by", {})
    re = rb.get("email", "")

    return FathomCall(
        title=i1["n"] or m.get("topic", "Sem Nome"),
        meeting_title=m.get("topic", ""),
        url=m.get("video_url", ""),
        share_url=m.get("share_url", ""),
        recording_id=str(m.get("id")),
        created_at=m.get("created_at", ""),
        scheduled_start_time=m.get("started_at", ""),
        scheduled_end_time=m.get("ended_at", ""),
        recording_start_time=m.get("started_at", ""),
        recording_end_time=m.get("ended_at", ""),
        calendar_invitees_domains_type="one_or_more_external" if any(p.get("is_external") for p in parts) else "internal_only",
        transcript_language=m.get("language", "pt"),
        transcript=m.get("transcript", ""),
        default_summary=m.get("summary", ""),
        action_items=str(m.get("action_items", "")),
        crm_matches="",
        recorded_by_name=rb.get("name", ""),
        recorded_by_email=re,
        recorded_by_email_domain=re.split('@')[-1] if '@' in re else "",
        recorded_by_team="",
        invitee_1_name=i1["n"],
        invitee_1_email=i1["e"],
        invitee_1_email_domain=i1["d"],
        invitee_1_is_external=i1["ex"],
        invitee_1_matched_speaker_display_name=i1["s"],
        invitee_2_name=i2["n"],
        invitee_2_email=i2["e"],
        invitee_2_email_domain=i2["d"],
        invitee_2_is_external=i2["ex"],
        invitee_2_matched_speaker_display_name=i2["s"],
        invitees_extra=extras,
        invitee_3_name=i3["n"],
        invitee_3_email=i3["e"],
        invitee_3_email_domain=i3["d"],
        invitee_3_is_external=i3["ex"],
        invitee_3_matched_speaker_display_name=i3["s"],
        summary_template_name="General",
        summary_markdown=m.get("summary", ""),
        summary_fetch_status="success",
        summary_markdown_pt_br=m.get("summary", "")
    )
