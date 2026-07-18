# ChatGPT sign-in in the in-app Browser

Use this reference only for an optional skill that explicitly consumes ChatGPT
through the supported desktop app's built-in Browser. Do not treat the Codex
workspace's own account session as proof that the Browser profile is signed in.

Use the official Browser guide as the source of truth:
<https://help.openai.com/en/articles/20001277-using-the-built-in-browser-in-the-chatgpt-desktop-app>.

## Gate the offer

Offer `yes` only when all of these conditions hold:

1. The user is running a supported OpenAI desktop app on macOS or Windows that
   exposes the built-in Browser to the current Codex workspace.
2. The Browser control is visibly available in the current app and workspace.
3. An installed consumer skill explicitly says that it uses this in-app
   Browser to access ChatGPT and includes per-use data-transfer approval.

Available features can depend on the user's plan and workspace policy. Linux is
not a supported built-in Browser platform. This release intentionally includes
no ChatGPT Browser consumer skill, so recommend `later` unless a compatible
skill has subsequently been installed. Do not open a login page merely to make
setup look complete.

## Explain the boundary

- State that the in-app Browser has its own browsing state and does not reuse
  the user's normal Chrome profile or signed-in session.
- State that signing in only prepares that browser profile. It does not upload
  repository files and does not approve any future message, attachment,
  download, or transfer.
- State that a future consumer skill may send separately approved content to
  OpenAI under the active ChatGPT account's data controls and workspace policy.
- Ask the user to verify the active account and institutional policy before
  using confidential, regulated, referee, student, patient, or unpublished
  restricted material.

## Protect the credential screen

1. After the gates above pass and the user asks to continue, tell the user how
   to open the built-in Browser themselves and navigate to
   `https://chatgpt.com`. Do not navigate there with a Browser-control tool;
   the first page can already contain an account selector or identifier.
2. Hand over the whole navigation and authentication interval to the user.
   From before navigation until the user says the flow is finished, do not call
   Browser inspection or automation tools, take screenshots, inspect the DOM,
   or read visible page text.
3. Tell the user to enter passwords, passkeys, MFA values, OAuth codes, and
   recovery information only in the Browser, never in chat.
4. Ask the user to return only after every credential or account-selection
   screen is gone. Ask them to confirm only that they can see the ordinary new
   chat input rather than a sign-in prompt; do not ask for an account name,
   screenshot, or copied page text.

Do not independently open or inspect the account menu, profile, settings,
plan, workspace selector, chat list, page DOM, cookies, local storage, session
identifiers, or browser history as a setup-time readiness check. The user's
minimal confirmation is the readiness check for this optional login step.

Record `chatgpt_browser.choice: "yes"` only when the desktop capability,
compatible consumer skill, user confirmation, and non-sensitive readiness
check all succeed at setup time. On Linux, with a missing Browser control, with
no compatible consumer, or after an incomplete login, offer `later` or `no`.

Treat `yes` as a setup preference, not persistent proof of authentication.
Before every consumer-skill use, recheck the capability and login live, show
the exact data and action proposed for OpenAI, and obtain new approval. Pause
again under the same credential-screen protocol if login has expired.
