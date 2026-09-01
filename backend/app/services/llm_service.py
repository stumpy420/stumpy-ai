import json
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database import get_db_connection
from app.config import DEFAULT_SETTINGS

class LLMService:
    @staticmethod
    def get_settings(user_id: int = 1) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()

        settings = dict(DEFAULT_SETTINGS)
        for row in rows:
            try:
                settings[row["key"]] = json.loads(row["value"])
            except Exception:
                settings[row["key"]] = row["value"]
        return settings

    @staticmethod
    def construct_system_prompt(
        settings: Dict[str, Any],
        recalled_memories: List[Dict[str, Any]],
        tone_override: Optional[Dict[str, Any]] = None
    ) -> str:
        conciseness = tone_override.get("conciseness", settings.get("tone_conciseness", 50)) if tone_override else settings.get("tone_conciseness", 50)
        formality = tone_override.get("formality", settings.get("tone_formality", 40)) if tone_override else settings.get("tone_formality", 40)
        style = tone_override.get("style", settings.get("tone_style", "balanced")) if tone_override else settings.get("tone_style", "balanced")

        style_descriptions = {
            "socratic": "Guide the user by asking thought-provoking questions, helping them arrive at solutions themselves.",
            "direct": "Provide immediate, crisp, and direct answers without unnecessary preamble or fluff.",
            "balanced": "Provide helpful, well-structured, and approachable answers with clear practical examples.",
            "coach": "Act as an encouraging mentor, celebrating milestones, providing constructive critiques, and suggesting next learning steps."
        }

        conciseness_instruction = (
            "Be extremely succinct, using high-density bullet points and direct code snippets." if conciseness > 70 else
            "Provide thorough, deep explanations with comprehensive background context and nuances." if conciseness < 30 else
            "Provide balanced explanations with clear code examples where appropriate."
        )

        formality_instruction = (
            "Maintain an academic, professional, and precise tone." if formality > 70 else
            "Use a friendly, casual, and energetic tone with natural phrasing." if formality < 30 else
            "Maintain a warm, polished, and collaborative tone."
        )

        memories_text = ""
        if recalled_memories:
            memories_text = "### Learned Context & Memories About the User:\n"
            for mem in recalled_memories:
                memories_text += f"- [{mem['category'].upper()}] {mem['topic']}: {mem['content']}\n"
        else:
            memories_text = "### Learned Context:\n- No specific prior memories triggered for this query."

        system_prompt = (
            "You are Stumpy AI, a hyper-personalized, adaptive AI companion that learns and evolves with the user over time.\n\n"
            "### Core Persona Directives:\n"
            f"- Role & Tone: {style_descriptions.get(style, style_descriptions['balanced'])}\n"
            f"- Verbosity: {conciseness_instruction}\n"
            f"- Formality: {formality_instruction}\n"
            "- Continuous Adaptation: Always take the user's saved preferences, projects, and learning targets into account. Seamlessly weave in relevant past context without stating 'According to my database'.\n"
            "- Transparency: Answer accurately and helpfully.\n\n"
            f"{memories_text}\n"
        )
        return system_prompt

    @classmethod
    async def generate_response(
        cls,
        user_message: str,
        chat_history: List[Dict[str, str]],
        recalled_memories: List[Dict[str, Any]],
        tone_override: Optional[Dict[str, Any]] = None,
        user_id: int = 1
    ) -> Dict[str, Any]:
        settings = cls.get_settings(user_id)
        provider = settings.get("provider", "builtin")
        system_prompt = cls.construct_system_prompt(settings, recalled_memories, tone_override)

        if provider == "gemini" and settings.get("gemini_api_key"):
            try:
                text = await cls._call_gemini(settings, system_prompt, chat_history, user_message)
                followups = cls._generate_followups(user_message, text, recalled_memories)
                return {"message": text, "suggested_followups": followups}
            except Exception as e:
                fallback_msg = f"> *[Notice: Gemini API returned an error ({str(e)}). Switched to Stumpy Local Engine.]*\n\n"
                local_resp = cls._builtin_generate(user_message, chat_history, recalled_memories, settings, tone_override)
                return {"message": fallback_msg + local_resp["message"], "suggested_followups": local_resp["suggested_followups"]}

        elif provider == "openai" and settings.get("openai_api_key"):
            try:
                text = await cls._call_openai(settings, system_prompt, chat_history, user_message)
                followups = cls._generate_followups(user_message, text, recalled_memories)
                return {"message": text, "suggested_followups": followups}
            except Exception as e:
                fallback_msg = f"> *[Notice: OpenAI API returned an error ({str(e)}). Switched to Stumpy Local Engine.]*\n\n"
                local_resp = cls._builtin_generate(user_message, chat_history, recalled_memories, settings, tone_override)
                return {"message": fallback_msg + local_resp["message"], "suggested_followups": local_resp["suggested_followups"]}

        else:
            return cls._builtin_generate(user_message, chat_history, recalled_memories, settings, tone_override)

    @classmethod
    async def _call_gemini(cls, settings: dict, system_prompt: str, history: list, new_message: str) -> str:
        api_key = settings.get("gemini_api_key")
        model = settings.get("gemini_model", "gemini-2.0-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        contents = []
        for h in history[-8:]:
            role = "user" if h["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": h["content"]}]})
        
        contents.append({"role": "user", "parts": [{"text": new_message}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "I received your message but couldn't generate a response."

    @classmethod
    async def _call_openai(cls, settings: dict, system_prompt: str, history: list, new_message: str) -> str:
        api_key = settings.get("openai_api_key")
        model = settings.get("openai_model", "gpt-4o-mini")
        url = "https://api.openai.com/v1/chat/completions"

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-8:]:
            role = "user" if h["role"] == "user" else "assistant"
            messages.append({"role": role, "content": h["content"]})
        messages.append({"role": "user", "content": new_message})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return "No response generated."

    @classmethod
    def _builtin_generate(
        cls,
        user_message: str,
        chat_history: List[Dict[str, str]],
        recalled_memories: List[Dict[str, Any]],
        settings: Dict[str, Any],
        tone_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        msg = user_message.lower().strip()
        style = (tone_override or {}).get("style", settings.get("tone_style", "balanced"))
        conciseness = (tone_override or {}).get("conciseness", settings.get("tone_conciseness", 50))

        user_name = None
        user_role = None
        active_project = None
        preferences = []
        skills_learning = []

        for m in recalled_memories:
            top = m.get("topic", "")
            cat = m.get("category", "")
            content = m.get("content", "")
            if top == "user_name" or "name is" in content.lower():
                user_name = content.replace("User's name is ", "").rstrip(".")
            elif top == "user_role" or "role" in top:
                user_role = content.replace("User is a ", "").rstrip(".")
            elif cat == "project" or "building" in content.lower():
                active_project = content.replace("User is building: ", "").rstrip(".")
            elif cat == "preference":
                preferences.append(content)
            elif cat == "skill":
                skills_learning.append(content)

        salutation = f"Hey {user_name}!" if user_name else "Hello!"

        if any(w in msg for w in ["hello", "hi", "hey", "who are you", "what can you do"]):
            body = (
                f"{salutation} I'm **Stumpy AI**, your personal adaptive AI companion. "
                "Unlike standard chatbots, I learn your preferences, keep track of your active projects, "
                "remember your feedback, and adapt my explanations to match your pace."
            )
            if active_project:
                body += f"\n\nI see you're currently working on **{active_project}**."
            if skills_learning:
                body += f"\n\nWe're also tracking your progress on **{skills_learning[0]}** in the Skill Mastery center!"
            
            body += (
                "\n\nHere are a few things we can do together:\n"
                "- 💬 **Chat & Co-Think**: Ask questions, brainstorm architectures, or debug code.\n"
                "- 🧠 **Brain Studio**: View what I've learned about you in real-time on the Knowledge Graph.\n"
                "- 🎯 **Skill Mastery**: Take adaptive micro-quizzes to test and solidify your knowledge.\n"
                "- 📚 **Second Brain**: Store reference notes and code snippets for instant recall."
            )

        elif any(w in msg for w in ["what do you know about me", "what do you remember", "what have you learned", "my preferences", "who am i", "architecture choices"]):
            if recalled_memories:
                body = "Here is what I currently have in my active memory about you:\n\n"
                for m in recalled_memories:
                    pill = f"**[{m['category'].upper()}]**"
                    body += f"- {pill} *{m['topic'].replace('_', ' ').title()}*: {m['content']}\n"
                body += "\n💡 You can inspect, modify, or add any memory directly in the **Brain Studio** tab!"
            else:
                body = "I'm just getting started learning about you! Tell me your name, what projects you're building, or what tech stack you prefer, and I'll adapt immediately."

        elif any(w in msg for w in ["code", "rust", "python", "fastapi", "react", "golang", "javascript", "typescript", "architecture", "system design", "database", "api", "function"]):
            context_note = ""
            if preferences:
                context_note = f"\n*(Adapting to your preference: {preferences[0]})*\n"

            if "rust" in msg:
                rust_sample = (
                    "```rust\n"
                    "use std::sync::Arc;\n"
                    "use tokio::sync::mpsc;\n\n"
                    "#[derive(Debug, Clone)]\n"
                    "pub struct EventBatch {\n"
                    "    pub id: u64,\n"
                    "    pub payload: Vec<u8>,\n"
                    "}\n\n"
                    "#[tokio::main]\n"
                    "async fn main() -> Result<(), Box<dyn std::error::Error>> {\n"
                    "    let (tx, mut rx) = mpsc::channel::<EventBatch>(1000);\n"
                    "    tokio::spawn(async move {\n"
                    "        tx.send(EventBatch { id: 1, payload: vec![1, 2, 3] }).await.unwrap();\n"
                    "    });\n"
                    "    while let Some(event) = rx.recv().await {\n"
                    "        println!(\"Processing event #{}\", event.id);\n"
                    "    }\n"
                    "    Ok(())\n"
                    "}\n"
                    "```"
                )
                body = (
                    f"### Rust High-Performance Architecture\n"
                    f"{context_note}"
                    "Rust gives you zero-cost abstractions, memory safety without garbage collection, and fearless concurrency.\n\n"
                    f"{rust_sample}\n\n"
                    "**Key design considerations**:\n"
                    "1. **Ownership & Lifetimes**: Prefer `Arc<T>` or channels for async cross-thread sharing.\n"
                    "2. **Error Handling**: Use `thiserror` for library crates and `anyhow` for applications."
                )
            elif "fastapi" in msg or "python" in msg:
                python_sample = (
                    "```python\n"
                    "from fastapi import FastAPI, Depends, HTTPException\n"
                    "from pydantic import BaseModel, Field\n\n"
                    "app = FastAPI(title='High-Performance Service')\n\n"
                    "class EventPayload(BaseModel):\n"
                    "    event_id: str\n"
                    "    timestamp: int\n"
                    "    metadata: dict = Field(default_factory=dict)\n\n"
                    "@app.post('/api/v1/events')\n"
                    "async def ingest_event(payload: EventPayload):\n"
                    "    return {'status': 'ingested', 'id': payload.event_id}\n"
                    "```"
                )
                body = (
                    f"### Modern Async Python & FastAPI\n"
                    f"{context_note}"
                    "FastAPI leverages Python type hints and Pydantic v2 for high throughput and automated OpenAPI schemas.\n\n"
                    f"{python_sample}\n\n"
                    "**Performance Tips**:\n"
                    "- Use `async def` for I/O bound endpoints (database, HTTP calls).\n"
                    "- Use regular `def` with background thread pools for CPU-heavy tasks."
                )
            else:
                body = (
                    f"### Technical Solution & Architectural Overview\n"
                    f"{context_note}"
                    "Based on your requirements, here is a resilient and scalable pattern:\n\n"
                    "1. **Core Data Flow**: Decouple ingestion from compute using an asynchronous queue or buffer.\n"
                    "2. **State Management**: Keep your application services stateless and push persistence to indexed stores.\n"
                    "3. **Extensibility**: Use dependency injection and interface contracts for rapid iteration."
                )

        elif any(w in msg for w in ["learn", "study", "how to improve", "quiz", "test me"]):
            body = (
                f"{salutation} Active recall and spaced repetition are the most effective ways to master technical skills!\n\n"
                "I can dynamically generate micro-quizzes tailored to your current level in the **🎯 Skill Mastery** tab. "
                "Every question you complete updates your mastery score and helps me pinpoint areas where you need more practice."
            )

        else:
            recalled_context_str = ""
            if recalled_memories:
                top_mem = recalled_memories[0]
                recalled_context_str = f"*(Bearing in mind your {top_mem['topic'].replace('_', ' ')}: {top_mem['content']})*\n\n"

            body = (
                f"{salutation}\n\n"
                f"{recalled_context_str}"
                f"I've received your thought: *\"{user_message}\"*\n\n"
                "I am continuously synthesizing what you share to make future recommendations, answers, and quizzes sharper and more relevant to your goals.\n\n"
                "How would you like to proceed with this?"
            )

        if conciseness > 75 and len(body) > 300:
            lines = [l for l in body.split("\n") if l.strip() and not l.startswith("I am continuously")]
            body = "\n".join(lines[:6])

        followups = cls._generate_followups(user_message, body, recalled_memories)
        return {"message": body, "suggested_followups": followups}

    @staticmethod
    def _generate_followups(user_message: str, response_text: str, memories: List[dict]) -> List[str]:
        msg = user_message.lower()
        if "rust" in msg:
            return ["How should I handle async error propagation in Tokio?", "Can you generate a quiz on Rust ownership?", "How do I optimize memory layouts?"]
        elif "fastapi" in msg or "python" in msg:
            return ["How do I integrate background tasks in FastAPI?", "What's the best way to handle DB connection pooling?", "Generate a Python async quiz!"]
        elif "remember" in msg or "what do you know" in msg:
            return ["Show me the interactive Knowledge Graph", "How do I edit or delete a memory?", "Teach Stumpy AI a new preference"]
        elif "project" in msg or "build" in msg:
            return ["What architecture pattern do you recommend?", "Add a note to my Second Brain", "Create a new learning milestone"]
        else:
            return ["Tell me what you've learned about my stack", "Generate a quick knowledge quiz", "Help me design my next feature"]
