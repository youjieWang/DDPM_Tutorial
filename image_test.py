import os
import numpy as np
import torchvision
import torch
import torchvision.transforms as transforms
from torch.optim import Adam
from utils.networkHelper import *

from noisePredictModels.Unet.UNet import Unet
from utils.trainNetworkHelper import SimpleDiffusionTrainer
from diffusionModels.simpleDiffusion.simpleDiffusion import DiffusionModel

# 数据集加载
data_root_path = "./dataset/"
if not os.path.exists(data_root_path):
    os.makedirs(data_root_path)

# 这边不需要做判断，里面的download已经做了一层判断了
# if not os.path.exists(os.path.join(data_root_path, "FashionMNIST")):
#     imagenet_data = torchvision.datasets.FashionMNIST(data_root_path, train=True, download=True, transform=transforms.ToTensor())
# else:
#     imagenet_data = torchvision.datasets.FashionMNIST(data_root_path, train=True, download=False, transform=transforms.ToTensor())
imagenet_data = torchvision.datasets.FashionMNIST(data_root_path, train=True, download=True, transform=transforms.ToTensor())

image_size = 28
channels = 1
batch_size = 2

data_loader = torch.utils.data.DataLoader(imagenet_data,
                                        batch_size=batch_size,
                                        shuffle=True,
                                        num_workers=0)

device = "cuda" if torch.cuda.is_available() else "cpu"
dim_mults = (1, 2, 4,)

denoise_model = Unet(
    dim=image_size,
    channels=channels,
    dim_mults=dim_mults
)


timesteps = 1000  # 定义推理的步数
schedule_name = "linear_beta_schedule"  # 定义推理的策略
DDPM = DiffusionModel(schedule_name=schedule_name,
                      timesteps=timesteps,
                      beta_start=0.0001,  # 这里的定义是根据论文中的定义
                      beta_end=0.02,
                      denoise_model=denoise_model).to(device)  # 初始化定义一些初始值，beta，alpha， 累成，根号累成，还有方差

optimizer = Adam(DDPM.parameters(), lr=1e-3)
epoches = 20

Trainer = SimpleDiffusionTrainer(epoches=epoches,
                                 train_loader=data_loader,
                                 optimizer=optimizer,
                                 device=device,
                                 timesteps=timesteps)


# 训练参数设置
root_path = "./saved_train_models"
setting = "imageSize{}_channels{}_dimMults{}_timeSteps{}_scheduleName{}".format(image_size, channels, dim_mults, timesteps, schedule_name)

saved_path = os.path.join(root_path, setting)
if not os.path.exists(saved_path):
    os.makedirs(saved_path)


# 训练好的模型加载，如果模型是已经训练好的，则可以将下面两行代码取消注释
# best_model_path = saved_path + '/' + 'BestModel.pth'
# DDPM.load_state_dict(torch.load(best_model_path))
    

# 如果模型已经训练好则注释下面这行代码，反之则注释上面两行代码
DDPM = Trainer(DDPM, model_save_path=saved_path)  # 模型训练

# 采样:sample 64 images
samples = DDPM(mode="generate", image_size=image_size, batch_size=64, channels=channels)  # 模型采样

# 随机挑一张显示
random_index = 1
# TODO 这边返回结果也下断点看一下
generate_image = samples[-1][random_index].reshape(channels, image_size, image_size)
figtest = reverse_transform(torch.from_numpy(generate_image))
figtest.save("./image.png")

