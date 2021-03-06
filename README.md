# Fine Grained Visual Classification

This repository aims to improve future object detection methods making use of scene depth maps.<br>
The model uses ResNet to extract object features based on rgb and depth channels. It also uses<br>
FCNHead to obtain a segmentation map based on these features.<br>

## Requirements

Python 3.8 or later with all [requirements.txt](https://github.com/alexjercan/fine-grained-visual-classification/blob/master/requirements.txt) dependencies installed, including `torch>=1.7.1`. To install run:
```bash
$ pip install -r requirements.txt
```

## Training
Use [BlenderRenderer](https://github.com/onorabil/blenderRenderer) to generate the dataset.
```bash
$ train.py [-h] [--dataset_path DATASET_PATH] [--epochs EPOCHS] [--batch_size BATCH_SIZE]
                [--learning_rate LEARNING_RATE] [--use_gpu] [--output_path OUTPUT_PATH] [--checkpoint CHECKPOINT]
                [--resnet] [--pretrained]
$ test.py [-h] [--dataset_path DATASET_PATH] [--batch_size BATCH_SIZE] [--use_gpu] [--checkpoint CHECKPOINT]
               [--resnet]
$ show.py [-h] [--dataset_path DATASET_PATH] [--batch_size BATCH_SIZE] [--use_gpu] [--checkpoint CHECKPOINT]
               [--resnet]
```

--dataset_path DATASET_PATH: Should point to the dataset generated by BlenderRenderer or a dataset with the same strucuture.<br>
--epochs EPOCHS: Represents the epoch at which the training stops.<br>
--batch_size BATCH_SIZE<br>
--learning_rate LEARNING_RATE<br>
--use_gpu: Use this flag to use gpu.<br>
--output_path OUTPUT_PATH: Represents the output path for the checkpoint.<br>
--checkpoint CHECKPOINT: Checkpoint file to resume training.<br>
--resnet: Use this flag to train without depth maps.<br>
--pretrained: Use this flag to get a pretrained ResNet model.<br>

## Results

One epoch training acc: 81%
![alt text](https://i.imgur.com/s1w2Iyq.png)




