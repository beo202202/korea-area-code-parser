import os
import json
import zipfile
import chardet
import re

# 파일의 인코딩을 감지하는 함수입니다.
def detect_encoding(file_content):
    result = chardet.detect(file_content)
    encoding = result['encoding']
    return encoding

# 텍스트 파일의 내용을 JSON 형식으로 변환하는 함수입니다.
def convert_txt_to_json(txt_content, aggregated_data):
    lines = txt_content.splitlines()
    print(f"Total lines in the file: {len(lines)}")
    
    if len(lines) == 0:
        print("The file is empty. Skipping this file.")
        return
    
    header = lines[0].split('|')  # 헤더 추출
    lines = lines[1:]  # 헤더를 제외한 데이터 라인

    # 컬럼 인덱스 매핑
    col_idx = {col: idx for idx, col in enumerate(header)}
    
    # 필요한 컬럼이 모두 존재하는지 확인
    required_columns = ['ADM_CD', 'ADM_SECT_NM', 'LOWEST_ADM_SECT_NM', 'ADM_SECT_GBN', 'CHG_BEF_ADM_SECT_GBN', 'DEL_YMD']
    if not all(col in col_idx for col in required_columns):
        print("Required columns are missing from the data.")
        return

    # 각 줄에 대해 데이터를 추출하고 JSON으로 변환합니다.
    for line in lines:
        columns = line.split('|')

        # 열 개수가 부족한 경우 무시
        if len(columns) < len(header):
            print(f"Line does not have enough columns: {columns}")
            continue

        # 컬럼 데이터 추출 및 공백 제거
        adm_cd = columns[col_idx['ADM_CD']].strip()
        adm_sect_nm = columns[col_idx['ADM_SECT_NM']].strip()
        lowest_adm_sect_nm = columns[col_idx['LOWEST_ADM_SECT_NM']].strip()
        adm_sect_gbn = columns[col_idx['ADM_SECT_GBN']].strip()
        chg_bef_adm_sect_gbn = columns[col_idx['CHG_BEF_ADM_SECT_GBN']].strip()
        del_ymd = columns[col_idx['DEL_YMD']].strip()

        # 추가 및 제거 조건 적용
        add_data = False
        remove_data = False

        if adm_sect_gbn in ('A'):
            add_data = True
        if adm_sect_gbn in ('L'):
            remove_data = True
        else:
            add_data = True

        if remove_data:
            continue  # 제거 대상이면 처리하지 않음

        if not add_data:
            continue  # 추가 대상이 아니면 처리하지 않음

        # 행정 코드에 따라 도, 시, 군, 구, 읍면동으로 구분하여 처리
        parts = adm_sect_nm.split()
        if len(parts) < 2:
            print(f"Not enough parts in adm_sect_nm: {adm_sect_nm}")
            continue

        province_name = parts[0]
        city_name = parts[1]
        is_special_city = province_name.endswith("특별시") or province_name.endswith("광역시") or province_name.endswith("특별자치시")

        # 특례시 목록 추가
        special_cities = ['수원시', '고양시', '용인시', '창원시']

        # 특례시 처리
        if city_name in special_cities:
            city_name = city_name.replace('시', '특례시')

        is_special_city = province_name.endswith("특별시") or province_name.endswith("광역시") or province_name.endswith("특별자치시") or city_name.endswith("특례시")

        # 도 정보 초기화
        if province_name not in aggregated_data:
            aggregated_data[province_name] = {
                "province": province_name,
                "isSpecialCity": is_special_city,
                "cities": [],
                "totalTownships": 0
            }

        province = aggregated_data[province_name]

        # 읍면동 처리
        if len(parts) >= 3:
            township_name = ' '.join(parts[2:])
            print(f"처리 중인 township_name: {township_name}")  # 디버깅 출력

            # '리' 단위와 '리(한자)' 제거
            if township_name.endswith('리') or re.search(r'리\([里]\)$', township_name):
                print(f"'리' 단위 제거: {township_name}")  # 디버깅 출력
                continue  # '리' 단위와 '리(한자)'는 처리하지 않음

            # '구' 단위로 끝나는 데이터 처리
            if township_name.endswith('구'):
                if len(parts) > 3:  # '구' 다음에 추가 정보가 있는 경우
                    township_name = ' '.join(parts[3:])
                    print(f"'구' 다음 정보 처리: {township_name}")  # 디버깅 출력
                else:
                    print(f"'구'만 있는 경우 건너뛰기: {township_name}")  # 디버깅 출력
                    continue  # '구'만 있는 경우 건너뛰기

            # 복합 동 처리
            new_townships = []
            if re.search(r'\d+[\.,]\d+동$', township_name):
                base_name = re.sub(r'\d+[\.,]\d+동$', '', township_name)
                numbers = re.findall(r'\d+', township_name)
                new_townships = [f"{base_name}{num}동" for num in numbers]
            elif '.' in township_name or ',' in township_name:
                parts = re.split(r'[.,]', township_name)
                base_name = re.sub(r'(동|가)$', '', parts[0].strip())
                new_townships = [f"{base_name}{part.strip()}동" for part in parts if part.strip()]
            else:
                new_townships = [township_name]
            
            print(f"생성된 new_townships: {new_townships}")  # 디버깅 출력

            # 시 정보 검색 또는 생성
            city = next((c for c in province['cities'] if c['name'] == city_name), None)
            if not city:
                city = {
                    "name": city_name,
                    "townships": [],
                    "totalTownships": 0
                }
                province['cities'].append(city)
                city['township_set'] = set()

            for township in new_townships:
                print(f"처리 중인 개별 township: {township}")  # 디버깅 출력

                # '출장소'가 포함된 읍면동 건너뛰기
                if '출장소' in township:
                    print(f"'출장소'가 포함된 읍면동은 건너뜁니다: {township}")
                    continue

                # 읍/면/동으로 끝나는 기본 지명 추출
                # base_township_match = re.match(r'(.+?(?:읍|면|동))(.*)', township)
                # base_township_match = re.match(r'(.+(?:읍|면|동))(.*)', township)
                base_township_match = re.match(r'(.+(?:읍|면|동))(?:\s|$)(.*)', township)
                if base_township_match:
                    base_township = base_township_match.group(1)
                    suffix = base_township_match.group(2)
                    print(f"추출된 base_township: {base_township}, suffix: {suffix}")  # 디버깅 출력
                    # base_township이 이미 존재하는지 확인
                    if base_township in city['township_set']:
                        print(f"이미 존재하는 읍/면/동입니다. 확장된 형태를 건너뜁니다: {township}")
                        continue
                    elif suffix:
                        # 추가적으로 suffix가 있을 경우 base_township만 추가
                        township = base_township
                        print(f"suffix 제거 후 township: {township}")  # 디버깅 출력

                # '면'이 지명의 일부인 경우 (예: '동면') 처리
                if township.endswith('면') and len(township) > 1:
                    if township[-2] == '동' or not township[-2].isdigit():
                        print(f"'면' 유지: {township}")  # 디버깅 출력
                        pass  # '면'을 제거하지 않음
                    else:
                        township = township[:-1]  # 일반적인 '면' 제거
                        print(f"'면' 제거 후: {township}")  # 디버깅 출력

                if township not in city['township_set']:
                    city['townships'].append(township)
                    city['township_set'].add(township)
                    city['totalTownships'] += 1
                    province['totalTownships'] += 1
                    print(f"도시 {city_name} 아래에 읍면동이 추가되었습니다: {township} ({adm_cd})")
                else:
                    print(f"읍면동 {township}이(가) 도시 {city_name}에 이미 존재합니다. 건너뜁니다.")

        else:
            # 읍면동 정보가 없는 경우 처리
            # 특별시나 광역시가 아닌 경우 읍면동 단위만 저장
            if not is_special_city:
                township_name = city_name
                city_name = None

                # 시 정보 검색 또는 생성
                city = next((c for c in province['cities'] if c['name'] == '기타'), None)
                if not city:
                    continue
                
                # '리' 단위와 '리(한자)' 제거
                if township_name.endswith('리') or re.search(r'리\([里]\)$', township_name):
                    continue  # '리' 단위와 '리(한자)'는 처리하지 않음

                # '구' 단위로 끝나는 데이터 제외
                if township_name.endswith('구'):
                    continue

                if township_name not in city['township_set']:
                    city['townships'].append(township_name)
                    city['township_set'].add(township_name)
                    city['totalTownships'] += 1
                    province['totalTownships'] += 1
                    print(f"Township added under province {province_name}: {township_name} ({adm_cd})")
                else:
                    print(f"Township {township_name} already exists under province {province_name}, skipping.")
            else:
                # 특별시나 광역시의 구 단위만 있는 데이터는 저장하지 않음
                continue

    # JSON 저장 시 중복 방지를 위한 set은 제거합니다.
    for province in aggregated_data.values():
        for city in province['cities']:
            if 'township_set' in city:
                del city['township_set']

# ZIP 파일을 처리하여 필요한 정보를 추출하는 함수입니다.
def process_zip_files(directory):
    if not os.path.exists(directory):
        raise FileNotFoundError(f"지정된 경로를 찾을 수 없습니다: {directory}")

    aggregated_data = {}

    for filename in os.listdir(directory):
        if filename.endswith(".zip"):
            zip_path = os.path.join(directory, filename)
            print(f"Processing ZIP file: {filename}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    print(f"File info: {file_info.filename}, Size: {file_info.file_size}")
                    if file_info.filename.endswith(".txt"):
                        print(f"Processing text file inside ZIP: {file_info.filename}")
                        with zip_ref.open(file_info) as file:
                            file_content = file.read()
                            detected_encoding = detect_encoding(file_content)
                            print(f"Detected encoding: {detected_encoding}")
                            try:
                                txt_content = file_content.decode(detected_encoding)
                            except (UnicodeDecodeError, TypeError):
                                print(f"Failed to decode with detected encoding. Skipping {file_info.filename}.")
                                continue

                            print(f"Length of txt_content: {len(txt_content)}")
                            if len(txt_content) == 0:
                                print(f"The file {file_info.filename} is empty after decoding. Skipping.")
                                continue

                            convert_txt_to_json(txt_content, aggregated_data)

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

# 메인 함수: .zip 파일이 있는 디렉터리를 지정하고 처리합니다.
if __name__ == "__main__":
    directory = "./zip_files"  # .zip 파일들이 저장된 디렉터리 경로
    process_zip_files(directory)