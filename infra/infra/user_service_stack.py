from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ecs_patterns as ecs_patterns,
    CfnOutput
)
from constructs import Construct

class UserServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create a VPC (Networking)
        vpc = ec2.Vpc(self, "DevVpc", max_azs=2)

        # 2. Create an ECR Repository (Docker Image Storage)
        repository = ecr.Repository(self, "UserServiceRepo",
            repository_name="user-service-mcp",
            image_scan_on_push=True
        )

        # 3. Create an ECS Cluster
        cluster = ecs.Cluster(self, "DevCluster", vpc=vpc)

        # 4. Define the Fargate Task & Service with a Load Balancer
        # This high-level pattern creates the Task Definition, Service, and ALB.
        # Image is pulled from ECR (built and pushed by buildspec.yml)
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "UserMcpService",
            cluster=cluster,            # Required
            cpu=256,                    # Default is 256
            memory_limit_mib=512,       # Default is 512
            desired_count=1,            # Number of running tasks
            public_load_balancer=True,  # Accessible from the internet
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                # Reference existing image from ECR (not building from Dockerfile)
                image=ecs.ContainerImage.from_ecr_repository(
                    repository=repository,
                    tag="latest"  # Always use latest tag for running service
                ),
                container_port=8000,
                environment={
                    "DATABASE_URL": "REPLACE_WITH_YOUR_RDS_URL",
                    "PORT": "8000"
                }
            )
        )

        # Health check configuration
        # Use TCP health check for SSE server (more reliable than HTTP for streaming endpoints)
        # Simply checks if port 8000 is accepting connections
        fargate_service.target_group.configure_health_check(
            protocol=ecs.Protocol.TCP,
            interval=30,
            timeout=5,
            healthy_threshold_count=2,
            unhealthy_threshold_count=3
        )

        # Outputs
        CfnOutput(self, "ServiceURL", value=fargate_service.load_balancer.load_balancer_dns_name)
        CfnOutput(self, "ECRRepoURI", value=repository.repository_uri)