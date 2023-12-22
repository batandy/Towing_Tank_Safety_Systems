import os
import sys
import cv2
import time
import torch
import psutil
import argparse
import numpy as np
from pathlib import Path
from collections import Counter
import torch.backends.cudnn as cudnn
from utils.general import set_logging
from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, time_sync
from PIL import Image, ImageTk
import tkinter as tk


FILE = Path(__file__).resolve()
ROOT = FILE.parents[0] 
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT)) 
ROOT = Path(os.path.relpath(ROOT, Path.cwd())) 


import skimage
from sort import *
pts=[]
track_ids={}


def bbox_rel(*xyxy):
    bbox_left = min([xyxy[0].item(), xyxy[2].item()])
    bbox_top = min([xyxy[1].item(), xyxy[3].item()])
    bbox_w = abs(xyxy[0].item() - xyxy[2].item())
    bbox_h = abs(xyxy[1].item() - xyxy[3].item())
    x_c = (bbox_left + bbox_w / 2)
    y_c = (bbox_top + bbox_h / 2)
    w = bbox_w
    h = bbox_h
    return x_c, y_c, w, h

palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)
def compute_color_for_labels(label):
    color = [int(int(p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)

def is_point_inside_polygon(point, polygon, id):
    global track_ids
    x, y = point
    polygon = np.array(polygon, np.int32)
    is_in = cv2.pointPolygonTest(polygon, (x, y), False) > 0
    if is_in==True and track_ids[id] == 0:
        track_ids[id] = 1
    if is_in==False and track_ids[id] == 1:
        track_ids[id] = 2
    return is_in

def check_for_one(dictionary):
    return any(value == 1 for value in dictionary.values())



#바운딩 박스 그리기
def draw_boxes(img, bbox, identities=None, categories=None, 
                names=None, offset=(0, 0)):
    global is_inside, cnt, prevent, inside_polygon, pts, track_ids
    for i, box in enumerate(bbox):
        x1, y1, x2, y2 = [int(i) for i in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]
        cat = int(categories[i]) if categories is not None else 0
        id = int(identities[i]) if identities is not None else 0
        data = (int((box[0]+box[2])/2),(int((box[3]))))
        label = names[cat] + str(id)
        if id not in track_ids:
            track_ids[id]=0

        color = compute_color_for_labels(id)
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(img, (x1, y1), (x2, y2),color, 2)
        cv2.rectangle(img, (x1, y1 - 20), (x1 + w, y1), (255,191,0), -1)
        cv2.putText(img, label, (x1, y1 - 5),cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
        [255, 255, 255], 1)
        cv2.circle(img, data, 3, data,-1)
            
        
        if names[cat] == "Drowning":         #Drowning 탐지 시 빨간색
            DrawnAlarm = img.copy()
            #DrawnAlarm[:,:] = (57,131,255)
            DrawnAlarm[:,:] = (0,0,255)
            Drawn_dst = cv2.addWeighted(img, 0.7, DrawnAlarm, 0.3, 0)
            img[:,:]=Drawn_dst[:,:]

        elif names[cat]=="Human":
            if len(pts) !=0:
                is_in = is_point_inside_polygon(data, pts, id)
                if check_for_one(track_ids) and is_in:
                    alarm = img.copy()
                    #alarm[:,:] = (57,131,255)  #ROI 진입 시 주황색
                    alarm[:,:] =(57,255,236) #노랑색
                    dst = cv2.addWeighted(img, 0.5, alarm, 0.5, 0)
                    img[:,:]=dst[:,:]

        elif names[cat] == "Swimming":           #Swimming 탐지 시 핑크색
            SwimAlarm = img.copy()
            SwimAlarm[:,:] = (203,153,255)
            Swim_dst = cv2.addWeighted(img, 0.5, SwimAlarm, 0.5, 0)
            img[:,:]=Swim_dst[:,:]

    return img
#..............................................................................
##roi 관련 함수
roi_confirmed = False  # ROI 영역이 확정되었는지 여부를 나타내는 플래그
# 마우스 이벤트 콜백 함수
def draw_roi(event, x, y, flags, param):
    global roi_confirmed
    global pts

    if event == cv2.EVENT_LBUTTONDOWN:  # 왼쪽 버튼 클릭하면 점 추가
        pts.append((x, y))

    if event == cv2.EVENT_RBUTTONDOWN:  # 오른쪽 버튼 클릭하면 가장 최근에 추가한 점 제거
        pts.pop()

@torch.no_grad()
def detect(weights=ROOT / 'yolov5s.pt',
        source=ROOT / 'yolov5/data/images', 
        data=ROOT / 'data/coco128.yaml',  
        stframe=None,
        imgsz=(640, 640),
        conf_thres=0.25,
        iou_thres=0.25,  
        max_det=1000,  
        device='cpu',  
        view_img=False,
        save_txt=False, 
        save_conf=False, 
        save_crop=False, 
        nosave=False,  
        classes=None,  
        agnostic_nms=False,  
        augment=False,  
        visualize=False,  
        update=False,  
        project=ROOT / 'runs/detect',  
        name='exp',  
        exist_ok=False,  
        line_thickness=2,  
        hide_labels=False,  
        hide_conf=False,  
        half=False, 
        dnn=False,
        display_labels=False,
        ):
    save_img = not nosave and not source.endswith('.txt') 

    #.... Initialize SORT .... 
    sort_max_age = 5 
    sort_min_hits = 2
    sort_iou_thresh = 0.2
    sort_tracker = Sort(max_age=sort_max_age,
                       min_hits=sort_min_hits,
                       iou_threshold=sort_iou_thresh) 
    track_color_id = 0
    #......................... 

    # ------------------------- ROI ------------------------
    if source == '0':
        video_name='webcam'
    else:
        start_index = source.rfind('/') + 1
        end_index = source.rfind('.')
        video_name = source[start_index:end_index]
    file_path = f"roi_coor/{video_name}.txt"
    global pts

    if os.path.isfile(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
            pts = [tuple(map(int, line.strip().split(','))) for line in lines]

    
    webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
        ('rtsp://', 'rtmp://', 'http://', 'https://'))

    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  

    set_logging()
    device = select_device(device)
    half &= device.type != 'cpu'  

    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data)
    stride, names, pt, jit, onnx, engine = model.stride, model.names, model.pt, model.jit, model.onnx, model.engine
    imgsz = check_img_size(imgsz, s=stride)  

    half &= (pt or jit or onnx or engine) and device.type != 'cpu'  
    if pt or jit:
        model.model.half() if half else model.model.float()

    if webcam:
        cudnn.benchmark = True  
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt)
        bs = len(dataset) 
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt)
        bs = 1 
    vid_path, vid_writer = [None] * bs, [None] * bs
    
    t0 = time.time()
    
    dt, seen = [0.0, 0.0, 0.0], 0
    for path, im, im0s, vid_cap, s in dataset:
        t1 = time_sync()
        im = torch.from_numpy(im).to(device)
        im = im.half() if half else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        t2 = time_sync()
        dt[0] += t2 - t1

        # Inference
        visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
        pred = model(im, augment=augment, visualize=visualize)
        t3 = time_sync()
        dt[1] += t3 - t2

        # NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
        dt[2] += time_sync() - t3

        
        for i, det in enumerate(pred):  # per image
            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            points = np.array(pts, np.int32)
            cv2.polylines(im0, [points], True, (255, 255, 255), 2)


            p = Path(p)
            save_path = str(save_dir / p.name)
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            s += '%gx%g ' % im.shape[2:]
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]
            imc = im0.copy() if save_crop else im0
            annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            if len(det):
                det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "

                dets_to_sort = np.empty((0,6))
                
                # NOTE: We send in detected object class too
                for x1,y1,x2,y2,conf,detclass in det.cpu().detach().numpy():
                    dets_to_sort = np.vstack((dets_to_sort, 
                                              np.array([x1, y1, x2, y2, 
                                                        conf, detclass])))
                 
                # Run SORT
                tracked_dets = sort_tracker.update(dets_to_sort)
                tracks =sort_tracker.getTrackers()

                # draw boxes for visualization
                if len(tracked_dets)>0:
                    bbox_xyxy = tracked_dets[:,:4]
                    identities = tracked_dets[:, 8]
                    categories = tracked_dets[:, 4]
                    draw_boxes(im0, bbox_xyxy, identities, categories, names)

            
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:
                    if vid_path != save_path: 
                        vid_path = save_path
                        if isinstance(vid_writer, cv2.VideoWriter):
                            vid_writer.release()  
                        if vid_cap: 
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                            save_path += '.mp4'
                        vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    vid_writer.write(im0)
            
        stframe.image(im0, channels="BGR",use_column_width=True)
        
    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        print(f"Results saved to {save_dir}{s}")

    if update:
        strip_optimizer(weights)
    
    if vid_cap:
        vid_cap.release()
