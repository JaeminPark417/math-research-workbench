# Math Research Workbench

**수학 연구자를 위한, 처음부터 친절한 Codex 연구 작업공간입니다.**

[English](README.md) · [상세 초기 설정](GETTING_STARTED.ko.md)

Math Research Workbench는 연구 아이디어, 논문 노트, 증명 작업, 연구 프로젝트를
평범한 Markdown 파일로 정리하도록 돕습니다. ChatGPT 웹 버전만 사용해 본 분도
쓸 수 있도록 만들었으며, Git·터미널·프로그래밍 경험이 없어도 됩니다.

이 공개 저장소에는 재사용 가능한 틀만 있습니다. 개인 연구 노트, 개인 경로,
비밀번호나 인증 정보, 기계학습 실험 환경은 포함하지 않습니다.

## 가장 쉬운 시작 방법

권장 방법은 배포용 ZIP 파일을 받는 것입니다. GitHub 사용은 선택 사항입니다.

1. macOS 또는 Windows에서
   [ChatGPT 데스크톱 앱](https://chatgpt.com/download/)을 설치하고 로그인합니다.
   Linux에서는 현재 [Codex 명령줄 도구](https://developers.openai.com/codex/cli/)와
   기본적인 터미널 사용법이 필요합니다.
2. [최신 배포판](https://github.com/JaeminPark417/math-research-workbench/releases/latest)에서
   ZIP 파일을 다운로드합니다.
3. ZIP을 iCloud Drive, OneDrive, Dropbox, Google Drive가 동기화하지 않는
   로컬 폴더에 풉니다. 사용자 홈 폴더 바로 아래에 `MathResearch` 폴더를
   만들어 넣는 방법을 권장합니다.
4. 데스크톱 앱에서 **Codex**를 선택하고 압축을 푼 폴더를 엽니다.
5. 다음 메시지를 직접 보냅니다.

   ```text
   초기 설정을 시작해줘
   ```

폴더를 여는 것만으로는 Codex가 먼저 말을 걸거나 설정을 시작하지 않습니다.
반드시 위 메시지를 보내거나 `$first-run`을 실행해야 합니다.

Codex는 한 번에 하나씩 다음을 물어봅니다.

- 사용할 언어
- 글 파일의 변경 이력을 보관할 비공개(private) GitHub 저장소 사용 여부
- PDF와 큰 파일을 둘 외부 저장소 사용 여부
- Obsidian 설치 및 확장 기능(plugin) 사용 여부
- Overleaf 또는 이 PC에서 TeX 원고를 PDF로 만들지 여부

모두 선택 사항입니다. 프로그램 설치, 계정 변경, 원격 저장소 생성, 이 폴더 밖의
파일 작성 전에는 무엇이 바뀌는지 먼저 보여주고 승인을 받습니다.

## 폴더 구성

| 폴더 | 용도 |
| --- | --- |
| `inbox/` | 아직 분류하지 않은 메모와 자료 |
| `ideas/` | 질문, 추측, 발전 중인 연구 방향 |
| `papers/` | 서지정보와 독서 노트; 논문 PDF 원문은 두지 않음 |
| `notes/` | 재사용할 정의, 보조정리, 예시, 설명 |
| `projects/` | 진행 중인 연구, 증명, 세션 기록, 초고 |
| `files/` | 큰 파일의 임시 로컬 위치; 기본적으로 GitHub에서 제외 |
| `meta/` | 작성 규칙, 문서 형식, 안전 원칙, 서식 |

Codex나 Obsidian을 사용하지 않아도 파일은 일반 문서 편집기로 읽을 수 있습니다.
Obsidian은 같은 Markdown 파일을 보기 좋게 편집하는 선택형 프로그램입니다.

## 첫 요청 예시

```text
이 연구 질문을 inbox에 기록하고 수학적으로 정확하게 정식화해줘.
```

```text
이 arXiv 링크의 서지정보를 확인하고 논문 노트를 만들어줘.
```

```text
이 증명을 검토해줘. 확립된 단계, 빈틈, 가능한 수정안을 구분하고,
너 혼자 검토했다는 이유로 검증 완료라고 표시하지 마.
```

```text
이 문제를 위한 새 프로젝트를 만들고 생성하는 폴더를 하나씩 설명해줘.
```

더 많은 예시는 [일상 사용 가이드](docs/daily-workflow.ko.md)에 있습니다.

## 중요한 기본 안전 원칙

- 미공개 연구의 GitHub 저장소는 **비공개(private)**가 기본입니다.
- GitHub는 자동 백업이 아닙니다. 저장(commit)하고 올리기(push)까지 마친 변경만
  GitHub에 나타나며, Codex가 매번 대상 파일과 의미를 설명하고 승인을 받아야 합니다.
- 작업공간 자체는 클라우드 동기화 폴더 안에 두지 않습니다. PDF와 큰 파일만
  별도 외부 저장소에 둡니다.
- 비밀번호, 접근 토큰, 개인 키, 브라우저 쿠키를 대화창에 붙여 넣지 않습니다.
- 커뮤니티 확장 기능은 제3자 프로그램입니다.
  [확장 기능 안내](docs/obsidian-plugins.ko.md)를
  읽고 필요한 것만 하나씩 설치합니다.
- Obsidian에서 수식을 보는 데 로컬 TeX 설치는 필요하지 않습니다. 원고를 PDF로
  만드는 일은 우선 Overleaf를 권장합니다.
- AI의 검토만으로 증명이 성립하거나 참고문헌이 확인된 것은 아닙니다.
- 로컬 폴더를 연다고 Codex가 오프라인 프로그램이 되는 것은 아닙니다. 요청 처리에
  필요한 내용이 OpenAI로 전송될 수 있습니다. 비공개 심사 자료, 학생·환자 정보,
  공동연구 기밀처럼 제한된 자료를 사용하기 전에 소속 기관의 규정과 계정의
  [데이터 제어 설정](https://help.openai.com/en/articles/7730893-data-controls-faq)을
  확인하세요.

## 로컬 데스크톱과 클라우드의 차이

macOS 또는 Windows에서는 ChatGPT 데스크톱 앱에서 첫 설정을 진행하세요. 로컬 폴더에
권한을 주면 Codex가 그 폴더에서 작업할 수 있습니다. Linux에는 현재 데스크톱 앱이
없어 Codex 명령줄 도구와 터미널 사용법이 필요합니다. 호스팅된 Codex·클라우드 환경은
사용자의 PC에 Obsidian이나 TeX을 설치하거나, PC의 외부 저장소 폴더를 확인하거나,
이 기기의 로컬 설정 파일을 유지할 수 없습니다. 그런 환경에서는 Markdown 자체는 쓸
수 있지만 로컬 설정을 완료한 것처럼 처리하지 않습니다.
[OpenAI 공식 안내](https://help.openai.com/en/articles/20001275)

macOS와 Windows에서는 Codex 명령줄 도구가 필요하지 않습니다.

## 도움말

- [상세 초기 설정](GETTING_STARTED.ko.md)
- [Obsidian 안내](docs/obsidian.ko.md)
- [Obsidian 확장 기능 안내](docs/obsidian-plugins.ko.md)
- [문제 해결](docs/troubleshooting.ko.md)
- [안전한 업데이트](docs/updating.ko.md)
- [보안 정책(영문)](SECURITY.md)
- [기여 방법(영문)](CONTRIBUTING.md)
- [라이선스와 콘텐츠 안내(영문)](CONTENT-NOTICE.md)

Math Research Workbench는 독립 프로젝트이며 OpenAI, Obsidian, GitHub, Overleaf,
클라우드 저장소 제공자와 제휴되어 있지 않습니다.
