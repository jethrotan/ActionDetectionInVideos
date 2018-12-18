import torch
from torch.autograd import Variable
import torch.nn.functional as F
import torchvision.transforms as transforms

import torch.nn as nn
import torch.utils.data
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import math
import copy

import os, sys
def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)

this_dir = os.path.dirname(__file__)
lib_path = os.path.join(this_dir, 'AlphaPose')
add_path(lib_path)

from opt import opt
# from dataloader import Image_loader, VideoDetectionLoader, DataWriter, crop_from_dets, Mscoco, DetectionLoader
from dataloader import *
from yolo.util import write_results, dynamic_write_results
from SPPE.src.main_fast_inference import *
from SPPE.src.utils.eval import getPrediction_batch
from SPPE.src.utils.img import load_image
import os
import time
from fn import getTime
import cv2
import random

from pPose_nms import pose_nms, write_json

import json
from yolo.darknet import Darknet

args = opt
args.dataset = 'coco'


class Alphapose_skeleton:
    def __init__(self):

        self.time_det = 0.0
        self.target_kps = [5, 6, 7, 8, 9, 10]

        # Load yolo detection model
        print('Loading YOLO model..')
        self.det_model = Darknet("AlphaPose/yolo/cfg/yolov3.cfg")
        self.det_model.load_weights('AlphaPose/models/yolo/yolov3.weights')
        self.det_model.cuda()
        self.det_model.eval()

        # Load pose model
        print('Loading Alphapose pose model..')
        pose_dataset = Mscoco()
        if args.fast_inference:
            self.pose_model = InferenNet_fast(4 * 1 + 1, pose_dataset)
        else:
            self.pose_model = InferenNet(4 * 1 + 1, pose_dataset)
        self.pose_model.cuda()
        self.pose_model.eval()


    def run(self, folder_or_imglist, heatmap_folder=None):
        if type(folder_or_imglist) == 'str':
            inputpath = folder_or_imglist
            print(inputpath)
            args.inputpath = inputpath

            # Load input images
            im_names = [img for img in sorted(os.listdir(inputpath)) if img.endswith('jpg')]
            dataset = Image_loader(im_names, format='yolo')
        else:
            imglist = folder_or_imglist
            dataset = Image_loader_from_images(imglist, format='yolo')

        # Load detection loader
        test_loader = DetectionLoader(dataset, self.det_model).start()

        skeleton_list = []
        # final_result = []
        for i in range(dataset.__len__()):
            with torch.no_grad():
                (inp, orig_img, im_name, boxes, scores) = test_loader.read()

                if boxes is None or boxes.nelement() == 0:
                    skeleton_result = None
                else:
                    # Pose Estimation
                    time1 = time.time()
                    inps, pt1, pt2 = crop_from_dets(inp, boxes)
                    inps = Variable(inps.cuda())

                    hm = self.pose_model(inps)
                    hm_data = hm.cpu().data

                    # if heatmap_folder is not None:
                    #     heatmap = hm_data.numpy()
                    #     print(heatmap.shape)
                    #     for h in range(heatmap.shape[0]):
                    #         heatmap_hand = heatmap[h][self.target_kps[0]]
                    #         for kk in self.target_kps[1:]:
                    #             heatmap_hand += heatmap[0][kk]

                            # outputpath = heatmap_folder+'_'+str(h+1)
                            # if not os.path.exists(outputpath):
                            #     os.mkdir(outputpath)

                            # heatmap_hand *= 255
                            # heatmap_hand[heatmap_hand < 0.0] = 0.0
                            # heatmap_hand = heatmap_hand.astype(np.int8)
                            # # print(np.amax(heatmap_hand), np.amin(heatmap_hand))
                            # cv2.imwrite(os.path.join(outputpath, im_name), heatmap_hand)

                            # cv2.imshow('orig_img', orig_img)
                            # cv2.imshow('skeletons', heatmap_hand)
                            # cv2.waitKey()

                    preds_hm, preds_img, preds_scores = getPrediction(
                            hm_data, pt1, pt2, args.inputResH, args.inputResW, args.outputResH, args.outputResW)

                    skeleton_result = pose_nms(boxes, scores, preds_img, preds_scores)
                    self.time_det += (time.time() - time1)

                # results = {
                #         'imgname': im_name.split('/')[-1],
                #         'result': skeleton_result
                #     }
                # final_result.append(results)

                skeleton_list.append([im_name.split('/')[-1]])
                if skeleton_result is not None:
                    for human in skeleton_result:
                        kp_preds = human['keypoints']
                        kp_scores = human['kp_score']

                        for n in range(kp_scores.shape[0]):
                            skeleton_list[-1].append(int(kp_preds[n, 0]))
                            skeleton_list[-1].append(int(kp_preds[n, 1]))
                            skeleton_list[-1].append(round(float(kp_scores[n]), 2))

        return skeleton_list

    def runtime(self):
        return self.time_det

    def save_skeleton(self, skeleton_list, outputpath):

        if not os.path.exists(outputpath):
            os.mkdir(outputpath)

        out_file = open(os.path.join(outputpath, 'skeleton.txt'), 'w')
        for skeleton in skeleton_list:
            out_file.write(' '.join(str(x) for x in skeleton))
            out_file.write('\n')
        out_file.close()


if __name__ == "__main__":

    base_folder = '/media/qcxu/qcxuDisk/Dataset/scratch_dataset/'
    __action__ = ['others', 'pick', 'scratch']

    # base_folder = '/media/qcxu/qcxuDisk/windows_datasets_all/clips/'
    # __action__ = ['normal', 'clean', 'pick', 'scratch']

    # get skeleton
    skeleton_det = Alphapose_skeleton()
    for act in __action__:

        base_in_clip_folder = base_folder + act + '/clips/'
        base_skeleton_folder = base_folder + act + '/skeletons/'
        base_heatmap_folder = base_folder + act + '/heatmap/'

        for sub_id, sub in enumerate(os.listdir(base_in_clip_folder)):

            if sub != 'Video_11_1_1':
                continue

            in_clip_folder = base_in_clip_folder + sub
            skeleton_folder = base_skeleton_folder + sub
            heatmap_folder = base_heatmap_folder + sub

            imglist = []
            for img_name in os.listdir(in_clip_folder):
                if img_name.endswith('jpg'):
                    imglist.append(cv2.imread(os.path.join(in_clip_folder, img_name)))

            skeleton_list = skeleton_det.run(imglist, heatmap_folder)
            skeleton_det.save_skeleton(skeleton_list, skeleton_folder)
