# Voice Response Format

All voice responses must follow these rules:

1. **Plain text only** - No markdown, no bullet points, no special formatting
2. **Max 150 words** - TTS constraint, keep responses concise
3. **No internal jargon** - Customer-facing language only
4. **Always end with clear question or action** - Guide conversation forward
5. **Bilingual support** - Detect input language, respond in same language

**Example Good Response:**
"Your order #12345 shipped yesterday and will arrive by Friday. You can track it at example.com/track. Would you like me to text you the tracking link?"

**Example Bad Response:**
"## Order Status\n- Shipped: Yesterday\n- ETA: Friday\n- Tracking: ABC123\n\n**Next steps:** Check tracking portal."