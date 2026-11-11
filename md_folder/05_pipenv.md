# pipenv 정리

`pip`(패키지 설치)과 `virtualenv`(가상환경)를 합쳐놓은 도구.

기존 방식:
```bash
python -m venv venv                # 가상환경 만들기
source venv/bin/activate           # 활성화
pip install requests               # 패키지 설치
pip freeze > requirements.txt      # 의존성 기록
```

pipenv는 이 과정을 하나로 묶고, `Pipfile`이라는 파일로 의존성을 더 깔끔하게 관리해준다.

## 설치

```bash
pip install pipenv
```

## 기본 사용법

### 1. 프로젝트 폴더 만들고 이동
```bash
mkdir myproject
cd myproject
```

### 2. 가상환경 + 패키지 설치를 동시에
```bash
pipenv install requests
```
이 명령 하나로:
- 가상환경이 자동으로 생성되고
- `requests` 패키지가 설치되고
- `Pipfile`이 생성/업데이트되고
- `Pipfile.lock`이 생성됨 (정확한 버전 고정)

### 3. 가상환경 활성화
```bash
pipenv shell
```
이 안에서는 `python`, `pip` 명령이 가상환경 걸로 실행됨.

### 4. 가상환경 나가기
```bash
exit
```

### 5. 개발용 패키지 설치 (예: 테스트 도구)
```bash
pipenv install pytest --dev
```

### 6. 가상환경 진입 없이 바로 실행
```bash
pipenv run python app.py
```
## 자주 쓰는 명령 정리

```bash
pipenv install                # Pipfile 보고 전체 설치
pipenv install <패키지명>      # 패키지 추가 설치
pipenv uninstall <패키지명>    # 패키지 제거
pipenv graph                  # 설치된 패키지 의존성 트리 보기
pipenv --venv                 # 가상환경 경로 확인
pipenv --rm                   # 가상환경 삭제
```