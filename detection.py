
# from Alphapose_skeleton import Alphapose_skeleton
from skeleton_tools import skeleton_tools
from action_recognition import action_recognition

import time
import os
import cv2
from PIL import Image


class detection:
    def __init__(self, reg_model_file, skeleton_opt='Openpose', is_vis=False, is_static_BG=False, thres=0.5):

        if skeleton_opt == 'MSRA':
            from MSRA_skeleton import MSRA_skeleton
            self.skeleton_det = MSRA_skeleton()
        elif skeleton_opt == 'Alphapose':
            from Alphapose_skeleton import Alphapose_skeleton
            self.skeleton_det = Alphapose_skeleton()
        elif skeleton_opt == 'Openpose':
            from Openpose_skeleton import Openpose_skeleton
            self.skeleton_det = Openpose_skeleton()
        else:
            raise Exception('Error: ' + skeleton_opt + ' could not be found')

        self.is_vis = is_vis
        self.is_static_BG = is_static_BG
        self.thres = thres

        self.st = skeleton_tools()
        self.reg = action_recognition(reg_model_file)
        print('=================== Initialized ===================\n\n')

        self.time_sk_det = 0.0
        self.time_st = 0.0
        self.time_reg = 0.0
        self.time_vis = 0.0

    def run(self, imglist):
        ### imglist: list of images read by opencv2

        # detect skeleton
        time1 = time.time()
        skeleton = self.skeleton_det.run(imglist)
        self.time_sk_det += (time.time() - time1)

        # prepare hand clip
        time1 = time.time()
        im_name_all, kp_preds_all, kp_scores_all = self.st.get_valid_skeletons(
            'None', in_skeleton_list=skeleton, is_savejson=False)
        # self.st.vis_skeleton('None', 'None', 'None.json',
        #     im_name_all, kp_preds_all, kp_scores_all, imglist,
        #     result_labels=None, is_save=False, is_vis=True, thres=0.3)
        clip_all = self.st.get_hand_clip('None', 'None', 'None', 'None.json',
            im_name_all, kp_preds_all, kp_scores_all, imglist,
            is_save=False, is_vis=self.is_vis, is_static_BG=self.is_static_BG)
        self.time_st += (time.time() - time1)

        # run action recornition
        time1 = time.time()
        result_labels = []
        for clip in clip_all:
            clip_PIL = [Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)) for img in clip]
            if clip_PIL is None or len(clip_PIL) == 0:
            	result_labels.append([0, [0.0, 0.0, 0.0]])
            else:
            	label, probs = self.reg.run(clip_PIL)
            	result_labels.append([label, probs])
        self.time_reg += (time.time() - time1)

        # visualize result
        time1 = time.time()
        img_out_all = self.st.vis_skeleton('None', 'None', 'None.json',
            im_name_all, kp_preds_all, kp_scores_all, imglist,
            result_labels=result_labels, is_save=False, is_vis=True, thres=self.thres)
        self.time_vis += (time.time() - time1)

        return img_out_all

    def print_runtime(self):
        print('\n\n=================== Time Analysis ===================')

        time_total = self.time_sk_det + self.time_st + self.time_reg + self.time_vis
        print('time pure skeleton:', '{:.4f}'.format(self.skeleton_det.runtime()))
        print('time_skeleton:', '{:.4f}'.format(self.time_sk_det), '{:.4f}'.format(self.time_sk_det / time_total))
        print('time_tool:', '{:.4f}'.format(self.time_st), '{:.4f}'.format(self.time_st / time_total))
        print('time_action:', '{:.4f}'.format(self.time_reg), '{:.4f}'.format(self.time_reg / time_total))
        print('time_visualise:', '{:.4f}'.format(self.time_vis), '{:.4f}'.format(self.time_vis / time_total))


if __name__ == "__main__":

    reg_model_file = 'results-scratch-18/save_200.pth'
    detection = detection(reg_model_file, skeleton_opt='Openpose', is_vis=False, is_static_BG=False, thres=0.9)

    base_folder = '/media/qcxu/qcxuDisk/Dataset/scratch_dataset/others/clips/Video_11_1_1'
    imglist = []
    for img_name in os.listdir(base_folder):
        if img_name.endswith('jpg'):
            imglist.append(cv2.imread(os.path.join(base_folder, img_name)))

    detection.run(imglist)
