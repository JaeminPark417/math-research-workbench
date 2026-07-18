# External storage reference

GitHub and cloud storage solve different problems:

- GitHub: Markdown, templates, and version history.
- External storage: PDFs, scans, slides, images, and other binaries.

Do not put the Git repository itself inside a synchronized folder. Two programs
editing `.git` can create conflict copies or corrupt history.

## Selection workflow

1. Ask whether the user already has Google Drive, Dropbox, OneDrive, or another
   synced folder installed.
2. Detect likely folders read-only. Do not assume a path exists.
3. Show the resolved folder without dumping unrelated home-directory content.
4. Propose a dedicated subfolder such as `MathResearchFiles`.
5. Create it only after approval.
6. Record provider and path only in `.harness/local.yaml`, which is Git-ignored.

If no provider is used, keep binary files under `files/`. Its contents are
ignored by Git and therefore need a separate backup chosen by the user.

## If the sync application is not installed

Do not install or sign in automatically. Explain that an external provider is
optional and offer `local-only` or `later` first. If the user wants a provider,
use its current official download and setup guide, show the exact application
and destination, and obtain separate approval before running an installer or
opening an account flow:

- Google Drive for desktop: <https://support.google.com/drive/answer/10838124>
- Dropbox desktop application: <https://help.dropbox.com/installs/download-dropbox>
- Microsoft OneDrive: <https://www.microsoft.com/microsoft-365/onedrive/download>

Never request a cloud-storage password, recovery code, cookie, or access token.
If the provider has no supported client for the operating system, recommend an
ordinary local folder with the user's existing backup method instead of an
unofficial sync tool.

## Common locations to inspect

- macOS: `~/Library/CloudStorage/`, `~/Dropbox`, and iCloud Drive.
- Windows: OneDrive environment variables and provider folders under the user
  profile.
- Linux: provider-specific mount or sync directories selected by the user.

These are hints, not guaranteed paths. Never scan an entire cloud drive during
setup. Verify only the selected directory.

## Linking files

Store a relative identifier such as `file_ref: algebra/paper.pdf` in the
relevant note. Codex combines it with the private root in local configuration
when the user asks to open or locate the file. Explain that absolute links are
machine-specific. Do not commit a username or a private absolute path into
shared notes. The relative value is a reference for Codex to resolve with local
configuration, not a directly clickable Markdown link.
