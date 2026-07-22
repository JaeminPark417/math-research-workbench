# 문제 해결

지금 보이는 증상과 같은 항목부터 읽으세요. 오류 메시지를 Codex에 붙여 넣을 수
있지만, 먼저 사람 이름, 비공개 경로, 로그인 정보, 기밀 연구 내용을 지우세요.

## 폴더를 열었는데 아무 일도 일어나지 않습니다

정상입니다. 폴더를 여는 것만으로는 메시지가 전송되지 않습니다. Codex 채팅에
다음을 보내세요.

```text
초기 설정을 시작해줘
```

또는 `$first-run`을 실행해도 됩니다.

## Codex가 잘못된 폴더라고 말합니다

`AGENTS.md`, `README.md`, `meta/`, `.agents/`가 바로 들어 있는 폴더를 여세요.
ZIP 압축을 풀면 이름이 비슷한 폴더가 두 겹으로 생길 때가 있습니다. 그 파일들이
들어 있는 안쪽 폴더를 선택하면 됩니다.

## Codex가 읽기는 하지만 수정하지 못합니다

로컬 폴더를 열었는지, 앱에 그 폴더 접근 권한이 있는지 확인하세요. 작업 폴더를
신뢰하거나 workspace 접근을 허용하기 전까지 Codex가 읽기 전용으로 시작할 수
있습니다. 허용하기 전에 화면에 표시된 경로를 읽으세요. workbench 폴더만으로
충분한데 사용자 홈 폴더 전체에 대한 접근 권한을 주지 마세요.

## 초기 설정에서 클라우드 환경이라고 합니다

호스팅된 checkout은 내 컴퓨터의 프로그램이나 폴더를 설정할 수 없습니다.
macOS 또는 Windows에서
[ChatGPT 데스크톱 앱](https://chatgpt.com/download/)으로 같은 workbench를
로컬에서 열고, Codex를 선택한 뒤 `초기 설정을 시작해줘`라고 보내세요. Linux에는
현재 ChatGPT 데스크톱 앱이 없으므로 Codex CLI와 터미널 기본 사용법이 필요합니다.
클라우드 작업은 그곳에 있는 Markdown을 편집할 수는 있지만, 내 컴퓨터의 초기
설정을 완료했다고 표시해서는 안 됩니다.

## 열 때마다 초기 설정이 다시 시작됩니다

Codex에게 다음과 같이 요청하세요.

```text
첫 실행 설정이 완료 상태로 유지되지 않는 이유를 진단해줘. 설정 상태와 권한만
확인하고, 비공개 경로를 출력하거나 내 답변을 바꾸지는 마.
```

흔한 원인은 쓰기 권한이 없는 폴더, 없어진 `.harness/local.yaml`, 중단된 설정,
또는 새 질문 두 개에 답해야 하는 이전 버전의 설정입니다.

## 설정 상태가 invalid, unreadable, inconsistent 또는 unsupported라고 나옵니다

초기 설정을 멈추세요. Codex는 로컬 설정 항목을 이어서 쓰거나, 덮어쓰거나,
링크를 따라가거나, 삭제해서는 안 됩니다. 연구 노트는 이 컴퓨터에서만 쓰는 설정
파일과 별개이므로 그대로 두어야 합니다.

Codex에게 다음과 같이 요청하세요.

```text
초기 설정 상태를 안전하게 복구하도록 도와줘. 값이 가려진 setup-state 결과만
사용하고, 로컬 설정 파일을 읽거나 링크를 따라가지 말아줘. 아직 아무것도 바꾸지
말고, 새 버전이 필요한지 또는 승인 후 격리 이름으로 바꿔야 하는지 설명해줘.
```

`unsupported`라면 상태 파일보다 먼저 workbench 프레임워크를 업데이트합니다. 나머지
경우에는 Codex가 정확한 로컬 설정 항목만 타임스탬프가 붙은 격리 이름으로 바꾸는
방법을 제안할 수 있습니다. 먼저 `.harness` 자체가 링크인지, `local.yaml`만 링크인지
구분하고, 링크를 따라가지 않는 정확한 이동 작업과 복구 출처를 보여준 뒤 승인을
받아야 합니다. 항목을 삭제하지 마세요. `.harness` 자체가 링크나 junction이라면 그
링크를 안전하게 격리한 뒤 새 릴리스 사본에서 공개 `.harness` 파일을 복구하고,
링크를 통과해 파일을 복사하지 마세요.

## Python 3.9 이상을 찾지 못했습니다

Python 3.9 이상은 값이 가려진 로컬 설정·검증 도우미만 실행합니다. Python을 배울 필요는
없습니다. 초기 설정은 설치를 제안하기 전에 이미 있는 명령과 Codex에 번들된
workspace 실행 환경부터 확인합니다. 둘 다 없다면 임시 텍스트 명령으로 저장된
설정 상태를 만들거나 읽지 않습니다.

저장되는 초기 설정 없이 일반 Markdown 작업을 계속하려면 `나중에`를 고르세요.
설치하려면 Codex에게 공식 <https://www.python.org/downloads/> 사용자용 설치
프로그램을 설명해 달라고 하세요. 열기·다운로드·실행에는 각각 승인이 필요합니다.
설치 뒤 workbench를 다시 열고 `초기 설정을 시작해줘`라고 보내세요.

## Claude Code가 설치되지 않거나 로그인되지 않습니다

Claude Code와 Claude는 Anthropic이 제공하는 별도 제품입니다. 선택 사항이며,
이 배포판의 검토는 Claude Pro 또는 Max의 개인 직접 로그인만 허용합니다. Team,
Enterprise, Console/API key, 클라우드 제공자, proxy, 별도 gateway는 별도로 검토된
흐름이 필요합니다. safe mode도 관리자 정책 훅을 끄지 못하므로, 관리형 정책이
감지되거나 확인할 수 없을 때도 멈춥니다.
맞는 구독이 없다면 `나중에`를 선택하세요. 평소 Codex 작업에는 지장이 없습니다.
Anthropic의 최신 공식 [설치 안내](https://code.claude.com/docs/en/installation)와
[인증 안내](https://code.claude.com/docs/en/authentication)를 확인하세요.

Claude Code 설치와 로그인 시작은 각각 별도로 승인해야 합니다. 비밀번호,
passkey, MFA, OAuth 입력 화면이 나오면 Codex는 멈추고 사용자가 직접 완료해야
합니다. 비밀 정보나 인증 코드를 채팅에 붙여 넣지 말고, 이 설정에서는
`claude setup-token`을 사용하지 마세요. 인증이 계속 실패한다면 오류 메시지에서
이름, 계정 식별자, 비공개 경로, 인증 코드를 지운 뒤 공유하세요.

값이 가려진 점검이 준비 상태라면 Codex가 사용자가 Claude를 safe mode로 열고
`/status`의 `Setting sources`만 확인하도록 안내합니다. 화면을 복사하지 마세요.
`Enterprise managed settings`가 보이거나 없다고 확인할 수 없으면 `나중에`를
선택하고 검토 자료를 보내지 않습니다.

## 로그인했는데 Claude 검토가 다시 승인을 요청합니다

정상입니다. 로그인은 Claude를 사용할 준비가 되었다는 뜻일 뿐 연구자료 전송을
허용하지 않습니다. Codex는 검토할 때마다 Anthropic이 제공자임을 밝히고, 목적을
설명하고, workspace 밖으로 나갈 정확한 파일·diff·본문을 나열한 뒤 그 한 번의
검토에 대해 승인받아야 합니다. 거절해도 Claude Code 설정을 해제할 필요가 없고
평소 작업을 계속할 수 있습니다.

## 앱 내 Browser가 보이지 않거나 ChatGPT가 다시 로그인하라고 합니다

앱 내 Browser는 지원되는 macOS 또는 Windows 데스크톱 환경에서만 사용할 수
있습니다. 제품 기능 제공 여부, 요금제, workspace 정책에 따라 보이지 않을 수
있으며 Linux에서는 사용할 수 없습니다. Browser가 없거나 이를 쓰는 호환 스킬이
설치되어 있지 않다면 `나중에`를 선택하세요. OpenAI의 공식
[Browser 안내](https://help.openai.com/en/articles/20001277-using-the-built-in-browser-in-the-chatgpt-desktop-app)를 확인하세요.

Browser는 일반 브라우저나 다른 앱의 로그인 상태와 분리된 로그인 공간(profile)을
사용하므로 ChatGPT 로그인을 새로 요구할 수 있습니다. 인증 화면에서는 Codex가
멈춰야 하며, 비밀번호, passkey, MFA 응답, OAuth 코드는 사용자가 직접 입력합니다.
Codex는 그 화면을 검사하거나 캡처하지 않습니다. 로그인은 파일 업로드나 메시지
전송을 허용하지 않습니다. 호환 스킬은 전송할 정확한 내용을 미리 보여주고 작업할
때마다 다시 승인을 받아야 합니다.

## workbench가 OneDrive, iCloud, Dropbox, Google Drive 안에 있습니다

Codex와 Obsidian에서 편집을 멈추세요. 백업을 만들고 두 프로그램을 모두 닫은
다음, workbench 전체를 동기화되지 않는 로컬 폴더로 옮깁니다. 새 위치에서 다시
열고, 저장된 경로를 바꾸기 전에 Codex에게 확인해 달라고 요청하세요. 열려 있는
workspace를 Codex가 자동으로 옮기게 하지 마세요.

원한다면 PDF만 별도의 외부 저장소 폴더에 보관하세요.

## GitHub 백업이 공개 상태입니다

출판 전 연구를 추가하거나 동기화하지 마세요. Codex에게 로그인 정보를 출력하지
말고 현재 공개 범위만 확인해 달라고 요청한 뒤, GitHub 계정 화면에서 비공개로
바꾸세요. 현재 절차는 GitHub의
[저장소 공개 범위 안내](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility)를
확인하세요.

비공개 자료가 이미 공개되었다면, 지금 비공개로 바꾸더라도 아무도 복사하지
않았다고 보장할 수 없습니다. 노출된 비밀번호나 토큰은 해당 서비스에서 폐기한 뒤
새로 발급하고, 민감한 자료라면 소속 기관의 지침을 따르세요.

GitHub는 자동 백업이 아닙니다. 변경 사항을 커밋하고 푸시해야만 온라인 사본에
나타납니다. 동기화 전에 목적지가 비공개인지와 어떤 파일이 포함되는지 확인하세요.

## 외부 저장소의 파일이 보이지 않습니다

Google Drive, Dropbox, OneDrive 프로그램이 실행 중이고 해당 파일이 이
컴퓨터에도 내려받아져 있는지 확인하세요. workbench 전체를 클라우드 동기화
폴더로 옮기지 마세요. Codex에게 저장된 외부 폴더 경로를 읽기 전용으로 확인해
달라고 요청하고, 새 하위 폴더를 만들거나 파일을 옮기기 전에는 대상 경로를
화면에서 확인하세요.

`files/`에 넣은 큰 파일은 GitHub가 백업하지 않습니다. 별도의 백업이 필요합니다.

## Obsidian이 빈 vault를 엽니다

**Open folder as vault**를 선택하고 `inbox/`, `ideas/`, `projects/`가 들어 있는
기존 workbench 최상위 폴더를 선택하세요. 그중 한 하위 폴더를 선택하거나 빈
vault를 새로 만들지 마세요. Obsidian 공식
[vault 안내](https://help.obsidian.md/vault)도 참고하세요.

## Obsidian 커뮤니티 플러그인을 설치했는데 작동하지 않습니다

설치한 플러그인은 별도로 활성화해야 합니다. **Settings → Community plugins**를
열고 설치된 플러그인의 스위치를 확인하세요. 플러그인은 한 번에 하나씩
업데이트하고, 플러그인 자체 문서가 요구할 때만 Obsidian을 다시 시작하세요.
설치 직후 문제가 생겼다면 그 플러그인부터 끄세요. Markdown 노트는 그대로 남아
있습니다.

**MRW LaTeX Delimiter Compatibility** 문제는 **Browse**에서 검색해 해결하지 마세요. Codex에게 `python3 scripts/install-bundled-obsidian-plugin.py`를 옵션 없이 실행해 달라고 하세요. `installed_current`는 번들 파일과 설치본이 같다는 뜻이고, `installed_stale`은 별도 승인을 받아 적용할 Workbench 업데이트가 있다는 뜻입니다. 활성화하거나 갱신한 뒤 Reading view, Live Preview, 수식이 있는 표 셀 안팎으로 커서를 옮길 때의 동작, Obsidian 재시작 후 동작을 확인하세요.

| 상태 또는 결과 | 의미와 안전한 다음 단계 |
| --- | --- |
| `not_installed` | 아직 아무 파일도 복사되지 않았습니다. 그대로 사용하거나 동의 기반 설치 안내로 돌아갑니다. |
| `installed_current` | 설치 파일과 이 Workbench 릴리스가 같습니다. Enable 스위치와 렌더링 테스트를 확인합니다. |
| `installed_stale` | 더 새 번들 버전이 있습니다. 변경 설명을 읽고 Obsidian을 닫은 뒤, 원할 때만 이 업데이트를 별도로 승인합니다. |
| `empty` | 이전 시도가 빈 플러그인 폴더를 남겼습니다. Codex가 정확한 작업을 보여주고 승인을 받은 뒤에만 다시 설치합니다. |
| `installed_modified` | 같은 버전의 설치 파일이 번들과 다릅니다. 덮어쓰지 말고 Codex에게 차이를 비교해 다른 복사본을 보관하도록 요청합니다. |
| `installed_newer` | 설치 플러그인이 현재 Workbench보다 새 버전입니다. Workbench를 갱신하거나 새 설치본을 보존하고, 이전 버전으로 내리지 않습니다. |
| `unsafe` 또는 `result=unsafe_path` | 링크, junction 또는 일반 파일이 아닌 항목 때문에 경로가 안전하지 않습니다. 이 플러그인 경로만 조사하고 링크를 따라 쓰지 않습니다. |
| `unrecognized`, `install_refused`, `update_refused` | 필요한 파일이 없거나 예상하지 못한 파일이 있습니다. Obsidian을 닫고 Codex에게 이 폴더 하나만 삭제 없이 목록화하도록 요청합니다. 설치 도우미가 남긴 `.main.js.mrw-*`, `.manifest.json.mrw-*` 파일은 출처를 확인하고 이동 승인을 받은 뒤에만 Git에서 제외되는 복구 폴더로 옮깁니다. |
| `invalid_bundle` 또는 `bundle_unavailable` | 선택형 원본 번들이 불완전하거나 바뀌었습니다. Workbench를 다시 받거나 안전하게 갱신하고, `main.js`만 따로 내려받지 않습니다. |
| `close_obsidian_and_retry` | Obsidian이 실행 파일을 사용 중일 가능성이 큽니다. 완전히 닫은 뒤 이미 승인한 작업만 다시 실행합니다. |

Finder와 Windows가 만드는 `.DS_Store`, `Thumbs.db`, `Desktop.ini`는 설치 도우미가 무시합니다. 그 밖의 예상하지 못한 파일은 자동으로 정리하지 않고 그대로 보존한 채 확인합니다.

인터넷에서 알 수 없는 `main.js` 파일을 내려받거나 다른 사람의
`.obsidian/plugins` 폴더를 복사하는 방식으로 문제를 해결하지 마세요.
고정된 Workbench 설치 도우미만 검토된 직접 설치 예외입니다. [플러그인 안내](obsidian-plugins.ko.md)를 따르세요.

## Obsidian에서는 수식이 보이지만 `.tex` 파일은 조판되지 않습니다

두 기능은 서로 다른 시스템입니다. Obsidian은 MathJax로 Markdown 수식을
보여 주지만, 원고를 PDF로 만들려면 Overleaf 또는 로컬 TeX 배포판이 필요합니다.
로컬 설치 없이 계속하려면 Overleaf를 선택하고, 컴퓨터에서 조판하려면 초기 설정의
로컬 TeX 항목을 다시 실행하세요.

조판 오류가 나면 Codex에게 의미 있는 첫 오류와 그 오류를 일으킨 파일·줄을
보여 달라고 요청하세요. 신뢰할 수 없는 문서를 조판하기 위해 `shell-escape`를
켜지 마세요.

## Codex가 승인을 요청합니다

승인 질문은 안전을 위한 기능입니다. 실행할 정확한 명령, 대상 폴더, 계정, 작업의
효과를 읽어 보세요. 언제든 거절하고 수동 방법이나 덜 침습적인 방법을 요청해도
됩니다.

특히 GitHub 연결, 외부 저장소에 폴더 만들기, Obsidian 또는 TeX 설치, Claude
Code 설치, Anthropic 로그인, 각 Claude 검토, Browser 로그인, 각 Browser 파일
업로드나 메시지 전송, 커뮤니티 플러그인 설치는 모두 별도의 선택입니다. 하나에
동의했다고 다른 작업까지 승인한 것은 아닙니다.

## 파일이 사라진 것 같습니다

문제가 생긴 폴더에 새 파일을 쓰지 마세요. Codex에게 Git 이력, Obsidian 파일
복구, 운영체제 휴지통, 백업을 읽기 전용으로 확인해 달라고 요청하세요. 어떤
복사본이 최신인지 알기 전에는 정리, reset, 대량 복원 명령을 실행하지 마세요.

## 민감한 연구 내용을 Codex에 보내도 될지 모르겠습니다

로컬 폴더를 열어도 Codex가 오프라인으로만 작동하는 것은 아닙니다. 답변 처리에
필요한 내용이 OpenAI로 전송될 수 있습니다. 출판 전 심사 보고서, 개인 정보,
기밀 공동 연구, 규제 대상 자료를 넣기 전에 소속 기관 정책과 계정의 데이터 제어
설정을 확인하세요. OpenAI의
[데이터 제어 안내](https://help.openai.com/en/articles/7730893-data-controls-faq)도
참고하세요. 확신이 없으면 자료를 넣지 말고 담당자에게 먼저 문의하세요.

workbench 자체의 보안 문제로 보인다면 [SECURITY.md](../SECURITY.md)를
따르세요.
