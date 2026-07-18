# 수학자를 위한 Obsidian 플러그인 안내

## 커뮤니티 플러그인 없이 시작하기

처음에는 **기본(core) 플러그인만** 사용하는 것을 권합니다. Obsidian에 포함된
검색, 백링크, 속성, 템플릿, 개요, 파일 복구 기능만으로도 초기 작업 대부분을 할
수 있습니다.

커뮤니티 플러그인은 사용자를 대신해 실행되고 vault에 접근할 수 있는 제3자
코드입니다. 해결하려는 문제를 한 문장으로 분명히 말할 수 있을 때만 설치하세요.
여러 플러그인을 묶어서 한꺼번에 설치하거나, 다른 사람의 플러그인 폴더를 복사하거나,
논문이나 웹페이지가 요구하는 코드를 그대로 설치하면 안 됩니다.

Obsidian의 공식 절차와 경고는
[Community plugins](https://help.obsidian.md/community-plugins)에 있습니다.

## 안전한 설치 순서

선택한 플러그인마다 다음 과정을 **하나씩 따로** 반복하세요.

1. 노트를 백업하고 열어 둔 편집을 모두 마칩니다.
2. **Settings → Community plugins**를 엽니다.
3. Obsidian의 경고를 읽은 뒤에만 **Turn on community plugins**를 선택합니다.
4. **Browse**를 선택합니다.
5. 아래에 나온 정확한 플러그인 이름을 검색하고, 제작자와 설명이 맞는지
   확인합니다.
6. **Install**을 선택한 다음 **Enable**을 선택합니다.
7. 실제 연구 노트에 쓰기 전에 버려도 되는 시험용 노트에서 테스트합니다.
8. 예상하지 못한 동작이 나타나면 먼저 그 플러그인을 끕니다. Markdown 파일은
   그대로 남습니다.

Codex가 이 화면들을 차례로 안내할 수는 있지만, 플러그인 코드를 직접 내려받거나
복사해서는 안 됩니다. 업데이트도 한 번에 하나씩 검토하세요. 커뮤니티 플러그인이
항상 자동으로 업데이트되는 것은 아닙니다.

## 목적별 선택 플러그인

### 수식 입력을 빠르게: Latex Suite

[Latex Suite](https://community.obsidian.md/plugins/obsidian-latex-suite)는 짧은
글자를 LaTeX 표기로 확장하고 수식 입력 단축 기능을 제공합니다. Obsidian 안에서
수식을 많이 직접 쓸 때만 유용합니다.

처음에는 기본 설정을 그대로 사용하세요. 모르는 사람이 만든 snippet 모음을 붙여
넣지 마세요. 플러그인 자체 문서도 snippet 파일이 JavaScript로 해석되어 임의의
코드를 실행할 수 있다고 경고합니다. 자동 확장 기능이 일반 문장이나 한글 입력을
방해하지 않는지도 확인하세요.

이 플러그인은 수식 입력을 도울 뿐입니다. `.tex` 원고를 PDF로 조판하지도 않고,
수학적 내용이 옳은지 검증하지도 않습니다.

### Zotero 문헌 가져오기: Zotero Integration

[Zotero Integration](https://community.obsidian.md/plugins/obsidian-zotero-desktop-connector)은
Zotero에서 인용 정보, 참고문헌, 노트, PDF 주석을 가져올 수 있습니다. 이미
Zotero 데스크톱을 사용하고 있고 그 작업 흐름을 연결하고 싶을 때만 선택하세요.
공식 목록에 따르면 이 플러그인은 데스크톱 전용이며
[Better BibTeX for Zotero](https://retorque.re/zotero-better-bibtex/)가 필요합니다.

이 추가 프로그램도 별도의 설치이므로, Codex에게 먼저 설명을 듣고 따로 허락한
뒤 진행하세요. 가져온 문헌 정보에도 오류나 누락이 있을 수 있습니다. 제목, 저자,
연도, DOI, arXiv 식별자는 일차 문헌 정보 출처와 대조하세요.

### 표와 대시보드: Dataview

[Dataview](https://community.obsidian.md/plugins/dataview)는 Markdown 속성을
조건에 따라 골라 목록이나 표로 만들 수 있습니다. 필수 기능이 아니라 고급 편의
기능입니다. 처음에는 일반 폴더와 검색이 더 쉽습니다.

가능하면 일반 Dataview 질의만 사용하세요. 공식 목록은 DataviewJS와 인라인
JavaScript가 파일을 만들거나 다시 쓰거나 삭제할 수 있고, 네트워크 요청도 보낼
수 있다고 경고합니다. 신뢰할 수 없는 노트나 웹사이트에서 복사한 JavaScript를
실행하지 마세요.

### Git 작업 자동화: Obsidian Git

[Obsidian Git](https://community.obsidian.md/plugins/obsidian-git)은 Obsidian
안에서 커밋, pull, push를 실행할 수 있습니다. **초기 설정 때에는 권하지
않습니다.** 비공개 GitHub 백업이 정상적으로 작동하고, 커밋·pull·push가 무엇을
바꾸는지 이해한 뒤에만 고려하세요.

이 플러그인은 자동 동기화와 되돌리기 어려운 Git 작업을 제공합니다. 직접 한 번
백업하고 왕복 확인을 마치기 전에는 예약 동기화나 자동 pull을 켜지 마세요.
충돌을 해결하려고 discard-all, 저장소 삭제, 강제 push, 이력 다시 쓰기를 사용하면
안 됩니다. Obsidian과 다른 도구에서 자동 Git 작업을 동시에 실행하지 마세요.

Git 용어가 아직 낯설다면 이 플러그인을 설치하는 대신, Codex가 포함 파일과
비공개 목적지를 매번 확인하는 백업 흐름을 안내하도록 하세요. GitHub는 자동
백업이 아니며, 커밋하고 푸시한 변경만 온라인에 나타납니다.

## 간단한 선택 표

| 필요한 기능 | 권장 선택 |
| --- | --- |
| 노트 읽기, 검색, 연결, 복구 | 기본 플러그인만 사용 |
| 많은 수식을 더 빨리 입력 | Latex Suite 고려 |
| 기존 Zotero 데스크톱 문헌 가져오기 | Zotero Integration 고려 |
| 속성 기반 대시보드 만들기 | Dataview는 나중에 고려 |
| Obsidian 안에서 Git 자동 백업 | 고급 기능이므로 기본적으로 미루기 |

플러그인이 많다고 더 좋은 연구 시스템이 되는 것은 아닙니다. 작고 이해하기 쉬운
설정이 업데이트하고, 문제를 찾고, 신뢰하기에 더 좋습니다.
