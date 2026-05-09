import json
import time
from voice_role.models.segment import TranscriptionSegment


SYSTEM_PROMPT = """你是一个专业的语音分析助手。以下是一段多人对话的文字记录，已通过说话人分离算法分成不同的说话人（用 SPEAKER_00, SPEAKER_01 等标识）。

请根据对话内容判断每个说话人的性别（male/female），并为每个说话人分配一个中文标签。

标签规则：
- 如果只有男性说话人：男一、男二...
- 如果只有女性说话人：女一、女二...
- 如果男女都有：男一、女一、男二、女二...（交替编号）

请返回纯JSON格式（不要包含markdown代码块标记）：
{
  "speakers": [
    {"speaker_id": "SPEAKER_00", "gender": "male", "label": "男一"},
    {"speaker_id": "SPEAKER_01", "gender": "female", "label": "女一"}
  ]
}"""


class LLMRefiner:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1", model: str = "deepseek-chat"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def refine(self, segments: list[TranscriptionSegment]) -> list[TranscriptionSegment]:
        if not segments:
            return segments

        # Get unique speaker IDs
        speaker_ids = list(dict.fromkeys(seg.speaker_id for seg in segments))
        if len(speaker_ids) <= 0:
            return segments

        # Build transcript with speaker labels
        transcript_lines = []
        for seg in segments:
            transcript_lines.append(f"[{seg.speaker_id}] {seg.text}")

        # Truncate if too long (~3000 char limit for context)
        transcript_text = "\n".join(transcript_lines)
        if len(transcript_text) > 4000:
            transcript_text = transcript_text[:4000] + "\n...(截断)"

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"对话记录：\n---\n{transcript_text}\n---"},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            content = response.choices[0].message.content.strip()
            # Remove possible markdown code block wrappers
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]

            speaker_map = json.loads(content)
            label_map = {}
            gender_map = {}
            for spk in speaker_map.get("speakers", []):
                sid = spk.get("speaker_id", "")
                label_map[sid] = spk.get("label", sid)
                gender_map[sid] = spk.get("gender", None)

            for seg in segments:
                if seg.speaker_id in label_map:
                    seg.speaker_label = label_map[seg.speaker_id]
                    seg.gender = gender_map.get(seg.speaker_id)

        except Exception:
            # LLM call failed — keep default labels
            pass

        return segments
