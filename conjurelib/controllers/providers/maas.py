# Copyright (c) 2015 Canonical Ltd.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from conjurelib.ui.views import MaasProviderView
from conjurelib.models.providers import MaasProviderModel


class MaasProviderController:
    def __init__(self, common):
        self.common = common
        self.view = MaasProviderView(self.common,
                                     self.finish)
        self.model = MaasProviderModel

    def finish(self, result):
        """ Deploys to the maas provider
        """
        self.model.config['maas-server'] = result['maas_server'].value
        self.model.config['maas-oauth'] = result['maas_apikey'].value
        print("Deploying with: {}".format(self.model.to_yaml()))

    def render(self):
        self.common['ui'].set_header(
            title="MAAS Provider",
            excerpt="Enter your MAAS credentials to "
            "enable deploying to this provider."
        )
        self.common['ui'].set_body(self.view)
