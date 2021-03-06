import torch
from torch.functional import Tensor
import torch.nn.functional as F
import torch.optim
import torchvision.transforms as transforms
from argparse import ArgumentParser
from dataset.blender_dataset import BlenderDataset
from torch.utils.data import DataLoader
from model.depthnet import depthnet152, depthnet18
from model.resnet import resnet152, resnet18
from time import time


def get_args():
    parser = ArgumentParser(
        description='Trains a nn using the blender dataset.')
    parser.add_argument('--dataset_path', type=str, default=None)
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--learning_rate', type=float, default=0.001)
    parser.add_argument('--use_gpu', action="store_true", default=False)
    parser.add_argument('--output_path', type=str, default='./checkpoint.pth')
    parser.add_argument('--checkpoint', type=str, default=None)
    parser.add_argument('--resnet', action="store_true", default=False)
    parser.add_argument('--pretrained', action="store_true", default=False)

    args = parser.parse_args()
    return args


def loss_function(prediction, target, num_classes) -> Tensor:
    p_labels, p_bboxes, p_seg_masks = prediction
    t_labels, t_bboxes, t_seg_masks = target

    loss_labels = F.cross_entropy(p_labels, t_labels, reduction="sum")

    loss_bboxes = F.l1_loss(p_bboxes, t_bboxes, reduction="none")
    loss_bboxes = loss_bboxes.sum(1).sum()

    loss_seg_masks = F.cross_entropy(
        p_seg_masks, t_seg_masks.squeeze(1), reduction="mean")

    loss: Tensor = loss_labels + loss_bboxes / num_classes + loss_seg_masks
    return loss


if __name__ == '__main__':
    args = get_args()

    use_cuda = torch.cuda.is_available() and args.use_gpu
    device = torch.device('cuda' if use_cuda else 'cpu')

    epoch = 0
    num_epochs = args.epochs
    batch_size = args.batch_size
    learning_rate = args.learning_rate

    render_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Resize((256, 256)),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])

    depth_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Resize((256, 256)),
        transforms.Normalize((0.5,), (0.5,)),
    ])

    seg_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Resize((256, 256)),
    ])

    train_dataset = BlenderDataset(root_dir=args.dataset_path, csv_fname='train.csv', class_fname='class.csv',
                                   render_transform=render_transform, depth_transform=depth_transform, albedo_transform=seg_transform, train=True)
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True)

    use_resnet = args.resnet
    pretrained = args.pretrained
    num_classes = train_dataset.num_classes
    model = (resnet18 if use_resnet else depthnet18)(pretrained=pretrained,
                                                     num_classes=num_classes, zero_init_residual=True)

    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)

    if args.checkpoint:
        checkpoint = torch.load(args.checkpoint, map_location=device)
        epoch = checkpoint["epoch"]
        model.load_state_dict(checkpoint["model_state"])
        optimizer.load_state_dict(checkpoint["optimizer_state"])

    model = model.to(device)

    n_total_steps = len(train_loader)
    for epoch in range(epoch, num_epochs):
        t1 = time()
        for i, (rgb_images, depth_images, t_labels, t_bboxes, t_seg_masks) in enumerate(train_loader):
            rgb_images: Tensor = rgb_images.to(device)
            depth_images: Tensor = depth_images.to(device)
            t_labels: Tensor = t_labels.to(device)
            t_bboxes: Tensor = t_bboxes.to(device)
            t_seg_masks: Tensor = t_seg_masks.to(device)
            target = (t_labels, t_bboxes, t_seg_masks)

            prediction = model(rgb_images, depth_images)
            loss = loss_function(prediction, target, num_classes)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if (i + 1) % 1000 == 0:
                print(
                    f'Epoch [{epoch + 1}/{num_epochs}], Step [{i + 1}/{n_total_steps}], Loss: {loss.item():.4f}')

        torch.save({
            "epoch": epoch + 1,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict()
        }, args.output_path)
        t2 = time()
        print(f'Epoch [{epoch + 1}/{num_epochs}], Step [{n_total_steps}/{n_total_steps}], Loss: {loss.item():.4f}, Time: {(t2 - t1):.4f}s')

    print('Finished Training')
