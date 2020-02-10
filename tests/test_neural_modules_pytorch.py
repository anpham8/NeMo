# ! /usr/bin/python
# -*- coding: utf-8 -*-

# =============================================================================
# Copyright 2020 NVIDIA. All Rights Reserved.
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

import unittest

import nemo
from nemo.backends.pytorch.nm import TrainableNM
from tests.common_setup import NeMoUnitTest


class TestNM1(TrainableNM):
    def __init__(self, var1=1, var2=2, var3=3):
        super(TestNM1, self).__init__()


class TestNM2(TestNM1):
    def __init__(self, var2):
        super(TestNM2, self).__init__(var2=var2)


class TestNeuralModulesPT(NeMoUnitTest):
    def setUp(self) -> None:
        super().setUp()

        # Mockup abstract methods.
        TestNM1.__abstractmethods__ = set()
        TestNM2.__abstractmethods__ = set()

    def test_default_init_params(self):
        simple_nm = TestNM1(var1=1)
        init_params = simple_nm.init_params
        self.assertEqual(init_params["var1"], 1)
        self.assertEqual(init_params["var2"], 2)
        self.assertEqual(init_params["var3"], 3)

    def test_simple_init_params(self):
        simple_nm = TestNM1(var1=10, var3=30)
        init_params = simple_nm.init_params
        self.assertEqual(init_params["var1"], 10)
        self.assertEqual(init_params["var2"], 2)
        self.assertEqual(init_params["var3"], 30)

    def test_nested_init_params(self):
        simple_nm = TestNM2(var2="hello")
        init_params = simple_nm.init_params
        self.assertEqual(init_params["var2"], "hello")

    def test_constructor_TaylorNet(self):
        tn = nemo.backends.pytorch.tutorials.TaylorNet(dim=4)
        self.assertEqual(tn.init_params["dim"], 4)

    def test_call_TaylorNet(self):
        x_tg = nemo.core.neural_modules.NmTensor(
            producer=None,
            producer_args=None,
            name=None,
            ntype=nemo.core.neural_types.NeuralType(
                {
                    0: nemo.core.neural_types.AxisType(nemo.core.neural_types.BatchTag),
                    1: nemo.core.neural_types.AxisType(nemo.core.neural_types.ChannelTag),
                }
            ),
        )

        tn = nemo.backends.pytorch.tutorials.TaylorNet(dim=4)
        # note that real port's name: x was used
        y_pred = tn(x=x_tg)
        self.assertEqual(y_pred.producer, tn)
        self.assertEqual(y_pred.producer_args.get("x"), x_tg)

    def test_simple_chain(self):
        data_source = nemo.backends.pytorch.tutorials.RealFunctionDataLayer(n=10000, batch_size=1)
        trainable_module = nemo.backends.pytorch.tutorials.TaylorNet(dim=4)
        loss = nemo.backends.pytorch.tutorials.MSELoss()
        x, y = data_source()
        y_pred = trainable_module(x=x)
        loss_tensor = loss(predictions=y_pred, target=y)

        # check producers' bookkeeping
        self.assertEqual(loss_tensor.producer, loss)
        self.assertEqual(loss_tensor.producer_args, {"predictions": y_pred, "target": y})
        self.assertEqual(y_pred.producer, trainable_module)
        self.assertEqual(y_pred.producer_args, {"x": x})
        self.assertEqual(y.producer, data_source)
        self.assertEqual(y.producer_args, {})
        self.assertEqual(x.producer, data_source)
        self.assertEqual(x.producer_args, {})
