# Jarvis AI Assistant - Architecture Design

## Goal
Build a modular personal AI assistant that you can control from your Android phone to manage your home Windows PC, coordinate AI tools (Cursor, Claude Desktop, Grok, OpenCode AI), automate GUI tasks, and control your Kali VM.

## Non-Goals (for now)
- Unattended risky actions without confirmation
- Automated pentesting/exploitation (only authorized defensive use)
- Multi-user access (single owner only)

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MOBILE (Android)                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Telegram   │    │     PWA     │    │   Voice     │         │
│  │    Bot      │    │  (Phase 2)  │    │  (Phase 4)  │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │   CONNECTIVITY  │
                    │   (Tailscale)   │
                    └────────┬────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                     HOME PC (Windows 11)                        │
│                            │                                    │
│                   ┌────────▼────────┐                          │
│                   │   HOME AGENT    │                          │
│                   │   (FastAPI)     │                          │
│                   └────────┬────────┘                          │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         │                  │                  │                │
│  ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐          │
│  │   MODULE    │   │   MODULE    │   │   MODULE    │          │
│  │  REGISTRY   │   │  DISPATCHER │   │  AUDIT LOG  │          │
│  └──────┬──────┘   └──────┬──────┘   └─────────────┘          │
│         │                  │                                    │
│  ┌──────┴──────────────────┴──────────────────┐                │
│  │              EXECUTION MODULES              │                │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ │                │
│  │  │ Chrome │ │ Cursor │ │ Claude │ │ Kali │ │                │
│  │  │ Module │ │ Module │ │ Module │ │ SSH  │ │                │
│  │  └────────┘ └────────┘ └────────┘ └──────┘ │                │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ │                │
│  │  │Outlook │ │ Grok   │ │OpenCode│ │ Win  │ │                │
│  │  │ Module │ │ Module │ │ Module │ │ Apps │ │                │
│  └──┴────────┴─┴────────┴─┴────────┴─┴──────┴─┘                │
│                            │                                    │
│                   ┌────────▼────────┐                          │
│                   │  GUI AUTOMATION │                          │
│                   │    DRIVER       │                          │
│                   │ (UIA + pyauto)  │                          │
│                   └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Connectivity Options

### Option 1: Tailscale (RECOMMENDED)
**What it is:** A mesh VPN that creates a private network between your devices.

**Pros:**
- Free tier (up to 100 devices)
- No port forwarding needed (works through NAT)
- Works on Android + Windows
- Encrypted, secure
- Easy setup (install app, login, done)

**Cons:**
- Requires Tailscale account
- Both devices need Tailscale installed

**How it works:** Install Tailscale on your phone and PC. They get private IP addresses (like 100.x.x.x). Your phone can reach your PC directly.

---

### Option 2: Cloudflare Tunnel
**What it is:** Exposes your home server to the internet via Cloudflare's network.

**Pros:**
- No port forwarding needed
- Free tier available
- HTTPS by default
- Works from anywhere (no VPN app needed on phone)

**Cons:**
- Traffic goes through Cloudflare (third party)
- Requires Cloudflare account
- Slightly more complex setup
- Your server is technically "public" (protected by auth)

**How it works:** Install cloudflared on your PC. It creates an outbound tunnel to Cloudflare. You get a URL like `jarvis.yourdomain.com` that routes to your home PC.

---

### Option 3: SSH Port Forward
**What it is:** Traditional SSH tunnel through a cloud server.

**Pros:**
- Maximum control
- No third-party services
- Very secure

**Cons:**
- Requires a cloud server (small cost)
- Manual setup of port forwarding
- More technical to maintain

**How it works:** Rent a small VPS, set up SSH reverse tunnel from home PC to VPS, connect from phone to VPS.

---

### My Recommendation
**Start with Tailscale** because:
1. Easiest setup for your situation (NAT router, no port forwarding)
2. Free
3. Works great on Android
4. Most secure (no public exposure)

We can always switch later if needed.

---

## Mobile Interface Options

### Option 1: Keep Telegram (RECOMMENDED for MVP)
**Pros:**
- Already working!
- Native Android notifications
- Works offline (queues messages)
- Voice messages built-in

**Cons:**
- Limited UI (text-based)
- Telegram is a third party

**Verdict:** Keep for MVP, it's already proven.

---

### Option 2: PWA (Progressive Web App)
**Pros:**
- Custom UI (buttons, dashboards, live screenshots)
- Works on any device
- Can be "installed" on Android home screen
- No app store needed

**Cons:**
- Need to build it
- Requires connectivity to work

**Verdict:** Add in Phase 2 for richer UI.

---

### Option 3: Native Android App
**Pros:**
- Best performance
- Full device integration
- Background services

**Cons:**
- Most work to build
- Need to maintain separately

**Verdict:** Phase 3+ if needed. Can wrap PWA in a native shell (Capacitor).

---

## Module System Design

Each module is a plugin that can be added/removed. Structure:

```python
class ModuleBase:
    name: str                    # "chrome", "cursor", "kali"
    capabilities: list[str]      # ["chrome.navigate", "chrome.screenshot"]
    
    def execute(self, action: str, params: dict) -> Result:
        """Execute an action and return result"""
        pass
    
    def get_state(self) -> dict:
        """Return current state (is app open, what's visible, etc.)"""
        pass
```

### Planned Modules

| Module | Priority | Integration Method |
|--------|----------|-------------------|
| Windows Apps | P0 | subprocess + UIA |
| Chrome | P0 | Playwright (DOM access) |
| Screenshot | P0 | pyautogui |
| Cursor | P1 | CLI + filesystem + GUI fallback |
| Kali VM | P1 | SSH (not GUI) |
| Claude Desktop | P2 | UIA + OCR |
| Grok | P2 | API if available, else UIA |
| OpenCode AI | P2 | CLI/API if available |
| Outlook | P2 | COM API or UIA |
| Voice | P3 | Whisper for STT |

---

## AI Agent Coordination ("Supreme Manager")

The manager doesn't directly control AI tools. Instead:

1. **Manager creates task spec:**
   ```
   Task: "Create a Python script that fetches weather data"
   Target: Cursor
   Steps: 
     1. Open project folder
     2. Create new file weather.py
     3. Write code (delegate to Cursor AI)
     4. Run tests
     5. Commit if tests pass
   ```

2. **Module executes using best method:**
   - Cursor: Use filesystem + git + CLI (stable)
   - Only use GUI automation when necessary

3. **Manager verifies outcome:**
   - Check if file exists
   - Check if tests passed
   - Take screenshot as evidence

This approach is more reliable than trying to "puppet" the AI tools.

---

## Security Features

1. **Device pairing:** First device to connect becomes owner
2. **Action allowlist:** Only pre-approved actions can run
3. **Confirmation for dangerous actions:** Delete, send email, run scripts
4. **Audit log:** Every action logged with timestamp
5. **Panic button:** Instantly disable remote control
6. **No secrets in logs:** Passwords/tokens never logged

---

## Development Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Refactor current Telegram bot into modular architecture
- [ ] Create Home Agent (FastAPI server)
- [ ] Implement core modules: Windows Apps, Screenshot, Chrome
- [ ] Add proper logging and error handling
- [ ] Set up Tailscale connectivity

**MVP Done When:** You can send a Telegram command, it executes on your PC, and you get a screenshot back.

### Phase 2: Enhanced Control (Week 3-4)
- [ ] Add PWA interface with dashboard
- [ ] Implement Cursor module (filesystem + CLI)
- [ ] Implement Kali module (SSH)
- [ ] Add action confirmation system
- [ ] Improve state reporting (what's open, what's happening)

### Phase 3: AI Coordination (Week 5-6)
- [ ] Add Claude Desktop module
- [ ] Add Grok module
- [ ] Add OpenCode AI module
- [ ] Implement task planning/coordination
- [ ] Add project tracking

### Phase 4: Polish (Week 7+)
- [ ] Voice control (Whisper STT)
- [ ] Better error recovery
- [ ] Performance optimization
- [ ] Native Android wrapper (optional)

---

## Questions Before We Start

1. **Connectivity:** Are you okay with installing Tailscale on both your phone and PC?

2. **Authentication:** Currently your bot uses "first user wins." Do you want stronger auth (password, 2FA)?

3. **AI Tools:** Which of these have CLI/API access on your system?
   - Cursor: Has CLI (`cursor` command)?
   - Claude Desktop: Any API?
   - Grok: Web only or local?
   - OpenCode AI: CLI available?

4. **Kali VM:** Is SSH enabled in your Kali VM? What's the IP/hostname?

5. **Project deployment:** When you say "deploy projects," where do you deploy to? (GitHub, Vercel, your own server?)

6. **Running as service:** Should the Home Agent run automatically when Windows starts? (Affects some permissions)

---

## Next Steps

Once you confirm the architecture:

1. I'll refactor your existing code into the modular structure
2. Set up the Home Agent (FastAPI)
3. Create the first modules (Windows Apps, Screenshot, Chrome)
4. Help you install Tailscale
5. Test end-to-end: Phone → Tailscale → Home Agent → Execute → Screenshot back

Let me know your answers to the questions above and we can start building!
