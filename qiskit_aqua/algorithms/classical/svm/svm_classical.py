# -*- coding: utf-8 -*-

# Copyright 2018 IBM.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

import copy
import logging

from qiskit_aqua import QuantumAlgorithm, get_multiclass_extension_instance
from qiskit_aqua.algorithms.classical.svm import SVM_Classical_Binary, SVM_Classical_Multiclass
from qiskit_aqua.utils import get_num_classes

logger = logging.getLogger(__name__)


class SVM_Classical(QuantumAlgorithm):
    """
    The classical svm interface.
    Internally, it will run the binary classification or multiclass classification
    based on how many classes the data have.
    """

    SVM_Classical_CONFIGURATION = {
        'name': 'SVM',
        'description': 'SVM_Classical Algorithm',
        'classical': True,
        'input_schema': {
            '$schema': 'http://json-schema.org/schema#',
            'id': 'SVM_Classical_schema',
            'type': 'object',
            'properties': {
                'gamma': {
                    'type': ['number', 'null'],
                    'default': None
                }
            },
            'additionalProperties': False
        },
        'depends': ['multiclass_extension'],
        'problems': ['svm_classification'],
        'defaults': {
            'multiclass_extension': {
                'name': 'AllPairs',
                'estimator': 'RBF_SVC_Estimator',
            }
        }
    }

    def __init__(self, configuration=None):
        super().__init__(configuration or copy.deepcopy(SVM_Classical.SVM_Classical_CONFIGURATION))
        self._ret = {}
        self.instance = None

    def init_params(self, params, algo_input):
        svm_params = params.get(QuantumAlgorithm.SECTION_KEY_ALGORITHM)

        is_multiclass = get_num_classes(algo_input.training_dataset) > 2
        if is_multiclass:
            multiclass_extension_params = params.get(QuantumAlgorithm.SECTION_KEY_MULTICLASS_EXTENSION)
            multiclass_extension = get_multiclass_extension_instance(multiclass_extension_params['name'])
            multiclass_extension.init_params(multiclass_extension_params)
            # checking the options:
            estimator = multiclass_extension_params.get('estimator', None)
            if estimator is None:
                logger.debug("You did not provide the estimator, which is however required!")
            if estimator not in ["RBF_SVC_Estimator"]:
                logger.debug("You should use one of the classical estimators")
            logger.info("Multiclass classifcation algo:" + multiclass_extension_params['name'])
        else:
            logger.warning("We will apply the binary classifcation and"
                           "ignore all options related to the multiclass")
            multiclass_extension = None

        self.init_args(algo_input.training_dataset, algo_input.test_dataset,
                       algo_input.datapoints, svm_params.get('gamma'), multiclass_extension)

    def init_args(self, training_dataset, test_dataset, datapoints, gamma,
                  multiclass_extension=None):

        if multiclass_extension is None:
            svm_instance = SVM_Classical_Binary()
        else:
            svm_instance = SVM_Classical_Multiclass(multiclass_extension)

        svm_instance.init_args(training_dataset, test_dataset, datapoints, gamma)
        self.instance = svm_instance

    def train(self, data, labels):
        """
        train the svm
        Args:
            data (numpy.ndarray): NxD array, where N is the number of data,
                                  D is the feature dimension.
            labels (numpy.ndarray): Nx1 array, where N is the number of data
        """
        self.instance.train(data, labels)

    def test(self, data, labels):
        """
        test the svm
        Args:
            data (numpy.ndarray): NxD array, where N is the number of data,
                                  D is the feature dimension.
            labels (numpy.ndarray): Nx1 array, where N is the number of data

        Returns:
            float: accuracy
        """
        return self.instance.test(data, labels)

    def predict(self, data):
        """
        predict using the svm
        Args:
            data (numpy.ndarray): NxD array, where N is the number of data,
                                  D is the feature dimension.
        Returns:
            numpy.ndarray: predicted labels, Nx1 array
        """
        return self.instance.predict(data)

    def run(self):
        return self.instance.run()

    @property
    def label_to_class(self):
        return self.instance.label_to_class

    @property
    def class_to_label(self):
        return self.instance.class_to_label