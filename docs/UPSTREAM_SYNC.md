# Upstream Synchronization Guide

이 문서는 CopilotKit Python SDK의 upstream 변경사항을 추적하고 병합하는 방법을 설명합니다.

## 개요

- **Upstream Repository**: https://github.com/CopilotKit/CopilotKit
- **SDK Path**: `sdk-python/`
- **Local Path**: `copilotkit_sdk/`
- **Git Remote**: `copilotkit-upstream`

## 현재 버전 확인

```bash
# 현재 사용 중인 SDK 버전 확인
cat copilotkit_sdk/pyproject.toml | grep "^version"

# PyPI의 최신 버전 확인
uv pip index versions copilotkit
```

## Upstream 변경사항 확인

### 1. Upstream Fetch

```bash
# Upstream의 최신 변경사항 가져오기
git fetch copilotkit-upstream main
```

### 2. 변경사항 확인

```bash
# 임시 디렉토리에 최신 sdk-python 가져오기
cd /tmp
git clone --no-checkout --depth 1 --filter=blob:none \
  https://github.com/CopilotKit/CopilotKit.git copilotkit-temp
cd copilotkit-temp
git sparse-checkout init --cone
git sparse-checkout set sdk-python
git checkout main

# 버전 확인
cat sdk-python/pyproject.toml | grep "^version"

# 변경 내역 확인
cd /tmp/copilotkit-temp
git log --oneline --since="1 month ago" -- sdk-python/

# 정리
cd /tmp
rm -rf copilotkit-temp
```

### 3. 차이점 비교

```bash
# 현재 프로젝트로 돌아오기
cd /Users/jhj/Desktop/personal/251029_online_seminar

# 임시로 최신 버전 다운로드
cd /tmp
curl -L https://github.com/CopilotKit/CopilotKit/archive/refs/heads/main.tar.gz | \
  tar xz CopilotKit-main/sdk-python --strip-components=1

# 차이점 비교
diff -r /tmp/sdk-python /Users/jhj/Desktop/personal/251029_online_seminar/copilotkit_sdk

# 정리
rm -rf /tmp/sdk-python
```

## Upstream 업데이트 병합

### 방법 1: 선택적 파일 업데이트 (권장)

특정 파일이나 기능만 업데이트하고 싶을 때 사용합니다.

```bash
# 1. 임시 디렉토리에 최신 버전 다운로드
cd /tmp
curl -L https://github.com/CopilotKit/CopilotKit/archive/refs/heads/main.tar.gz -o copilotkit.tar.gz
tar xzf copilotkit.tar.gz
cd CopilotKit-main/sdk-python

# 2. 필요한 파일만 복사 (예: 버그 수정된 파일)
cp copilotkit/agent.py /Users/jhj/Desktop/personal/251029_online_seminar/copilotkit_sdk/copilotkit/

# 3. 변경사항 확인 및 커밋
cd /Users/jhj/Desktop/personal/251029_online_seminar
git diff copilotkit_sdk/copilotkit/agent.py
git add copilotkit_sdk/copilotkit/agent.py
git commit -m "upstream: update agent.py from CopilotKit main"

# 4. 정리
rm -rf /tmp/copilotkit.tar.gz /tmp/CopilotKit-main
```

### 방법 2: 전체 업데이트

전체 SDK를 업데이트하되 커스터마이징을 유지하고 싶을 때:

```bash
# 1. 현재 커스터마이징 내역 확인
git log --oneline copilotkit_sdk/

# 2. 커스터마이징한 파일 목록 작성
# docs/CUSTOMIZATIONS.md를 참고하여 수정한 파일들을 백업

# 3. 백업 디렉토리 생성
mkdir -p /tmp/customizations_backup
cp copilotkit_sdk/copilotkit/your_custom_file.py /tmp/customizations_backup/

# 4. 최신 upstream 다운로드
cd /tmp
curl -L https://github.com/CopilotKit/CopilotKit/archive/refs/heads/main.tar.gz -o copilotkit.tar.gz
tar xzf copilotkit.tar.gz

# 5. SDK 전체 교체
rm -rf /Users/jhj/Desktop/personal/251029_online_seminar/copilotkit_sdk
cp -r /tmp/CopilotKit-main/sdk-python /Users/jhj/Desktop/personal/251029_online_seminar/copilotkit_sdk

# 6. 커스터마이징 다시 적용
cd /Users/jhj/Desktop/personal/251029_online_seminar
cp /tmp/customizations_backup/your_custom_file.py copilotkit_sdk/copilotkit/

# 7. 변경사항 확인 및 커밋
git status
git add copilotkit_sdk/
git commit -m "upstream: sync with CopilotKit main (version X.X.X)"

# 8. 정리
rm -rf /tmp/copilotkit.tar.gz /tmp/CopilotKit-main /tmp/customizations_backup
```

### 방법 3: 자동화 스크립트

반복적인 업데이트를 위한 스크립트를 작성할 수 있습니다.

`scripts/sync_upstream.sh`:
```bash
#!/bin/bash
set -e

UPSTREAM_URL="https://github.com/CopilotKit/CopilotKit/archive/refs/heads/main.tar.gz"
PROJECT_ROOT="/Users/jhj/Desktop/personal/251029_online_seminar"
TEMP_DIR="/tmp/copilotkit_sync_$$"

echo "Syncing CopilotKit SDK from upstream..."

# 임시 디렉토리 생성
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Upstream 다운로드
echo "Downloading upstream..."
curl -L "$UPSTREAM_URL" -o copilotkit.tar.gz
tar xzf copilotkit.tar.gz

# 버전 확인
NEW_VERSION=$(grep "^version" CopilotKit-main/sdk-python/pyproject.toml | cut -d'"' -f2)
OLD_VERSION=$(grep "^version" "$PROJECT_ROOT/copilotkit_sdk/pyproject.toml" | cut -d'"' -f2)

echo "Current version: $OLD_VERSION"
echo "New version: $NEW_VERSION"

if [ "$OLD_VERSION" = "$NEW_VERSION" ]; then
    echo "Already up to date!"
    rm -rf "$TEMP_DIR"
    exit 0
fi

# 차이점 표시
echo "Changes:"
diff -rq "$TEMP_DIR/CopilotKit-main/sdk-python" "$PROJECT_ROOT/copilotkit_sdk" || true

read -p "Do you want to proceed with the update? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled"
    rm -rf "$TEMP_DIR"
    exit 0
fi

# 업데이트 (커스터마이징 보존은 수동으로 처리)
echo "Updating SDK..."
# 여기서는 실제 업데이트 로직을 추가
# 커스터마이징된 파일은 수동으로 병합 필요

# 정리
rm -rf "$TEMP_DIR"
echo "Sync complete!"
```

## 충돌 해결

커스터마이징한 파일이 upstream에서도 변경된 경우:

1. **Three-way merge 사용**:
```bash
# 1. 백업
cp copilotkit_sdk/copilotkit/conflicting_file.py /tmp/our_version.py

# 2. Upstream 버전 가져오기
cp /tmp/CopilotKit-main/sdk-python/copilotkit/conflicting_file.py /tmp/upstream_version.py

# 3. 수동 병합 또는 merge tool 사용
git merge-file copilotkit_sdk/copilotkit/conflicting_file.py \
  /tmp/original_version.py \
  /tmp/upstream_version.py
```

2. **변경사항을 패치로 관리**:
   - 커스터마이징을 git patch 형태로 저장
   - Upstream 업데이트 후 patch 재적용

## 주기적인 체크

### 월간 체크리스트

- [ ] Upstream의 새 릴리스 확인
- [ ] 보안 패치 여부 확인
- [ ] 새로운 기능 검토
- [ ] 필요시 선택적 업데이트

### GitHub Watch 설정

```bash
# GitHub CLI 사용
gh repo set-preference CopilotKit/CopilotKit --enable-notifications=true
```

또는 웹에서:
1. https://github.com/CopilotKit/CopilotKit 방문
2. Watch → Custom → Releases 선택

## 버전 추적

각 업데이트 후 다음 정보를 커밋 메시지에 포함:

```
upstream: sync with CopilotKit v0.1.70

- Updated dependencies: langgraph 0.3.25 → 0.3.30
- Bug fix: agent state management issue
- Upstream commit: abc123def456

Custom changes preserved:
- copilotkit/custom_agent.py
- copilotkit/integrations/custom_integration.py
```

## 참고 자료

- Upstream Repository: https://github.com/CopilotKit/CopilotKit
- SDK Documentation: https://github.com/CopilotKit/CopilotKit/blob/main/sdk-python/README.md
- Release Notes: https://github.com/CopilotKit/CopilotKit/releases
- PyPI Package: https://pypi.org/project/copilotkit/
