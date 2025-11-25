import collections
import os
import time
import uuid
from time import sleep
import requests
from minio.error import S3Error
from ultralytics import YOLO
import cv2
import log_config
import models_config
import minio_config
import posts_config
import base64

DETECT_INTERVAL = 20 #每隔多少帧抽一帧
SAVE_LENTH = 3 #保存报警帧前后多少秒
ROOT_PATH = os.path.dirname(os.getcwd())
TEMP_FILE = rf"{ROOT_PATH}\TEMP"
TEMP_VIDEO = rf"{TEMP_FILE}\temp_video.mp4" #视频本地临时储存地址


class Task:
    def __init__(self, request: posts_config.request_start, detect_id):
        self.detect_id =detect_id
        self.streamings = request.listStreamings
        self.time = request.time
        self.model_types = request.modelTypes
        self.is_processing = False
        self.response_url = ''
        self.frame_pre = ''
        self.frame_post = ''
        self.last_sent_time=0
        self.send_interval=request.time

    def detect(self,frame,model:str):
        results = YOLO(models_config.MODELS_PATH_BY_NAME[model]).predict(source=frame, save=False, show=False, save_txt=False)
        for result in results:
            for box in result.boxes:
                if int(box.cls[0]) in models_config.MODELS_LABELS_BY_NAME[model]:
                    return result
        return None

    #def image_to_minio(self,file):
    #    found = minio_config.minio_client.bucket_exists(minio_config.bucketName)
    #    if not found:
    #        minio_config.minio_client.make_bucket(minio_config.bucketName)
    #    local_file_path = file  # 本地图片路径
    #    object_name =f"image/IotVideo/videoUrl/{str(uuid.uuid4())}.jpg"  # 图片在MinIO存储桶中的路径和名称
    #    try:
    #        minio_config.minio_client.fput_object(minio_config.bucketName, object_name, local_file_path)
    #        return object_name
    #    except S3Error as exc:
    #        print("上传失败:", exc)
    #        return None

    def image_to_base64(self,image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def send_response(self,model:str,stream : str):
        response = posts_config.response_alarm(
            alarmContentUrl=self.image_to_base64(self.frame_pre),
            alarmContentExtUrl=self.image_to_base64(self.frame_post),
            alarmInfo=model,
            alarmTime=time.strftime("%Y%m%d%H%M%S"),
            detectId=self.detect_id
        )
        res= posts_config.resonse_alarm(iotAiAlarmRecordDto=response)
        log_config.logging.info(f"alarm send: {model}\turl:{stream}")
        print(f"alarm send: {model}\turl:{stream}")
        #requests.post(posts_config.RECEIVE_URL, json=jsonable_encoder(res), headers=minio_config.headers)

    def download_if_needed(self,url:str):#判断是收到的是视频下载地址，视频流还是本地视频
        stream_keywords = ['hls', 'rtmp', 'm3u8', 'stream', 'live']

        if os.path.isfile(url):
            return url  #如果是本地视频直接使用

        if any(keyword in url.lower() for keyword in stream_keywords):
            return url #如果是视频流直接使用

        else:
            response = requests.get(url, stream=True)
            with open(TEMP_VIDEO, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            return TEMP_VIDEO#如果是视频下载地址下载后使用

    def process(self):
        try:
            self.is_processing = True
            for stream in self.streamings:
                if not self.is_processing:
                    break
                stream = self.download_if_needed(stream)#判断一下地址类型，变为可以直接cv处理的类型

                alarm_count=0
                cap = cv2.VideoCapture(stream, cv2.CAP_FFMPEG)
                fps = cap.get(cv2.CAP_PROP_FPS)
                clip_frames = int(fps * SAVE_LENTH)  # 当前帧前后需要存的帧数
                buffer_size = int(fps * SAVE_LENTH)  # 缓冲区，放前几秒的
                last_trigger_frame = -self.send_interval * fps# 上次报警时间，初始化为足够早的时间
                frame_count = 0
                buffer = collections.deque(maxlen=buffer_size)
                recording = False
                recording_frames = 0
                out = None
                clip_count = 0

                while self.is_processing:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    buffer.append((frame_count, frame.copy()))
                    if frame_count % DETECT_INTERVAL == 0 and frame_count - last_trigger_frame >= self.send_interval * fps:  # 每隔开DETECT_INTERVAL抽1帧检测,且间隔足够
                        # 轮流使用所有模型进行检测，每种模型至少有一项报警即会发送报警，检测到的报警后有一段时间的冷却
                        #cv2.imwrite(TEMP_VIDEO, frame)
                        for model in self.model_types:
                            result = self.detect(frame, model)
                            if result:  # 如果监测有结果

                                alarm_count += 1
                                last_trigger_frame = frame_count
                                recording = True
                                recording_frames = 0
                                clip_count += 1

                                # 保存当前帧前后监测情况图
                                now = time.time()
                                self.frame_pre = os.path.join(TEMP_FILE, f"pre_{self.detect_id}_{alarm_count}.jpg")
                                self.frame_post = os.path.join(TEMP_FILE, f"post_{self.detect_id}_{alarm_count}.jpg")
                                cv2.imwrite(self.frame_pre, frame)
                                cv2.imwrite(self.frame_post, result[0].plot())

                                #保存前save_lenth秒
                                out = cv2.VideoWriter(
                                    f"{TEMP_FILE}/clip_{self.detect_id}_{alarm_count}.avi",
                                    cv2.VideoWriter_fourcc(*'DIVX'),
                                    fps,
                                    (int(cap.get(3)), int(cap.get(4)))
                                )
                                for idx, buffered_frame in buffer:
                                    out.write(buffered_frame)

                                log_config.logging.info(f'alarm detected:\ncount:{alarm_count}\nstreamId:{self.detect_id}\nalarm:{model}\nurl: {stream}')
                                print(f"监测到报警：\ncount:{alarm_count}\n监测ID：{self.detect_id}\n报警名称：{model}\n视频流：{stream}")
                                self.send_response(model,stream)
                            elif not recording:
                                print("无报警")

                    if recording:#找到后短时间不会报警但会保存后save_lenth秒
                        out.write(frame)
                        recording_frames += 1
                        # 如果已录制超过时长，结束录制
                        if recording_frames >= clip_frames:
                            recording = False
                            out.release()
                            out = None
                    frame_count += 1
                if out is not None:
                    out.release()
                cap.release()
        except Exception as e:
            log_config.logging.info(f'task wrong:{self.streamings}: {str(e)}')
            print(f"URL invalid:{self.streamings}: {str(e)}")
        finally:
            self.is_processing = False
