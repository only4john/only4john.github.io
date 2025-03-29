import cv2
import git
import os
import re
import time

repo_path = '/Users/feiteng/Documents/GitHub/only4john.github.io'
file_path = 'zh/index_zh.md'
github_url = 'https://github.com/only4john/only4john.github.io.git'
commit_message = "Update office status."
font_size = "16px"
face_cascade = cv2.CascadeClassifier('/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml')  # 或者你系统中 haarcascade 文件的路径
image_path = '/Users/feiteng/Documents/GitHub/only4john.github.io/last_face.jpg' # 保存最后检测到人脸的照片路径
camera_index = 0 # 摄像头的索引，默认为0，如果您的电脑有多个摄像头，请尝试更改这个数字

def update_github_page(in_office):
    try:
        repo = git.Repo(repo_path)
        index_file_path = os.path.join(repo_path, file_path)

        with open(index_file_path, 'r') as f:
            lines = f.readlines()

        #print("Original lines:", lines)

        # 定位到 "## 费  腾  FEI Teng" 行的位置
        name_line_index = -1
        for i, line in enumerate(lines):
            if "## 费&ensp;&ensp;腾&ensp;&ensp;FEI Teng" in line:
                name_line_index = i
                break

        if name_line_index != -1:
            if in_office:
                status_text = "我在办公室里"
                status_html = f' (<span style="color: green; font-size: {font_size};">&#x25CF;</span> <span style="font-size: {font_size};">{status_text}</span>)'
            else:
                status_text = "我不在办公室里"
                status_html = f' (<span style="color: red; font-size: {font_size};">&#x25CF;</span> <span style="font-size: {font_size};">{status_text}</span>)'
            
            # 删除之前添加的状态信息
            lines[name_line_index] = re.sub(rf' \(<span style="color: (green|red); font-size: {font_size};">&#x25CF;<\/span> <span style="font-size: {font_size};">(我在|我不在)办公室里<\/span>\)', '', lines[name_line_index])

            # 将状态信息添加到姓名行末尾
            lines[name_line_index] = lines[name_line_index].rstrip() + f'{status_html}\n'

        #print("Modified lines:", lines)

        with open(index_file_path, 'w') as f:
            f.writelines(lines)

        repo.git.add(file_path)
        repo.git.commit(m=commit_message)
        origin = repo.remote(name='origin')
        origin.push()
        print('GitHub page updated successfully!')
    except Exception as e:
        print(f'Error updating GitHub page: {e}')

# 主循环
cap = cv2.VideoCapture(camera_index)  # 使用默认摄像头

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

last_face_detected = False  # 初始状态：未检测到人脸

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if len(faces) > 0:
        print("Face detected!")
        cv2.imwrite(image_path, frame)  # 保存当前帧
        if not last_face_detected:
            update_github_page(True)
            last_face_detected = True
    else:
        print("No face detected.")
        if last_face_detected:
            update_github_page(False)
            last_face_detected = False
    
    time.sleep(600)  # 10 分钟 = 600 秒

cap.release()
cv2.destroyAllWindows()