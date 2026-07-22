# Obsidian: 선택해서 쓰는 시각적 노트 도구

Obsidian은 필수가 아닙니다. Math Research Workbench는 일반 Markdown 파일로
이루어져 있으므로 Obsidian 없이도 사용할 수 있습니다. Obsidian을 사용하면 같은
파일을 편리하게 편집하고, 검색하고, 서로 연결하고, 수식을 보기 좋게 표시할 수
있습니다.

Obsidian에서 **vault(볼트)**는 단순히 노트가 들어 있는 폴더를 뜻합니다.
workbench 폴더 자체가 이미 vault이므로, 다른 Obsidian 전용 폴더를 새로 만들거나
파일을 복사하지 마세요. Obsidian 공식 문서의
[로컬 Markdown 저장 방식](https://help.obsidian.md/data-storage)과
[기존 폴더를 vault로 여는 방법](https://help.obsidian.md/vault)도 참고할 수
있습니다.

## 원할 때만 설치하기

첫 실행 설정에서 예, 아니요, 나중에 중 하나를 고릅니다. 예를 선택하면 Codex는
다음 순서로 도와줍니다.

1. Obsidian이 이미 설치되어 있는지 확인합니다.
2. 사용하는 운영체제에 맞는 공식 설치 방법을 제시합니다.
3. 실행하려는 명령이나 패키지 관리자 작업의 의미를 설명합니다.
4. 실제 설치를 시작하기 전에 명시적으로 허락을 받습니다.

직접 설치하고 싶다면 공식
[Obsidian 다운로드 페이지](https://obsidian.md/download)와
[설치 안내](https://help.obsidian.md/install)를 이용하세요.

## workbench 열기

1. Obsidian을 실행합니다.
2. **Open folder as vault**를 선택합니다.
3. `AGENTS.md`, `inbox/`, `projects/`가 들어 있는 workbench 최상위 폴더를
   선택합니다.
4. **Open**을 선택합니다.
5. 운영체제가 폴더 접근 권한을 묻는다면, 경로가 맞는지 확인한 뒤 허용합니다.

이미 존재하는 이 workbench에는 **Create new vault**를 선택하지 마세요.

배포판의 `.obsidian` 폴더에는 작은 시작 설정이 들어 있습니다. 새 노트는
`inbox/`로, 첨부 파일은 `files/`로 보내고, 유용한 기본 플러그인을 켭니다.
컴퓨터마다 다른 창 배치와 플러그인 데이터는 연구 내용과 함께 공개하지 않아야
합니다.

## 권장 설정: 기본 플러그인만 사용하기

기본(core) 플러그인은 Obsidian에 포함되어 있고 Obsidian 팀이 관리합니다.
workbench는 다음과 같은 꼭 필요한 기능만 켭니다.

- 파일 탐색기, 검색, 빠른 전환
- 백링크와 나가는 링크
- 속성 보기, 페이지 미리 보기, 개요
- 템플릿과 명령어 팔레트
- 단어 수
- 파일 복구

**Settings → Core plugins**에서 관리할 수 있습니다. Obsidian 공식
[기본 플러그인 목록](https://help.obsidian.md/plugins)도 참고하세요.

공유된 템플릿 설정은 `meta/templates/` 폴더를 가리킵니다. Templates 기본
플러그인 설정을 열고, 템플릿을 삽입하기 전에 **Template folder location**이
`meta/templates`인지 확인하세요.

파일 복구 기능은 유용하지만 완전한 백업은 아닙니다. 중요한 연구 자료는 별도의
독립적인 백업에도 보관하세요. GitHub 역시 자동 백업이 아니며, 커밋하고 푸시한
텍스트만 저장합니다.

## 수식과 TeX

Obsidian은 MathJax를 사용해 Markdown 안의 LaTeX 방식 표기를 화면에 표시합니다.
예를 들면 다음과 같습니다.

```md
문장 안의 수식: $e^{2\pi i}=1$.

별도 줄의 수식:
$$
\int_0^1 x^n\,dx=\frac{1}{n+1}.
$$
```

이 기능에는 로컬 TeX 배포판이 필요하지 않습니다. 로컬 TeX 설치는 `.tex` 원고를
PDF로 조판할 때만 필요합니다. 표기법은 Obsidian의
[수학 구문 안내](https://help.obsidian.md/advanced-syntax#Math)에서 더 볼 수
있습니다.

## 커뮤니티 플러그인

커뮤니티 플러그인은 하나도 설치하지 않아도 됩니다. 먼저 몇 번의 작업 동안 기본
플러그인만 사용하고, 해결하려는 문제가 분명할 때 필요한 플러그인 하나만
설치하세요. 커뮤니티 플러그인은 vault에 접근할 수 있는 프로젝트 또는 제3자의 추가 코드를 실행합니다.
Obsidian도 공식
[커뮤니티 플러그인 안내](https://help.obsidian.md/community-plugins)에서 이를
명시적으로 경고합니다.

Workbench에는 기존 문서의 `\(...\)`와 `\[...\]` 표기를 위한 프로젝트 자체 호환 플러그인 하나도 `optional/` 아래에 실행되지 않는 상태로 들어 있습니다. 기본 상태에서는 설치되거나 활성화되지 않으며, 별도 동의와 테스트 절차는 플러그인 안내에 설명되어 있습니다.

하나라도 설치하기 전에 [Obsidian 플러그인 안내](obsidian-plugins.ko.md)를
읽어 보세요.

## Codex와 Obsidian을 함께 사용할 때

두 프로그램은 같은 파일을 편집합니다. 서로의 변경이 충돌하지 않도록 다음 원칙을
따르세요.

- 노트에 입력하던 내용을 마친 뒤 Codex에게 정리를 요청합니다.
- Codex가 어떤 파일을 바꾸었는지 설명하게 합니다.
- 큰 변경 뒤에는 Obsidian이 새로 읽을 시간을 잠시 줍니다.
- framework 업데이트나 파일 대량 이동 전에는 Obsidian을 닫습니다.

노트가 이전 내용으로 보이면 파일을 다시 열거나, Obsidian 문서에 나온 메타데이터
캐시 재구축 기능을 사용하세요. 급하다는 이유로 vault 복사본을 하나 더 만들지
마세요.
