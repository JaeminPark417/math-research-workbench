# Files

**This folder is not GitHub-backed binary storage by default.**

Keep this README as an index or explanation of the external file arrangement
chosen during setup. Store PDFs, scans, images, presentation files, and other
large or binary materials in the user's selected local or cloud drive, then
place a safe link or portable reference in the related Markdown note.

Why this is the default:

- ordinary Git handles changing binaries poorly;
- research PDFs may have licensing or sharing restrictions;
- scans and unpublished drafts may contain private material;
- a cloud-drive folder and a Git repository can conflict if they both try to
  synchronize the same working files.

Do not put passwords, access tokens, private sharing tokens, or machine-specific
credentials here. If the user deliberately chooses to version a small binary,
Codex must first explain the consequences and confirm that the file may be
shared under the repository's visibility setting.
