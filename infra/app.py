#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.user_service_basic_infra_stack import  UserServiceBasicInfraStack
from infra.user_service_infra_stack import UserServiceInfraStack


app = cdk.App()
infra_stack = UserServiceBasicInfraStack(
    app,
    "UserServiceBasicInfraStack"
)

UserServiceInfraStack(
    app,
    "UserServiceInfraStack",
    cluster=infra_stack.cluster,
    repository=infra_stack.repository,
)

app.synth()
