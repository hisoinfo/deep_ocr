import caffe
import json
import numpy as np
import os
import cv2
import shutil
import copy

class CaffeCls(object):
    def __init__(self, 
                 model_def,
                 model_weights,
                 y_tag_json_path,
                 is_mode_cpu=True,
                 width=64,
                 height=64):
        self.net = caffe.Net(model_def,
            model_weights,
            caffe.TEST)
        if is_mode_cpu:
            caffe.set_mode_cpu()
        self.y_tag_json = json.load(open(y_tag_json_path, "r"))
        self.width = width
        self.height = height

    def _predict_cv2_imgs_sub(self, cv2_imgs, pos_start, pos_end):
        cv2_imgs_sub = cv2_imgs[pos_start: pos_end]
        if cv2_imgs_sub[0][0] > 1.0:
            raise ValueError("image should be normalized between 0 and 1.0")

        self.net.blobs['data'].reshape(cv2_imgs_sub.shape[0], 1,
                                       self.width, self.height)
        self.net.blobs['data'].data[...] = cv2_imgs_sub.reshape(
            (cv2_imgs_sub.shape[0], 1, self.width, self.height))
        output = self.net.forward()

        output_tag_to_max_proba = []

        num_sample = cv2_imgs_sub.shape[0]
        for i in range(num_sample):
            output_prob = output['prob'][i]
            output_prob_index = sorted(
                range(len(output_prob)),
                key=lambda x:output_prob[x],
                reverse=True)            
            output_tag_to_probas = []
            for index in output_prob_index:
                item = (self.y_tag_json[str(index)],
                        output_prob[index])
                output_tag_to_probas.append(item)
            # output_tag_to_probas = output_tag_to_probas[:2]
            output_tag_to_max_proba.append(output_tag_to_probas)
        return output_tag_to_max_proba

    def predict_cv2_imgs(self, cv2_imgs, step=50):
        output_tag_to_max_proba = []
        num_sample = cv2_imgs.shape[0]
        for i in range(0, num_sample, step):
            pos_end = min(num_sample, (i + step))
            output_tag_to_max_proba += \
                self._predict_cv2_imgs_sub(cv2_imgs, i, pos_end)
        return output_tag_to_max_proba

    def predict_cv2_img(self, cv2_img):
        shape = cv2_img.shape
        cv2_imgs = cv2_img.reshape((1, shape[0], shape[1]))
        return self.predict_cv2_imgs(cv2_imgs)[0]

if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    data_dir_path = os.path.join(dir_path, "..", "data")
    image_list = []
    for image_path in os.listdir(data_dir_path):
        if image_path.startswith("mnist"):
            image = cv2.imread(image_path)
            image = cv2.resize(image, (32, 32))
            image_list.append(image)
    images = np.asarray(image_list)
    images = images / 255.0

    path_y_tag = os.path.join(data_dir_path, "mnist_y_tag.json")
    path_model_def = "/opt/caffe/examples/mnist/lenet.prototxt"
    model_weights = "/opt/caffe/examples/mnist/lenet_iter_10000.caffemodel"

    cls = CaffeCls(path_model_def, model_weights, path_y_tag)
    ret = cls.predict_cv2_imgs(images)

    print("ret=", ret)
