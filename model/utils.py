import torch.nn as nn
from torchvision.models.resnet import BasicBlock, Bottleneck, conv1x1

class ResNetModule(nn.Module):

    def __init__(self, block, layers, zero_init_residual=False, out_size=512):
        super(ResNetModule, self).__init__()
        self.inplanes = 64
        self.conv3 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3,
                               bias=False)
        self.bn64 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512 * block.expansion, out_size)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(
                    m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

        # Zero-initialize the last BN in each residual branch,
        # so that the residual branch starts with zeros, and each residual block behaves like an identity.
        # This improves the model by 0.2~0.3% according to https://arxiv.org/abs/1706.02677
        if zero_init_residual:
            for m in self.modules():
                if isinstance(m, Bottleneck):
                    nn.init.constant_(m.bn3.weight, 0)
                elif isinstance(m, BasicBlock):
                    nn.init.constant_(m.bn2.weight, 0)

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                conv1x1(self.inplanes, planes * block.expansion, stride),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv3(x)
        x = self.bn64(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        x = self.relu(x)

        return x


class DepthModule(nn.Module):

    def __init__(self, out_size=512):
        super(DepthModule, self).__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=11, stride=2, padding=5,
                               bias=False)
        self.conv16 = nn.Conv2d(16, 64, kernel_size=11, stride=4, padding=5,
                                bias=False)
        self.bn16 = nn.BatchNorm2d(16)
        self.bn64 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.fc = nn.Linear(4096, out_size)

    def forward(self, y):
        y = self.conv1(y)
        y = self.bn16(y)
        y = self.relu(y)
        y = self.maxpool(y)

        y = self.conv16(y)
        y = self.bn64(y)
        y = self.relu(y)
        y = self.maxpool(y)

        y = y.view(y.size(0), -1)
        y = self.fc(y)
        y = self.relu(y)

        return y