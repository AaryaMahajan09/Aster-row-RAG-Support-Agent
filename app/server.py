import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

from app.agent import SupportAgent

# Global Agent Instance
AGENT = None


def get_agent():
    global AGENT
    if AGENT is None:
        knowledge_base_path = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge-base")
        orders_path = os.getenv("ORDERS_PATH", "data/orders.json")
        AGENT = SupportAgent(
            knowledge_base_path=knowledge_base_path,
            orders_path=orders_path
        )
    return AGENT


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aster & Row — Support Assistant</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0B0F17;
            --bg-surface: #141B26;
            --bg-surface-elevated: #1D2635;
            --primary: #10B981;
            --primary-hover: #059669;
            --primary-glow: rgba(16, 185, 129, 0.2);
            --accent: #38BDF8;
            --accent-glow: rgba(56, 189, 248, 0.15);
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --border: rgba(255, 255, 255, 0.08);
            --border-highlight: rgba(16, 185, 129, 0.3);
            --card-radius: 16px;
            --badge-bg: rgba(56, 189, 248, 0.12);
            --badge-text: #7DD3FC;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Ambient Glow Background */
        .ambient-glow {
            position: fixed;
            top: -20%;
            left: 50%;
            transform: translateX(-50%);
            width: 800px;
            height: 500px;
            background: radial-gradient(circle, var(--primary-glow) 0%, var(--accent-glow) 40%, transparent 70%);
            filter: blur(80px);
            pointer-events: none;
            z-index: 0;
        }

        /* Header */
        header {
            position: relative;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 28px;
            background: rgba(20, 27, 38, 0.7);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-icon {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, #10B981, #0284C7);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
            color: white;
            box-shadow: 0 4px 14px var(--primary-glow);
        }

        .brand-info h1 {
            font-size: 17px;
            font-weight: 600;
            letter-spacing: -0.3px;
        }

        .brand-info p {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 500;
            color: #34D399;
            background: rgba(16, 185, 129, 0.1);
            padding: 6px 12px;
            border-radius: 20px;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .status-dot {
            width: 7px;
            height: 7px;
            background-color: #10B981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10B981;
        }

        /* Chat Container */
        .chat-container {
            position: relative;
            z-index: 1;
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            padding: 20px;
            overflow: hidden;
        }

        .messages-list {
            flex: 1;
            overflow-y: auto;
            padding-right: 8px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            scroll-behavior: smooth;
        }

        .messages-list::-webkit-scrollbar {
            width: 6px;
        }

        .messages-list::-webkit-scrollbar-thumb {
            background: var(--bg-surface-elevated);
            border-radius: 3px;
        }

        /* Message Bubbles */
        .message-row {
            display: flex;
            gap: 12px;
            animation: fadeIn 0.25s ease-out forwards;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message-row.user {
            justify-content: flex-end;
        }

        .avatar {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 600;
            flex-shrink: 0;
        }

        .avatar.agent {
            background: linear-gradient(135deg, #10B981, #0284C7);
            color: white;
        }

        .avatar.user {
            background: #334155;
            color: #CBD5E1;
        }

        .message-bubble {
            max-width: 78%;
            padding: 14px 18px;
            border-radius: 14px;
            font-size: 14.5px;
            line-height: 1.6;
        }

        .message-row.agent .message-bubble {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-top-left-radius: 4px;
            color: var(--text-primary);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .message-row.user .message-bubble {
            background: linear-gradient(135deg, #10B981, #059669);
            color: white;
            border-top-right-radius: 4px;
            box-shadow: 0 4px 14px var(--primary-glow);
        }

        /* Source Badges */
        .sources-card {
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .sources-title {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
        }

        .sources-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }

        .source-tag {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 11.5px;
            font-weight: 500;
            padding: 3px 8px;
            border-radius: 6px;
            background: var(--badge-bg);
            color: var(--badge-text);
            border: 1px solid rgba(56, 189, 248, 0.2);
        }

        .source-tag.order {
            background: rgba(16, 185, 129, 0.12);
            color: #6EE7B7;
            border-color: rgba(16, 185, 129, 0.25);
        }

        /* Suggestions Chips */
        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 10px 0;
        }

        .chip {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
        }

        .chip:hover {
            background: var(--bg-surface-elevated);
            color: var(--text-primary);
            border-color: var(--border-highlight);
            transform: translateY(-1px);
        }

        /* Input Bar */
        .input-bar-container {
            padding-top: 10px;
        }

        .input-bar {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 6px 8px 6px 16px;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .input-bar:focus-within {
            border-color: #10B981;
            box-shadow: 0 0 0 3px var(--primary-glow);
        }

        .input-bar input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text-primary);
            font-size: 14.5px;
            font-family: inherit;
        }

        .input-bar input::placeholder {
            color: var(--text-muted);
        }

        .send-btn {
            background: #10B981;
            color: white;
            border: none;
            outline: none;
            padding: 10px 18px;
            border-radius: 10px;
            font-size: 13.5px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.15s ease;
        }

        .send-btn:hover:not(:disabled) {
            background: #059669;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Typing Dots */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 4px 0;
        }

        .dot {
            width: 6px;
            height: 6px;
            background-color: var(--text-muted);
            border-radius: 50%;
            animation: pulse 1.4s infinite ease-in-out;
        }

        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes pulse {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
            40% { transform: scale(1); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="ambient-glow"></div>

    <header>
        <div class="brand">
            <div class="brand-icon">A&R</div>
            <div class="brand-info">
                <h1>Aster & Row Support</h1>
                <p>Grounded Customer Assistant</p>
            </div>
        </div>
    </header>

    <div class="chat-container">
        <div class="messages-list" id="messagesList">
            <!-- Welcome message -->
            <div class="message-row agent">
                <div class="avatar agent">AI</div>
                <div class="message-bubble">
                    Hello! I'm the Aster & Row customer support assistant. I can help with return policies, product care guidelines, international shipping questions, or track your orders.
                </div>
            </div>
        </div>

        <div class="suggestions">
            <button class="chip" onclick="askPreset('What is the standard return window?')">Return window?</button>
            <button class="chip" onclick="askPreset('Where is ORD-1007 and when should it arrive?')">Track ORD-1007</button>
            <button class="chip" onclick="askPreset('Do you ship to Canada and how long does it take?')">Shipping to Canada?</button>
            <button class="chip" onclick="askPreset('Can I put the Breeze Tumbler in the dishwasher?')">Breeze Tumbler care?</button>
            <button class="chip" onclick="askPreset('When will ORD-1004 arrive?')">Status of ORD-1004</button>
        </div>

        <div class="input-bar-container">
            <form class="input-bar" id="chatForm" onsubmit="handleSubmit(event)">
                <input 
                    type="text" 
                    id="userInput" 
                    placeholder="Ask a question or enter order ID (e.g. ORD-1007)..." 
                    autocomplete="off" 
                />
                <button type="submit" class="send-btn" id="sendBtn">
                    Send
                </button>
            </form>
        </div>
    </div>

    <script>
        const messagesList = document.getElementById('messagesList');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');

        function appendMessage(role, text, sources = []) {
            const row = document.createElement('div');
            row.className = `message-row ${role}`;

            const avatar = document.createElement('div');
            avatar.className = `avatar ${role}`;
            avatar.textContent = role === 'agent' ? 'AI' : 'You';

            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            
            // Format text with paragraph breaks
            const formatted = text.replace(/\\n/g, '<br/>');
            bubble.innerHTML = `<div>${formatted}</div>`;

            // Append sources if present
            if (sources && sources.length > 0) {
                const sourcesCard = document.createElement('div');
                sourcesCard.className = 'sources-card';
                
                const title = document.createElement('div');
                title.className = 'sources-title';
                title.textContent = 'Grounded Sources';
                sourcesCard.appendChild(title);

                const badges = document.createElement('div');
                badges.className = 'sources-badges';
                
                sources.forEach(src => {
                    const tag = document.createElement('span');
                    tag.className = `source-tag ${src.toLowerCase().includes('order') ? 'order' : ''}`;
                    tag.textContent = src;
                    badges.appendChild(tag);
                });

                sourcesCard.appendChild(badges);
                bubble.appendChild(sourcesCard);
            }

            if (role === 'agent') {
                row.appendChild(avatar);
                row.appendChild(bubble);
            } else {
                row.appendChild(bubble);
                row.appendChild(avatar);
            }

            messagesList.appendChild(row);
            messagesList.scrollTop = messagesList.scrollHeight;
        }

        function showTyping() {
            const row = document.createElement('div');
            row.className = 'message-row agent';
            row.id = 'typingIndicator';

            const avatar = document.createElement('div');
            avatar.className = 'avatar agent';
            avatar.textContent = 'AI';

            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            bubble.innerHTML = `
                <div class="typing-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            `;

            row.appendChild(avatar);
            row.appendChild(bubble);
            messagesList.appendChild(row);
            messagesList.scrollTop = messagesList.scrollHeight;
        }

        function removeTyping() {
            const typing = document.getElementById('typingIndicator');
            if (typing) typing.remove();
        }

        function askPreset(text) {
            userInput.value = text;
            handleSubmit(new Event('submit'));
        }

        async function handleSubmit(event) {
            event.preventDefault();
            const query = userInput.value.trim();
            if (!query) return;

            // Display user message
            appendMessage('user', query);
            userInput.value = '';
            userInput.disabled = true;
            sendBtn.disabled = true;
            showTyping();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query })
                });

                const data = await response.json();
                removeTyping();

                if (data.error) {
                    appendMessage('agent', `Error: ${data.error}`);
                } else {
                    appendMessage('agent', data.answer, data.sources);
                }
            } catch (err) {
                removeTyping();
                appendMessage('agent', `Network error: ${err.message}`);
            } finally {
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.focus();
            }
        }
    </script>
</body>
</html>
"""


class SupportRequestHandler(BaseHTTPRequestHandler):

    def _set_json_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        if parsed.path == "/api/health":
            self._set_json_headers(200)
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/chat":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)

                query = payload.get("query", "").strip()
                if not query:
                    self._set_json_headers(400)
                    self.wfile.write(json.dumps({"error": "Empty query"}).encode("utf-8"))
                    return

                agent = get_agent()
                raw_response = agent.answer(query)

                # Parse sources if present at the end
                sources = []
                answer_text = raw_response

                if "\n\nSources:" in raw_response:
                    parts = raw_response.split("\n\nSources:")
                    answer_text = parts[0].strip()
                    source_lines = parts[1].strip().splitlines()
                    for line in source_lines:
                        cleaned = line.lstrip("- ").strip()
                        if cleaned and cleaned.lower() != "none":
                            sources.append(cleaned)

                self._set_json_headers(200)
                response_data = {
                    "answer": answer_text,
                    "sources": sources,
                    "raw": raw_response
                }
                self.wfile.write(json.dumps(response_data).encode("utf-8"))

            except Exception as error:
                self._set_json_headers(500)
                self.wfile.write(json.dumps({"error": str(error)}).encode("utf-8"))
            return

        self.send_error(404, "Not Found")


def run_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, SupportRequestHandler)
    print("=" * 60)
    print(" Aster & Row Support Agent — Web Interface")
    print(f" Running at: http://localhost:{port}")
    print(" Press Ctrl+C to stop.")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    run_server(port=port)
