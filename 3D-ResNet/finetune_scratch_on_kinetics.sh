
base_folder=/media/qcxu/qcxuDisk/Dataset/scratch_dataset

#### Generate n_frames files using utils/n_frames_ucf101_hmdb51.py
# python utils/n_frames_ucf101_hmdb51.py ${base_folder}/hand

#### Generate annotation file in json format similar to ActivityNet using utils/ucf101_json.py
python utils/scratch_json.py ${base_folder}/TrainTestlist


# #### finetune
# python main.py --root_path ./data \
# --video_path ${base_folder}/hand \
# --annotation_path ${base_folder}/TrainTestlist/ucf101_01.json \
# --result_path results --dataset ucf101 --n_classes 400 --n_finetune_classes 3 \
# --pretrain_path models/resnet-18-kinetics.pth --ft_begin_index 4 \
# --model resnet --model_depth 18 --resnet_shortcut A --batch_size 16 --n_threads 4 --checkpoint 5