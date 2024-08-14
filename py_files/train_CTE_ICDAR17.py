# -*- coding: utf-8 -*-
"""notebookce522173bf

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/#fileId=https%3A//storage.googleapis.com/kaggle-colab-exported-notebooks/notebookce522173bf-1c2687f7-84a8-425e-b3f2-5a0f15f04da3.ipynb%3FX-Goog-Algorithm%3DGOOG4-RSA-SHA256%26X-Goog-Credential%3Dgcp-kaggle-com%2540kaggle-161607.iam.gserviceaccount.com/20240809/auto/storage/goog4_request%26X-Goog-Date%3D20240809T154825Z%26X-Goog-Expires%3D259200%26X-Goog-SignedHeaders%3Dhost%26X-Goog-Signature%3D3fceaed5a4f35bd83e4baaa1a9026e319f3a0bd58475cd97d2c230a33932a0725d10503f8bf0b3f3685a41af0519fb16351857f5f246e68e210cf31a533737e9e6b5e1839a725eb85afa868e52828804fa31e71086cf07b4fac22eb23409432c306a7c99f9d7a1983ad711b2740efaac4af9c98486be7ded51a71c49dc99360121cd59cedb1b3f1d890533310562134348d66d05acdd21c924d24ae15c39f4f87d8897f38384c82d75641ad062abc688c983ce90389803bc0373099b95850e194f909279f7a3d143418dbb065d7995d9f30280c26c4edc7a7499abb27f3d9f78562744c5d01139ce8ad388569a6be514f8df1fac90ba92021eead0f53944ba1b
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import matplotlib as plt
from torch.utils.data import DataLoader
from torch.optim import lr_scheduler
import matplotlib.pyplot as plt
import random
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter
from collections import defaultdict
import shutil
from sklearn.metrics import precision_recall_fscore_support

from cte import *
from dataloader_icdar17_words import *

import numpy as np
import os

class LabelSomCE(nn.Module):
	def __init__(self):
		super().__init__()

	def forward(self,x,target,smoothing=0.1):
		confidence = 1.0 - smoothing  # Calculate confidence for labels
		logprobs = F.log_softmax(x,dim=-1)  # Log probabilities
		nll_loss = - logprobs.gather(dim=-1,index=target.unsqueeze(1))  # Negative log likelihood loss
		nll_loss = nll_loss.squeeze(1)
		smooth_loss = -logprobs.mean(dim=-1)  # Mean loss for label smoothing
		loss = confidence * nll_loss + smoothing * smooth_loss  # Combined loss

		return loss.mean()  # Return average loss


class DeepWriter_Train:
    def __init__(self,dataset='CERUG-EN',imgtype='png'):
        self.dataset = dataset
        self.folder = dataset


        self.labelfolder = self.folder
        self.train_folder = self.folder + '/train/'  # Training data folder
        self.test_folder = self.folder + '/test/'  # Testing data folder

        self.imgtype = imgtype
        self.device = 'cuda'
        self.scale_size = (64, 128)  # Resize images

        if self.device == 'cuda':
            torch.backends.cudnn.benchmark = True  # Enable benchmark mode for performance

        if self.dataset == 'CVL':
            self.imgtype = 'tif'  # Change image type for CVL dataset

        self.model_dir = 'model'  # Directory to save models
        if not os.path.exists(self.model_dir):
            os.mkdir(self.model_dir)  # Create model directory if it doesn't exist

        basedir = 'CTE_WriterIdentification_dataset_ICDAR_model'
        self.logfile = basedir + '.log'  # Log file for training/testing loss
        self.modelfile = basedir
        self.batch_size = 16  # Batch size for training

        # Set up training data loader
        train_set = DatasetFromFolder(dataset=self.dataset,
        				labelfolder=self.labelfolder,
                        foldername=self.train_folder,
                        imgtype=self.imgtype,
                        scale_size=self.scale_size,
                        is_training=True)

        self.training_data_loader = DataLoader(dataset=train_set, num_workers=2,
                           batch_size=self.batch_size, shuffle=True, drop_last=True)

        # Set up testing data loader
        test_set = DatasetFromFolder(dataset=self.dataset,
        				labelfolder=self.labelfolder,
                        foldername=self.test_folder, imgtype=self.imgtype,
                        scale_size=self.scale_size,
                        is_training=False)

        self.testing_data_loader = DataLoader(dataset=test_set, num_workers=2,
                           batch_size=self.batch_size, shuffle=False)

        num_class = train_set.num_writer  # Get the number of classes
        self.model = GrnnNet(1, num_classes=train_set.num_writer).to(self.device)  # Initialize the model

        self.criterion = LabelSomCE()  # Loss function
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.0001, weight_decay=1e-4)  # Optimizer
        self.scheduler = lr_scheduler.StepLR(self.optimizer, step_size=10, gamma=0.5)  # Learning rate scheduler

    # Training
    def train(self, epoch):
        self.model.train()  # Set model to training mode
        losstotal = []

        for iteration, batch in enumerate(self.training_data_loader, 1):
            inputs = batch[0].to(self.device).float()  # Move input data to GPU
            target = batch[1].type(torch.long).to(self.device)  # Move target data to GPU

            self.optimizer.zero_grad()  # Zero gradients for optimizer

            logits = self.model(inputs)  # Forward pass

            train_loss = self.criterion(logits, target)  # Calculate loss

            losstotal.append(train_loss.item())  # Store loss
            train_loss.backward()  # Backward pass
            self.optimizer.step()  # Update parameters

        # Log average loss for the epoch
        with open(self.logfile, 'a') as fp:
            fp.write('Training epoch %d avg loss is: %.6f\n' % (epoch, np.mean(losstotal)))
        print('Training epoch:', epoch, '  avg loss is:', np.mean(losstotal))

        return np.mean(losstotal)  # Return average training loss

    # Testing
    def test(self, epoch, during_train=True):
        self.model.eval()
        losstotal = []

        if not during_train:
            self.load_model(epoch)  #

        top1 = 0
        top5 = 0
        ntotal = 0

        all_preds = []
        all_targets = []

        for iteration, batch in enumerate(self.testing_data_loader, 1):
            inputs = batch[0].to(self.device).float()
            target = batch[1].to(self.device).long()

            logits = self.model(inputs)  # Forward pass

            test_loss = self.criterion(logits, target)  # Calculate loss

            losstotal.append(test_loss.item())  # Store loss

            res = self.accuracy(logits, target, topk=(1, 5))  # Calculate accuracy
            top1 += res[0]
            top5 += res[1]

            ntotal += inputs.size(0)

            _, preds = logits.topk(1, 1, True, True)  # Get top predictions
            all_preds.extend(preds.cpu().numpy().flatten())  # Store predictions
            all_targets.extend(target.cpu().numpy().flatten())  # Store targets

        top1 /= float(ntotal)  # Calculate average top-1 accuracy
        top5 /= float(ntotal)  # Calculate average top-5 accuracy

        precision, recall, f1 = self.compute_metrics(all_preds, all_targets)  # Calculate metrics

        # Log results
        print('Testing epoch:', epoch, '  avg testing loss is:', np.mean(losstotal))
        print('Testing on epoch: %d has accuracy: top1: %.2f top5: %.2f' % (epoch, top1 * 100, top5 * 100))
        print('Precision: %.2f%%, Recall: %.2f%%, F1 Score: %.2f%%' % (precision * 100, recall * 100, f1 * 100))

        with open(self.logfile, 'a') as fp:
            fp.write('Testing epoch %d accuracy is: top1: %.2f top5: %.2f\n' % (epoch, top1 * 100, top5 * 100))

        return np.mean(losstotal)  # Return average testing loss

    def check_exists(self, epoch):
        model_out_path = self.model_dir + '/' + self.modelfile + '-model_epoch_{}.pth'.format(epoch)
        return os.path.exists(model_out_path)  # Check if model checkpoint exists

    def checkpoint(self, epoch):
        model_out_path = self.model_dir + '/' + self.modelfile + '-model_epoch_{}.pth'.format(epoch)
        torch.save(self.model.state_dict(), model_out_path)  # Save model checkpoint

    def load_model(self, epoch):
        model_out_path = self.model_dir + '/' + self.modelfile + '-model_epoch_{}.pth'.format(epoch)
        self.model.load_state_dict(torch.load(model_out_path, map_location=self.device))  # Load model
        print('Load model successful')

    def plot_losses(self, training_losses, testing_losses):
        indices = range(len(training_losses))
        plt.figure(figsize=(7.5, 4.5))
        plt.plot(indices, training_losses, 'b', label='Training loss')  # Plot training loss
        plt.plot(indices, testing_losses, 'r', label='Testing loss')  # Plot testing loss
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.legend()

        plt.xlim(left=0)
        plt.ylim(bottom=0)

        last_epoch = indices[-1]
        last_test_loss = testing_losses[-1]
        plt.plot([last_epoch, last_epoch], [0, last_test_loss], 'k--')  # Mark last test loss
        plt.text(last_epoch, last_test_loss, f'{last_test_loss:.1f}', color='k', va='bottom', ha='left')
        plt.savefig("/loss_plot.svg", format="svg", dpi=300)  # Save plot as SVG
        #plt.show()

    def train_loops(self, start_epoch, num_epoch):
        #if self.check_exists(num_epoch): return  # Skip if model exists
        if start_epoch > 0:
            self.load_model(start_epoch - 1)  # Load model if continuing training

        training_losses = []
        testing_losses = []

        for epoch in range(start_epoch, num_epoch):
            train_loss = self.train(epoch)  # Train for one epoch
            training_losses.append(train_loss)
            self.checkpoint(epoch)  # Save model checkpoint
            test_loss = self.test(epoch)  # Test after training
            testing_losses.append(test_loss)
            self.scheduler.step()  # Update learning rate
            self.plot_losses(training_losses, testing_losses)  # Plot losses

    def accuracy(self, output, target, topk=(1,)):
        with torch.no_grad():
            maxk = max(topk)
            _, pred = output.topk(maxk, 1, True, True)  # Get top-k predictions
            pred = pred.t()  # Transpose predictions
            correct = pred.eq(target.view(1, -1).expand_as(pred))  # Check correct predictions

            res = []
            for k in topk:
                correct_k = correct[:k].reshape(-1).float().sum(0, keepdim=True)  # Calculate correct count for top-k
                res.append(correct_k.data.cpu().numpy())  # Store results

        return res

    def compute_metrics(self, preds, targets):
        precision, recall, f1, _ = precision_recall_fscore_support(targets, preds, average='weighted')  # Compute metrics
        return precision, recall, f1

if __name__ == '__main__':
    mod = DeepWriter_Train(dataset='/kaggle/input/icdar17-widewords/ICDAR17_lsegs')
    mod.train_loops(0, 35)