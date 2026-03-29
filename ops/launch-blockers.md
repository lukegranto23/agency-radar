# Launch Blockers

## What Is Already Done

- product and report engine
- public-ready static pages under `docs/`
- five generated niche reports
- prospect sheets across the niche catalog
- draft outreach sequences for federal IT and federal cyber
- public sample contacts in [`data/sample_contacts.csv`](../data/sample_contacts.csv)

Real outreach lists should live under `data/private/`, which is gitignored.

## What Still Blocks Revenue

Only two things now require user-owned identity:

1. a public URL
2. a sender identity

Without those, I can keep building assets but I still cannot collect money or send live outreach.

## Minimal Inputs Needed

### Option A: GitHub publish path

- user runs `gh auth login` on this machine
- or sends a GitHub personal access token with repo scope

That lets me:

- create the remote repo
- push `agency-radar`
- turn `docs/` into a public Pages site

### Option B: Hugging Face publish path

- user runs `hf auth login`
- or sends an `HF_TOKEN`

That lets me:

- install the `hf` CLI
- create a Space
- upload the static site or a lightweight app wrapper

### Sender path

Provide one of:

- a Gmail account the user is willing to send from through OAuth/app password
- a domain inbox with SMTP credentials
- a transactional provider key such as Resend, Postmark, or SendGrid

With one sender path, I can turn the prepared pitch files into actual outbound mail.

## Honest Constraint

The repo is no longer the main blocker. Identity, publishing, and payment rails are.
