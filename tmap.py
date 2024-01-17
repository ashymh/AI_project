import requests
import folium
import json
import os
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time 
from datetime import datetime, timedelta
    
# 출발지 도착지 위,경도 중간 지점 계산 함수
def calculate_midpoint(lat1, lon1, lat2, lon2):
    return ((lat1 + lat2) / 2, (lon1 + lon2) / 2)

def route() :
    # https://ipstack.com
    ##########ip주소로 위도, 경도 찾는 API##########
    key = 'c887f69dd63ddb1cd9d4f53408974e46'
    send_url = 'http://api.ipstack.com/check?access_key=' + key

    # tmap app key
    APP_KEY = "HpVe5crDV38GvHu7tUyMA5CSmhca5PQk3vRWkFH0"

    headers = {
        "appKey": APP_KEY
    }

    # ip 주소 위치에 따른 위도 경도
    r = requests.get(send_url)
    j = json.loads(r.text)

    lat = j['latitude'] # 위도
    lon = j['longitude'] # 경도

    start = str(lat) + ", " + str(lon)

    # 도착지의 위도와 경도
    end_lat =   37.28406822785717 
    end_lon = 126.85166240118258

    end = str(end_lat) + ", " + str(end_lon)

    # 중간 지점 계산
    midpoint_lat, midpoint_lon = calculate_midpoint(lat, lon, end_lat, end_lon)

    # 티맵 경로 안내 API URL
    url = f"https://api2.sktelecom.com/tmap/routes?version=1&format=json&startX={start.split(',')[1]}&startY={start.split(',')[0]}&endX={end.split(',')[1]}&endY={end.split(',')[0]}"

    response = requests.get(url, headers=headers)       

    # 응답이 성공적인지 확인
    if response.status_code == 200:
        # API 응답에서 경로 정보를 추출
        routes_info = response.json()["features"]

        # 경로를 그릴 좌표들의 리스트 생성
        path_coordinates = []
        for feature in routes_info:
            if feature["geometry"]["type"] == "LineString":
                # 좌표계가 [경도, 위도] 형태로 되어 있으므로, [위도, 경도] 순으로 바꿔서 저장
                path_coordinates.extend([[coord[1], coord[0]] for coord in feature["geometry"]["coordinates"]])

        # 예상 이동 시간을 추출
        total_time = sum([feature["properties"]["totalTime"] for feature in routes_info if "totalTime" in feature["properties"]])

        # 현재 시각
        now = datetime.now()
        
        # 현재 시각에 total_time초를 추가
        future_time = now + timedelta(seconds=total_time)
        
        # 도착 시간 저장
        arrivalTime =  f"예상 도착 시간:{future_time.hour}시 {future_time.minute}분"
        
        # 초 단위로 얻은 소요 시간을 시, 분, 초로 나누어 저장
        if total_time > 60:
            min = total_time // 60
            sec = total_time % 60
            if min > 60:
                hour = min // 60
                min = min % 60
                total_time = str(hour) + "시간 " + str(min) + "분 " + str(sec) + "초"
            else:
                total_time = str(min) + "분 " + str(sec) + "초"
        else:
            total_time = str(total_time) + "초"
        requireTime = f"예상 이동 시간: {total_time}"
        
        #마커 생성
        start_marker = folium.Marker(location=path_coordinates[0], popup=folium.Popup('<strong>출발지</strong><br>'+requireTime, max_width=300, show=True), icon=folium.Icon(color='green'))
        end_marker = folium.Marker(location=path_coordinates[-1], popup=folium.Popup('<strong>집</strong><br>'+arrivalTime, max_width=300, show=True), icon=folium.Icon(color='red'))

        #km 계산
        total_distance = sum([feature["properties"]["totalDistance"] for feature in routes_info if "totalDistance" in feature["properties"]])
        total_distance_km = total_distance / 1000  # 미터를 킬로미터로 변환

        #km 정도에 따라 map_zoom 수치 조절
        if 0 <= total_distance_km <= 15:
            zoom_level = 13
        elif 15.1 <= total_distance_km <= 30:
            zoom_level = 12
        elif 30.1 <= total_distance_km <= 110:
            zoom_level = 11
        elif 110.1 <= total_distance_km <= 230:
            zoom_level = 10
        elif 230.1 <= total_distance_km <= 400:
            zoom_level = 9
        else:
            zoom_level = 8
        
        # Folium 지도 객체를 생성
        map = folium.Map(location=[midpoint_lat, midpoint_lon], zoom_start=zoom_level)
        
        # 출발지와 도착지 마커를 지도에 추가
        start_marker.add_to(map)
        end_marker.add_to(map)
        
        # Folium의 PolyLine을 사용하여 지도에 선을 그립니다.
        folium.PolyLine(path_coordinates, color="green", weight=3, opacity=1).add_to(map)

        # 지도를 HTML 파일로 저장합니다.
        map.save("route.html")
        
        # 크롬 드라이버를 설정합니다.
        driver = webdriver.Chrome()
                        
        #브라우저 창 크기 설정
        driver.set_window_size(1920, 1080)
                        
        # HTML 파일의 경로를 지정합니다. 파일이 위치한 경로를 정확하게 입력해야 합니다.
        file_path = 'file://' + os.path.realpath('route.html')
        # 크롬에서 HTML 파일을 엽니다.
        driver.get(file_path)

        # 5초간 대기합니다.
        time.sleep(10)

        # 현재 탭을 닫습니다.
        driver.close()
        
    else:
        print("Error:", response.status_code)