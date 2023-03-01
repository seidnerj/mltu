import os
import cv2
import numpy as np
from tqdm import tqdm
import requests, gzip, os, hashlib

import torch
import torch.nn.functional as F
import torch.optim as optim

from model import Net

from mltu.torch.dataProvider import DataProvider
from mltu.torch.model import Model
from mltu.torch.metrics import Accuracy

path='Datasets/data'
def fetch(url):
    if os.path.exists(path) is False:
        os.makedirs(path)

    fp = os.path.join(path, hashlib.md5(url.encode('utf-8')).hexdigest())
    if os.path.isfile(fp):
        with open(fp, "rb") as f:
            data = f.read()
    else:
        with open(fp, "wb") as f:
            data = requests.get(url).content
            f.write(data)
    return np.frombuffer(gzip.decompress(data), dtype=np.uint8).copy()

# load mnist dataset from yann.lecun.com, train data is of shape (60000, 28, 28) and targets are of shape (60000)
train_data = fetch("http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz")[0x10:].reshape((-1, 28, 28))
train_targets = fetch("http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz")[8:]
test_data = fetch("http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz")[0x10:].reshape((-1, 28, 28))
test_targets = fetch("http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz")[8:]

train_dataset = [[data, target] for data, target in zip(train_data, train_targets)]
test_dataset = [[data, target] for data, target in zip(test_data, test_targets)]

def preprocessor(data, target):
    # original data is shape of (28, 28), expand to (1, 28, 28) and normalize to [0, 1]
    data = np.expand_dims(data, axis=0) / 255.0
    return data, target

train_dataProvider = DataProvider(
    train_dataset, 
    data_preprocessors=[preprocessor],
    batch_size=64
    )

test_dataProvider = DataProvider(
    test_dataset,
    data_preprocessors=[preprocessor],
    batch_size=64
    )

# create network, optimizer and define loss function
network = Net()
optimizer = optim.Adam(network.parameters(), lr=0.001)
loss = F.nll_loss

# create model object that will handle training and testing of the network
model = Model(network, optimizer, loss, metrics=[Accuracy()])
model.fit(train_dataProvider, test_dataProvider, epochs=5)

# define output path and create folder if not exists
output_path = 'Models/06_pytorch_introduction'
if not os.path.exists(output_path):
    os.makedirs(output_path)

# save model.pt to defined output path
torch.save(model.model.state_dict(), os.path.join(output_path, "model.pt"))