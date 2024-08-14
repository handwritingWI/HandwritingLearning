# -*- coding: utf-8 -*-
"""train_CTE_CERUG_dataaug.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ppQNHs5ajzRXfATVKlYGvIlAAvGfFYMt
"""

import random
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.optim import lr_scheduler
import matplotlib.pyplot as plt
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter
from sklearn.metrics import precision_recall_fscore_support
import shutil
import numpy as np
import os
import tarfile

from cte import *
from dataloader_cerug import *


class LabelSomCE(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x, target, smoothing=0.1):
        # Compute the loss with label smoothing
        confidence = 1.0 - smoothing
        logprobs = F.log_softmax(x, dim=-1)
        nll_loss = -logprobs.gather(dim=-1, index=target.unsqueeze(1))
        nll_loss = nll_loss.squeeze(1)
        smooth_loss = -logprobs.mean(dim=-1)
        loss = confidence * nll_loss + smoothing * smooth_loss

        return loss.mean()

def extract_local_tar(folder, thetarfile):
    # Open the tar file
    with tarfile.open(thetarfile, mode="r:gz") as tar:
        # Extract all contents to the specified folder
        tar.extractall(path=folder)


def download_cerug(folder):
    # Download the CERUG dataset
    local_tarfile = "/CERUG-EN-train-images.tar.gz"
    extract_local_tar(folder, local_tarfile)
    local_tarfile = "/CERUG-EN-test-images.tar.gz"
    extract_local_tar(folder, local_tarfile)


class ImageTransformer:
    def __init__(self, foldername, imgtype='png'):
        # Initialize the image transformer with folder and image type
        self.imgtype = imgtype
        self.folder = foldername
        self.imglist = self.get_imgList(self.folder)
        print(f'Image list: {self.imglist}')
        print(f'Number of images: {len(self.imglist)}')

    def get_imgList(self, folder):
        # Get a list of images in the specified folder
        return [img for img in os.listdir(folder) if img.endswith(self.imgtype)]

    def elastic_transform(self, image, alpha, sigma):
        # Apply elastic transformation to the image
        random_state = np.random.RandomState(None)
        shape = image.shape

        dx = gaussian_filter((random_state.rand(*shape) * 2 - 1), sigma, mode="constant", cval=0) * alpha
        dy = gaussian_filter((random_state.rand(*shape) * 2 - 1), sigma, mode="constant", cval=0) * alpha

        x, y = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), indexing='ij')
        indices = np.reshape(x + dx, (-1, 1)), np.reshape(y + dy, (-1, 1))

        distorted_image = map_coordinates(image, indices, order=1, mode='reflect').reshape(shape)
        return distorted_image

    def perspective_transform(self, image):
        # Apply perspective transformation to the image
        width, height = image.size
        coeffs = self.find_coeffs(
            [(0, 0), (width, 0), (width, height), (0, height)],
            [(random.randint(0, width // 4), random.randint(0, height // 4)),
             (width - random.randint(0, width // 4), random.randint(0, height // 4)),
             (width - random.randint(0, width // 4), height - random.randint(0, height // 4)),
             (random.randint(0, width // 4), height - random.randint(0, height // 4))]
        )
        return image.transform((width, height), Image.PERSPECTIVE, coeffs, Image.BICUBIC)

    def find_coeffs(self, pa, pb):
        # Calculate the coefficients for perspective transformation
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])

        A = np.matrix(matrix, dtype=float)
        B = np.array(pb).reshape(8)

        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return np.array(res).reshape(8)

    def process_and_save_images(self):
        # Process images with transformations and save them
        for imgfile in self.imglist:
            # Open the image
            image = Image.open(os.path.join(self.folder, imgfile)).convert('L')
            original_image = np.array(image)

            # Save original image
            original_image_filename = os.path.join(self.folder, imgfile)
            image.save(original_image_filename)

            # Elastic distortion
            elastic_image = self.elastic_transform(original_image, alpha=34, sigma=4)
            elastic_image = Image.fromarray(elastic_image).convert('L')
            elastic_image_filename = os.path.join(self.folder, imgfile.split('.')[0] + '_1.' + self.imgtype)
            elastic_image.save(elastic_image_filename)

            # Perspective transformation
            perspective_image = self.perspective_transform(image)
            perspective_image_filename = os.path.join(self.folder, imgfile.split('.')[0] + '_2.' + self.imgtype)
            perspective_image.save(perspective_image_filename)


class DeepWriter_Train:
    def __init__(self, dataset='CERUG-EN', imgtype='png'):
        # Initialize training with specified dataset and image type
        self.dataset = dataset
        self.folder = dataset
        #self.labelfolder = 'dataset/'

        if not os.path.exists(self.folder):
            # Download dataset if not available
            if dataset == 'CERUG-EN':
                download_cerug(dataset)
            elif dataset == 'Firemaker':
                download_firemaker(dataset)
            else:
                print('****** Warning: the dataset %s does not existed!******' % dataset)
                print('Please go to the following website to check how to download the dataset:')
                print('https://www.ai.rug.nl/~sheng/writeridataset.html')
                print('*' * 20)
                raise ValueError('Dataset: %s does not existed!' % dataset)

        self.labelfolder = self.folder
        self.train_folder = self.folder + '/train/'
        #self.train_folder = '/kaggle/input/cerug-en/CERUG-EN-train-images/train/'

        # Transform images in training folder
        transformer = ImageTransformer(foldername=self.train_folder)
        transformer.process_and_save_images()

        self.test_folder = self.folder + '/test/'
        #self.test_folder = '/kaggle/input/cerug-en/CERUG-EN-test-images/test/'

        self.imgtype = imgtype
        self.device = 'cuda'
        self.scale_size = (64, 128)

        if self.device == 'cuda':
            torch.backends.cudnn.benchmark = True

        if self.dataset == 'CVL':
            self.imgtype = 'tif'

        self.model_dir = 'model'
        if not os.path.exists(self.model_dir):
            os.mkdir(self.model_dir)

        basedir = 'CTE_WriterIdentification_dataset_' + self.dataset + '_model'
        self.logfile = basedir + '.log'
        self.modelfile = basedir
        self.batch_size = 16

        # Create training dataset and data loader
        train_set = DatasetFromFolder(dataset=self.dataset,
                                       labelfolder=self.labelfolder,
                                       foldername=self.train_folder,
                                       imgtype=self.imgtype,
                                       scale_size=self.scale_size,
                                       is_training=True)

        self.training_data_loader = DataLoader(dataset=train_set, num_workers=0,
                                               batch_size=self.batch_size, shuffle=True, drop_last=True)

        # Create testing dataset and data loader
        test_set = DatasetFromFolder(dataset=self.dataset,
                                      labelfolder=self.labelfolder,
                                      foldername=self.test_folder, imgtype=self.imgtype,
                                      scale_size=self.scale_size,
                                      is_training=False)

        self.testing_data_loader = DataLoader(dataset=test_set, num_workers=0,
                                              batch_size=self.batch_size, shuffle=False)

        num_class = train_set.num_writer
        self.model = GrnnNet(1, num_classes=train_set.num_writer).to(self.device)

        self.criterion = LabelSomCE()  # Define loss function
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.0001, weight_decay=1e-4)  # Optimizer
        self.scheduler = lr_scheduler.StepLR(self.optimizer, step_size=10, gamma=0.5)  # Learning rate scheduler

    def train(self, epoch):
        self.model.train()
        losstotal = []

        total_batches = len(self.training_data_loader)

        for iteration, batch in enumerate(self.training_data_loader, 1):
            inputs = batch[0].to(self.device).float()
            target = batch[1].type(torch.long).to(self.device)

            self.optimizer.zero_grad()  # Zero gradients

            logits = self.model(inputs)  # Forward pass

            train_loss = self.criterion(logits, target)  # Compute loss

            losstotal.append(train_loss.item())  # Store loss
            train_loss.backward()  # Backward pass
            self.optimizer.step()  # Update weights

        # Log training loss
        with open(self.logfile, 'a') as fp:
            fp.write('Training epoch %d avg loss is: %.6f\n' % (epoch, np.mean(losstotal)))
        print('Training epoch:', epoch, '  avg loss is:', np.mean(losstotal))
        return np.mean(losstotal)

    def test(self, epoch, during_train=True):
        # Test the model
        self.model.eval()
        losstotal = []

        if not during_train:
            self.load_model(epoch)

        top1 = 0
        top5 = 0
        ntotal = 0

        all_preds = []
        all_targets = []

        for iteration, batch in enumerate(self.testing_data_loader, 1):
            inputs = batch[0].to(self.device).float()
            target = batch[1].to(self.device).long()

            logits = self.model(inputs)  # Forward pass

            test_loss = self.criterion(logits, target)  # Compute loss

            losstotal.append(test_loss.item())  # Store loss

            res = self.accuracy(logits, target, topk=(1, 5))  # Compute accuracy
            top1 += res[0]
            top5 += res[1]

            ntotal += inputs.size(0)

            _, preds = logits.topk(1, 1, True, True)  # Get predictions
            all_preds.extend(preds.cpu().numpy().flatten())
            all_targets.extend(target.cpu().numpy().flatten())

        # Average accuracy
        top1 /= float(ntotal)
        top5 /= float(ntotal)

        precision, recall, f1 = self.compute_metrics(all_preds, all_targets)  # Compute metrics

        # Log testing results
        print('Testing epoch:', epoch, '  avg testing loss is:', np.mean(losstotal))
        print('Testing on epoch: %d has accuracy: top1: %.2f top5: %.2f' % (epoch, top1 * 100, top5 * 100))
        print('Precision: %.2f%%, Recall: %.2f%%, F1 Score: %.2f%%' % (precision * 100, recall * 100, f1 * 100))
        with open(self.logfile, 'a') as fp:
            fp.write('Testing epoch %d accuracy is: top1: %.2f top5: %.2f\n' % (epoch, top1 * 100, top5 * 100))

        return np.mean(losstotal)

    def check_exists(self, epoch):
        # Check if model checkpoint exists
        model_out_path = self.model_dir + '/' + self.modelfile + '-model_epoch_{}.pth'.format(epoch)
        return os.path.exists(model_out_path)

    def checkpoint(self, epoch):
        # Save model checkpoint
        model_out_path = self.model_dir + '/' + self.modelfile + '-model_epoch_{}.pth'.format(epoch)
        torch.save(self.model.state_dict(), model_out_path)

    def load_model(self, epoch):
        # Load model from checkpoint
        model_out_path = self.model_dir + '/' + self.modelfile + '-model_epoch_{}.pth'.format(epoch)
        self.model.load_state_dict(torch.load(model_out_path, map_location=self.device))
        print('Load model successful')

    def plot_losses(self, training_losses, testing_losses):
        # Plot training and testing losses
        indices = range(len(training_losses))
        plt.figure(figsize=(7.5, 4.5))
        plt.plot(indices, training_losses, 'b', label='Training loss')
        plt.plot(indices, testing_losses, 'r', label='Testing loss')
        #plt.title('Training and Testing Losses')
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.legend()

        plt.xlim(left=0)
        plt.ylim(bottom=0)

        last_epoch = indices[-1]
        last_test_loss = testing_losses[-1]
        plt.plot([last_epoch, last_epoch], [0, last_test_loss], 'k--')
        plt.text(last_epoch, last_test_loss, f'{last_test_loss:.1f}', color='k', va='bottom', ha='left')
        plt.savefig("/loss_plot.svg", format="svg", dpi=300)

        #plt.show()

    def train_loops(self, start_epoch, num_epoch):
        # Main training loop
        #if self.check_exists(num_epoch): return
        if start_epoch > 0:
            self.load_model(start_epoch - 1)

        training_losses = []
        testing_losses = []

        for epoch in range(start_epoch, num_epoch):
            train_loss = self.train(epoch)
            training_losses.append(train_loss)
            self.checkpoint(epoch)  # Save checkpoint
            test_loss = self.test(epoch)  # Test the model
            testing_losses.append(test_loss)
            self.scheduler.step()  # Update learning rate
            self.plot_losses(training_losses, testing_losses)  # Plot losses

    def accuracy(self, output, target, topk=(1,)):
        # Compute accuracy of predictions
        with torch.no_grad():
            maxk = max(topk)
            _, pred = output.topk(maxk, 1, True, True)
            pred = pred.t()
            correct = pred.eq(target.view(1, -1).expand_as(pred))

            res = []
            for k in topk:
                correct_k = correct[:k].reshape(-1).float().sum(0, keepdim=True)
                res.append(correct_k.data.cpu().numpy())

        return res

    def compute_metrics(self, preds, targets):
        # Compute precision, recall, and F1 score
        precision, recall, f1, _ = precision_recall_fscore_support(targets, preds, average='macro')
        return precision, recall, f1


if __name__ == '__main__':

    mod = DeepWriter_Train(dataset='CERUG-EN')
    mod.train_loops(0, 70)