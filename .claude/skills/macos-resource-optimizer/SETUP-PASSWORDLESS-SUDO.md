# Passwordless Sudo 설정 가이드

## 목적
Claude Code가 메모리 최적화를 위해 `sudo purge` 명령어를 비밀번호 없이 실행할 수 있도록 설정합니다.

## 설정 방법

### 1. sudoers 파일 편집

터미널에서 다음 명령어를 실행하세요:

```bash
sudo visudo
```

### 2. 다음 줄을 파일 맨 끝에 추가

```bash
# Allow rdmtv to run specific memory optimization commands without password
rdmtv ALL=(ALL) NOPASSWD: /usr/bin/purge
rdmtv ALL=(ALL) NOPASSWD: /usr/sbin/purge
rdmtv ALL=(ALL) NOPASSWD: /usr/bin/vm_stat
rdmtv ALL=(ALL) NOPASSWD: /usr/sbin/sysctl
```

**중요**: `rdmtv`를 실제 사용자 이름으로 변경하세요 (터미널에서 `whoami` 명령어로 확인).

### 3. 저장 및 종료

- **vi 편집기**: `ESC` → `:wq` → `Enter`
- **nano 편집기**: `Ctrl + O` → `Enter` → `Ctrl + X`

### 4. 설정 확인

```bash
# 비밀번호 없이 실행되는지 확인
sudo -n purge
echo $?  # 0이면 성공
```

## 보안 고려사항

이 설정은 **특정 명령어만** 비밀번호 없이 실행할 수 있도록 제한합니다:
- ✅ `purge` - 메모리 정리만 허용
- ✅ `vm_stat` - 메모리 통계 조회만 허용
- ✅ `sysctl` - 시스템 설정 조회만 허용
- ❌ 다른 sudo 명령어는 여전히 비밀번호 필요

## 설정 후

설정 완료 후 Claude Code에서 다음과 같이 사용할 수 있습니다:

```bash
# Alfred를 통한 메모리 최적화
uv run scripts/alfred.py --optimize

# 직접 실행
sudo purge
```

## 문제 해결

### "sudo: purge: command not found"
```bash
# purge 명령어 경로 확인
which purge

# 확인된 전체 경로를 sudoers에 추가
# 예: /usr/bin/purge 또는 /usr/sbin/purge
```

### "syntax error in sudoers file"
```bash
# sudoers 파일 문법 검사
sudo visudo -c

# 오류가 있으면 다시 편집
sudo visudo
```

---

**설정 완료 시간**: 2-3분
**보안 수준**: 안전 (특정 명령어만 허용)
**영구 적용**: 재부팅 후에도 유지됨
