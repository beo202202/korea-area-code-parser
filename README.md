# 한국 행정구역 데이터 처리 프로젝트

이 프로젝트는 한국의 행정구역 데이터를 처리하여 JSON 형식으로 변환하는 Python 스크립트를 포함하고 있습니다.

## 데이터 소스

- 사용된 데이터는 2024년 4월 기준 행정구역 정보입니다.
- 현재 버전에서는 부천시 데이터가 누락되어 있습니다.

## 프로젝트 구조

```
project_root/
│
├── zip_files/                # 원본 ZIP 파일들이 저장된 디렉토리
│   ├── file1.zip
│   ├── file2.zip
│   └── ...
│
├── data/                     # 처리된 데이터가 저장되는 디렉토리
│   └── korea_area.json       # 최종 출력 파일
│
├── translate_korea_area.py   # 메인 처리 스크립트
├── requirements.txt          # 프로젝트 의존성 파일
├── README.md                 # 프로젝트 설명 문서
└── .gitignore                # Git 무시 파일 목록
```

## 기능

- 읍면동 데이터 처리 및 정제
- 특별시, 광역시, 특례시 등의 구분 처리
- 복합 동 명칭 분리
- 중복 데이터 제거
- 특수 케이스 (출장소, 리 단위 등) 처리

## 요구 사항

- Python 3.x
- pip (Python 패키지 관리자)

## 설치 및 실행

1. 가상 환경 생성 및 활성화:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # Linux/macOS
   myenv\Scripts\activate  # Windows
   ```

2. 필요한 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```

3. 스크립트 실행:
   ```bash
   python translate_korea_area.py
   ```

4. 결과 확인:
   실행 후 `data/korea_area.json` 파일이 생성됩니다.

## 데이터 처리 규칙

### 구 명칭과 읍면동 명칭 처리
- 특별시, 특별자치시, 광역시의 경우:
  - 구 단위만 있는 데이터 삭제 (예: '용산구' 삭제)
  - 구 단위와 동 단위를 합친 데이터 저장 (예: '용산구 후암동' 추가)
- 그 외 지역의 경우:
  - 시/군/구 단위로 저장 (예: '창원시 성산구')
  - 읍면동 단위로 저장 (예: '중앙동')
- 공통: 리 단위 및 출장소 포함 데이터 삭제

### 복합 동 명칭 처리
- 복합 동 분리 (예: '종로1.2.3.4가동' → '종로1동', '종로2동', '종로3동', '종로4동')
- 숫자로 구분된 동 분리 (예: '신천1.2동' → '신천1동', '신천2동')
- 점(.)으로 구분된 동 분리 (예: '불로.봉무동' → '불로동', '봉무동')

### 특수 케이스 처리
- 출장소 및 기타 부가 명칭 제거 (예: '사등면가조출장소' → '사등면')
- 리(里) 단위 삭제 (한자 포함)

### 데이터 추가 및 제거 조건
- ADM_SECT_GBN이 'A'인 경우 데이터 추가
- ADM_SECT_GBN이 'L'인 경우 데이터 제외
- 중복 데이터 제거

### 주의사항
- 부천시 데이터는 현재 누락되어 있으며, 추후 데이터 소스 업데이트 시 추가될 예정입니다.

## 출력 형식

```json
{
    "totalTownships": 3186,
    "provinces": [
        {
            "province": "강원특별자치도",
            "isSpecialCity": false,
            "cities": [
                {
                    "name": "춘천시",
                    "townships": [
                        "신북읍",
                        "동면",
                        "동산면",
                        "신동면",
                        ...
                    ]
                },
                ...
            ]
        },
        ...
    ]
}
```

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)하에 제공됩니다.