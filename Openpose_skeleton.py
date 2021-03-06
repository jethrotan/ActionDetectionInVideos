
import os
import sys
import time
import cv2
import json

# Remember to add your installation path here
import os, sys
def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)

this_dir = os.path.dirname(__file__)
lib_path = os.path.join(this_dir, 'openpose/build/python/openpose')
add_path(lib_path)

from openpose import *


class Openpose_skeleton:
    def __init__(self, cuda_id=0):

        self.time_det = 0.0
        self.time_run = 0.0

        # Load pose model
        print('Loading Openpose pose model..')
        params = dict()
        params["logging_level"] = 3
        params["output_resolution"] = "-1x-1"
        params["net_resolution"] = "-1x368"
        params["model_pose"] = "BODY_25"#"COCO"
        params["alpha_pose"] = 0.6
        params["scale_gap"] = 0.3
        params["scale_number"] = 1
        params["render_threshold"] = 0.05
        # If GPU version is built, and multiple GPUs are available, set the ID here
        params["num_gpu_start"] = 0
        params["disable_blending"] = False
        # Ensure you point to the correct path where models are located
        params["default_model_folder"] = 'openpose/models/'
        # Construct OpenPose object allocates GPU memory
        self.openpose = OpenPose(params)

        # skeletopn keypoint order
        # Nose, LEye, REye, LEar, REar
        # LShoulder, RShoulder, LElbow, RElbow, LWrist, RWrist
        # LHip, RHip, LKnee, Rknee, LAnkle, RAnkle, Neck
        # self.order = [0, 14, 15, 16, 17,
        #             2, 5, 3, 6, 4, 7,
        #             8, 11, 9, 12, 10, 13]
        self.order = [0, 15, 16, 17, 18,
                    2, 5, 3, 6, 4, 7,
                    9, 12, 10, 13, 11, 14]

    def run(self, folder_or_imglist, sample_rate):
        time_run_start = time.time()

        if type(folder_or_imglist) == 'str':
            inputpath = folder_or_imglist
            print(inputpath)

            imglist = []
            for im_name in os.listdir(inputpath):
                if im_name.endswith('jpg'):
                    imglist.append(cv2.imread(os.path.join(inputpath, im_name)))
        else:
            imglist = folder_or_imglist

        skeleton_list = []
        for i, img in enumerate(imglist):
            im_name = 'image_{:05d}.jpg'.format(i+1)
            
            time_det_start = time.time()
            if i % sample_rate == 0:
                keypoints, output_image = self.openpose.forward(img, True)
                pre_keypoints = keypoints
            else:
                keypoints = pre_keypoints
            self.time_det += (time.time() - time_det_start)

            skeleton_list.append([im_name.split('/')[-1]])
            if keypoints is not None:
                for keypoint in keypoints:
                    for n in range(len(self.order)):
                        skeleton_list[-1].append(int(keypoint[self.order[n]][0]))
                        skeleton_list[-1].append(int(keypoint[self.order[n]][1]))
                        skeleton_list[-1].append(round(float(keypoint[self.order[n]][2])))

        self.time_run += (time.time() - time_run_start)
        return skeleton_list

    def runtime(self):
        return self.time_det, self.time_run

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
    skeleton_det = Openpose_skeleton()

    time1 = time.time()
    for act in __action__:

        base_in_clip_folder = base_folder + act + '/clips/'
        base_skeleton_folder = base_folder + act + '/skeletons/'

        for sub_id, sub in enumerate(os.listdir(base_in_clip_folder)):

            if act != 'pick' or sub != 'Video_12_4_1':
                continue

            in_clip_folder = base_in_clip_folder + sub
            skeleton_folder = base_skeleton_folder + sub

            imglist = []
            for im_name in os.listdir(in_clip_folder):
                if im_name.endswith('jpg'):
                    imglist.append(cv2.imread(os.path.join(in_clip_folder, im_name)))

            skeleton_list = skeleton_det.run(imglist, sample_rate=1)
            # skeleton_det.save_skeleton(skeleton_list, skeleton_folder)
    print(time.time() - time1)