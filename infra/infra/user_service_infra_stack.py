from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    CfnOutput,
)
from constructs import Construct

class UserServiceInfraStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        cluster: ecs.Cluster,
        repository,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "UserService",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            public_load_balancer=True,
            assign_public_ip=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(
                    repository=repository,
                    tag="latest"
                ),
                container_port=8000,
            ),
        )

        # Health check
        fargate_service.target_group.configure_health_check(
            protocol=elbv2.Protocol.HTTP,
            path="/",
            healthy_http_codes="200,404",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
        )

        # Ensure everything is deleted with the stack
        fargate_service.service.apply_removal_policy(RemovalPolicy.DESTROY)
        fargate_service.load_balancer.apply_removal_policy(RemovalPolicy.DESTROY)

        CfnOutput(
            self,
            "ServiceURL",
            value=fargate_service.load_balancer.load_balancer_dns_name
        )
