from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    CfnOutput,
)
from constructs import Construct


class UserServiceBasicInfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        self.vpc = ec2.Vpc(
            self,
            "UserServicedVpc",
            max_azs=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="PublicSubnets"
                )
            ]
       )
        self.vpc.apply_removal_policy(RemovalPolicy.DESTROY)

        # ECS Cluster
        self.cluster = ecs.Cluster(
            self,
            "UserServiceCluster",
            vpc=self.vpc
        )
        self.cluster.apply_removal_policy(RemovalPolicy.DESTROY)

        # ECR Repository
        self.repository = ecr.Repository(
            self,
            "UserServiceRepo",
            repository_name="user-service-mcp",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Outputs (useful but not required for wiring)
        CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
        CfnOutput(self, "ClusterName", value=self.cluster.cluster_name)
        CfnOutput(self, "EcrRepoUri", value=self.repository.repository_uri)
