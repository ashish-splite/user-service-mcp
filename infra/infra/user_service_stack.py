from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    CfnOutput
)
from constructs import Construct


class UserServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. VPC
        vpc = ec2.Vpc(
            self,
            "DevVpc",
            max_azs=2
        )
        vpc.apply_removal_policy(RemovalPolicy.DESTROY)

        # 2. ECR Repository
        repository = ecr.Repository(
            self,
            "UserServiceRepo",
            repository_name="user-service-mcp",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        # 3. ECS Cluster
        cluster = ecs.Cluster(
            self,
            "DevCluster",
            vpc=vpc
        )
        cluster.apply_removal_policy(RemovalPolicy.DESTROY)

        # 4. ECS Fargate Service + ALB
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "UserMcpService",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(
                    repository=repository,
                    tag="latest"
                ),
                container_port=8000,
                environment={
                    "DATABASE_URL": "REPLACE_WITH_YOUR_RDS_URL",
                    "PORT": "8000"
                }
            )
        )

        # Health check
        fargate_service.target_group.configure_health_check(
            protocol=elbv2.Protocol.HTTP,
            path="/",
            healthy_http_codes="200,404",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3
        )

        # Outputs
        CfnOutput(
            self,
            "ServiceURL",
            value=fargate_service.load_balancer.load_balancer_dns_name
        )

        CfnOutput(
            self,
            "ECRRepoURI",
            value=repository.repository_uri
        )