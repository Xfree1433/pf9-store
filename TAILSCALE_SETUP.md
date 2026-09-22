# Tailscale VPN Access — BRIDGR Server

Checklist for giving an external IT contractor (Lan / Tiva IT) Tailscale access to
the BRIDGR server. Tailscale is a WireGuard-based mesh VPN; the contractor's device
joins our tailnet and reaches the server over a private `100.x.x.x` address.

> ⚠️ **Confirm the host first.** This branch is named for an *Azure* BRIDGR server,
> but the current docs (`BILLING.md`, `PF9-Server-Setup-Guide_1.md`) point to the
> Cloudflare-fronted host `139.94.250.128` / `ssh.plainspokenfoundrynine.com`
> (user `xfree143`). Decide which box Lan is connecting to before issuing the key —
> it changes the firewall step (see "Azure note" below).

---

## 1. Generate a pre-authorization key

Admin console → **Settings → Keys** → https://login.tailscale.com/admin/settings/keys
→ **Generate auth key…**

| Setting | Value | Why |
|---|---|---|
| Description | `Lan / Tiva IT — BRIDGR access` | Identifiable for later revocation |
| Reusable | **Off** | Single device only |
| Expiration | **1–7 days** | Short join window |
| Ephemeral | **Off** | Keep the node registered |
| Tags | `tag:tiva` | Scope ACLs to just this contractor |

Copy the key (`tskey-auth-…`) immediately — it's shown only once.

## 2. Lock it down with an ACL grant

A raw key joins as the key owner with full access. Restrict the tagged node to
**only** the BRIDGR box in the tailnet policy file (**Access Controls**):

```jsonc
"tagOwners": {
  "tag:tiva": ["<your-tailscale-login>"]
},
"acls": [
  {
    "action": "accept",
    "src":    ["tag:tiva"],
    "dst":    ["<bridgr-machine-or-100.x.x.x>:22,8080"]
  }
]
```

Adjust ports to what Lan needs: `22` (SSH), `8080` (nginx → store), plus the
internal gunicorn/app port if he needs it directly.

## 3. Install Tailscale on the BRIDGR server (if not already)

If the server isn't on the tailnet yet, Lan (or you) runs on the box:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# then note its Tailscale IP:
tailscale ip -4
```

## 4. Lan joins from his machine

```bash
# Linux
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --authkey tskey-auth-xxxxxxxxxxxx
```

Windows/macOS: install the Tailscale app, then `tailscale up --authkey …`.

## 5. Verify & revoke

- Confirm Lan's node appears in the admin console **Machines** list.
- Test he can reach the server: `ssh xfree143@<bridgr-100.x.x.x>`.
- **Revoke the key** from the Keys page once his device is connected (it's
  single-use, but revoke to be safe).

---

## Security notes

- **Send the key over a secure channel** — 1Password/Bitwarden Send or Signal,
  never plain email or Slack.
- Treat the auth key like a password. Set the short expiry; revoke after use.
- The `tag:tiva` ACL is what actually limits blast radius — don't skip step 2.

## Azure note

If BRIDGR is on an **Azure VM**, also allow Tailscale through the VM's Network
Security Group:

- Outbound **UDP 41641** (direct WireGuard); Tailscale falls back to DERP relay
  over HTTPS/443 if blocked, so direct UDP is a performance nicety, not strictly
  required.
- No inbound public ports are needed — Tailscale connects outbound, like the
  Cloudflare Tunnel does on the current host.
