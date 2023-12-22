import cv2
import numpy as np
import os

pts = []  # 좌표를 저장하는 리스트
roi_confirmed = False  # ROI 영역이 확정되었는지 여부를 나타내는 플래그
file_read = False

# 파일이 존재하면 파일에서 좌표를 읽어옴
file_path = "roi_coordinates.txt"
if os.path.isfile(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
        pts = [tuple(map(int, line.strip().split(','))) for line in lines]
    roi_confirmed = True

# 마우스 이벤트 콜백 함수
def draw_roi(event, x, y, flags, param):
    global roi_confirmed
    img2 = frame.copy()

    if not roi_confirmed:
        if event == cv2.EVENT_LBUTTONDOWN:  # 왼쪽 버튼 클릭하면 점 추가
            pts.append((x, y))

        if event == cv2.EVENT_RBUTTONDOWN:  # 오른쪽 버튼 클릭하면 가장 최근에 추가한 점 제거
            pts.pop()

        if event == cv2.EVENT_MBUTTONDOWN:  # 가운데 버튼 클릭하면 ROI 확정
            roi_confirmed = True



def is_point_inside_polygon(point, polygon):
    x, y = point
    polygon = np.array(polygon, np.int32)
    return cv2.pointPolygonTest(polygon, (x, y), False) > 0


# 동영상 열기
cap = cv2.VideoCapture('video/2.mp4')

print("[INFO] 왼쪽 클릭: 점 추가, 오른쪽 클릭: 가장 최근 점 제거, 'M' 키: ROI 영역 확정")
print("[INFO] 'S' 키: 선택 영역 저장 및 종료")
print("[INFO] 'ESC' 키: 종료")

while True:
    # 다음 프레임 읽기
    ret, frame = cap.read()
    # 동영상 끝에 도달하면 종료
    if not ret:
        print('영상이 끝났습니다.')
        break

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        print(is_inside)
        break
    if key == ord("s") and roi_confirmed:
        # 텍스트 파일에 좌표 저장
        with open("roi_coordinates.txt", "w") as file:
            for point in pts:
                file.write(f"{point[0]}, {point[1]}\n")
        print("[INFO] ROI 좌표가 로컬 파일에 저장되었습니다.")
        break
    if key == ord("m"):
        roi_confirmed = True

    if roi_confirmed==False:
        cv2.imshow('video', frame)
        cv2.setMouseCallback('video', draw_roi)

    point = (400, 700)  # 찍고자 하는 좌표 (x, y)  #-> 현재 좌표 가지고 오기

    if roi_confirmed:
        mask = np.zeros(frame.shape, np.uint8)
        points = np.array(pts, np.int32)
        # 다각형 그리기
        mask = cv2.polylines(mask, [points], True, (255, 255, 255), 2)
        mask2 = cv2.fillPoly(mask.copy(), [points], (255, 255, 255))  # ROI 계산용
        mask3 = cv2.fillPoly(mask.copy(), [points], (0, 255, 0))  # 데스크탑에 표시할 이미지

        show_image = cv2.addWeighted(src1=frame, alpha=0.8, src2=mask3, beta=0.2, gamma=0)

        cv2.imshow("show_img", show_image)
        is_inside = is_point_inside_polygon(point, pts) #-> 현재 객체 좌표 가지고 와서 검사
    


cap.release()
cv2.destroyAllWindows()
