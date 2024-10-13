import os
import json
import pandas as pd
import re

# 파일 경로 설정
SRC_DIR = './Src'
DATA_DIR = './data'
EXCEL_FILE = os.path.join(SRC_DIR, 'file.xlsx')
OUTPUT_FILE = os.path.join(DATA_DIR, 'korea_area.json')

def split_township_name(township_name):
    # '제' 제거
    township_name = re.sub(r'제(\d+)', r'\1', township_name)

    # 복합 동 분리 (예: '종로1.2.3.4가동' → '종로1가동', '종로2가동', '종로3가동', '종로4가동')
    if re.search(r'\d+[\.,]\d+', township_name):
        base_name = re.sub(r'\d+[\.,]\d+.*$', '', township_name)
        suffix = '가동' if '가동' in township_name else '동'
        numbers = re.findall(r'\d+', township_name)
        return [f"{base_name}{num}{suffix}" for num in numbers]

    # 점(.)으로 구분된 동 분리 (예: '불로.봉무동' → '불로동', '봉무동')
    if '.' in township_name or ',' in township_name:
        parts = re.split(r'[.,]', township_name)
        return [part.strip() if part.strip().endswith('동') else f"{part.strip()}동" for part in parts if part.strip()]

    return [township_name]

def convert_excel_to_json(excel_path, aggregated_data):
    df = pd.read_excel(excel_path)
    print(f"Total rows in the Excel file: {len(df)}")

    required_columns = ['행정동코드', '시도명', '시군구명', '읍면동명', '생성일자', '말소일자']
    if not all(col in df.columns for col in required_columns):
        print("Required columns are missing from the data.")
        return

    # NaN 값을 빈 문자열로 대체
    df = df.fillna('')

    for _, row in df.iterrows():
        adm_cd = str(row['행정동코드']).strip()
        province_name = str(row['시도명']).strip()
        city_name = str(row['시군구명']).strip()
        township_name = str(row['읍면동명']).strip()
        creation_date = str(row['생성일자']).strip()
        deletion_date = row['말소일자']

        if deletion_date:
            continue

        if not province_name or not city_name or not township_name:
            continue

        # 세종특별자치시의 경우 시군구명이 비어있을 수 있음
        if province_name == "세종특별자치시" and not city_name:
            city_name = "세종특별자치시"

        if province_name not in aggregated_data:
            aggregated_data[province_name] = {
                "province": province_name,
                "isSpecialCity": False,
                "cities": [],
                "totalTownships": 0
            }

        province = aggregated_data[province_name]

        city = next((c for c in province['cities'] if c['name'] == city_name), None)
        if not city:
            city = {
                "name": city_name,
                "townships": [],
                "totalTownships": 0
            }
            province['cities'].append(city)

        # 복합 동 명칭 처리
        new_townships = split_township_name(township_name)

        for township in new_townships:
            if '출장소' in township:
                continue

            if township not in city['townships']:
                city['townships'].append(township)
                city['totalTownships'] += 1
                province['totalTownships'] += 1

def process_excel_files(directory):
    aggregated_data = {}
    for filename in os.listdir(directory):
        if filename.endswith('.xlsx'):
            file_path = os.path.join(directory, filename)
            convert_excel_to_json(file_path, aggregated_data)

    total_townships = sum(province['totalTownships'] for province in aggregated_data.values())

    if aggregated_data:
        output_directory = os.path.join(os.path.dirname(__file__), "data")
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        json_path = os.path.join(output_directory, "korea_area.json")
        try:
            with open(json_path, 'w', encoding='utf-8') as json_file:
                output_data = {
                    "totalTownships": total_townships,
                    "provinces": list(aggregated_data.values())
                }
                json.dump(output_data, json_file, ensure_ascii=False, indent=4)
            print(f"JSON 파일이 성공적으로 생성되었습니다: {json_path}")
        except Exception as e:
            print(f"JSON 파일 생성 중 오류가 발생했습니다: {str(e)}")
    else:
        print("처리된 데이터가 없습니다. 입력 파일에 유효한 데이터가 있는지 확인하세요.")

    print(f"총 처리된 읍면동 수: {total_townships}")
    print(f"처리된 도/시 수: {len(aggregated_data)}")

if __name__ == "__main__":
    process_excel_files(SRC_DIR)
