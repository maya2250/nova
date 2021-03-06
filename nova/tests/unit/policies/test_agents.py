#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from nova.api.openstack.compute import agents
from nova.db.sqlalchemy import models
from nova.tests.unit.api.openstack import fakes
from nova.tests.unit.policies import base


class AgentsPolicyTest(base.BasePolicyTest):
    """Test os-agents APIs policies with all possible context.
    This class defines the set of context with different roles
    which are allowed and not allowed to pass the policy checks.
    With those set of context, it will call the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super(AgentsPolicyTest, self).setUp()
        self.controller = agents.AgentController()
        self.req = fakes.HTTPRequest.blank('')
        # Check that admin is able to perform the CRUD operation
        # on agents.
        self.admin_authorized_contexts = [
            self.legacy_admin_context, self.system_admin_context,
            self.project_admin_context]
        # Check that non-admin is not able to perform the CRUD operation
        # on agents.
        self.admin_unauthorized_contexts = [
            self.system_member_context, self.system_reader_context,
            self.system_foo_context, self.project_member_context,
            self.other_project_member_context,
            self.project_foo_context, self.project_reader_context
        ]

    @mock.patch('nova.db.api.agent_build_destroy')
    def test_delete_agent_policy(self, mock_delete):
        rule_name = "os_compute_api:os-agents"
        self.common_policy_check(self.admin_authorized_contexts,
                                 self.admin_unauthorized_contexts,
                                 rule_name, self.controller.delete,
                                 self.req, 1)

    @mock.patch('nova.db.api.agent_build_get_all')
    def test_index_agents_policy(self, mock_get):
        rule_name = "os_compute_api:os-agents"
        self.common_policy_check(self.admin_authorized_contexts,
                                 self.admin_unauthorized_contexts,
                                 rule_name, self.controller.index,
                                 self.req)

    @mock.patch('nova.db.api.agent_build_update')
    def test_update_agent_policy(self, mock_update):
        rule_name = "os_compute_api:os-agents"
        body = {'para': {'version': '7.0',
                'url': 'http://example.com/path/to/resource',
                'md5hash': 'add6bb58e139be103324d04d82d8f545'}}

        self.common_policy_check(self.admin_authorized_contexts,
                                 self.admin_unauthorized_contexts,
                                 rule_name, self.controller.update,
                                 self.req, 1, body=body)

    def test_create_agent_policy(self):
        rule_name = "os_compute_api:os-agents"
        body = {'agent': {'hypervisor': 'kvm',
                          'os': 'win',
                          'architecture': 'x86',
                          'version': '7.0',
                          'url': 'http://example.com/path/to/resource',
                          'md5hash': 'add6bb58e139be103324d04d82d8f545'}}

        def fake_agent_build_create(context, values):
            values['id'] = 1
            agent_build_ref = models.AgentBuild()
            agent_build_ref.update(values)
            return agent_build_ref

        self.stub_out("nova.db.api.agent_build_create",
                      fake_agent_build_create)

        self.common_policy_check(self.admin_authorized_contexts,
                                 self.admin_unauthorized_contexts,
                                 rule_name, self.controller.create,
                                 self.req, body=body)


class AgentsScopeTypePolicyTest(AgentsPolicyTest):
    """Test os-agents APIs policies with system scope enabled.
    This class set the nova.conf [oslo_policy] enforce_scope to True
    so that we can switch on the scope checking on oslo policy side.
    It defines the set of context with scoped token
    which are allowed and not allowed to pass the policy checks.
    With those set of context, it will run the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super(AgentsScopeTypePolicyTest, self).setUp()
        self.flags(enforce_scope=True, group="oslo_policy")

        # Check that system admin is able to perform the CRUD operation
        # on agents.
        self.admin_authorized_contexts = [
            self.system_admin_context]
        # Check that non-system or non-admin is not able to perform the CRUD
        # operation on agents.
        self.admin_unauthorized_contexts = [
            self.legacy_admin_context, self.system_member_context,
            self.system_reader_context, self.project_admin_context,
            self.system_foo_context, self.project_member_context,
            self.other_project_member_context,
            self.project_foo_context, self.project_reader_context
        ]
