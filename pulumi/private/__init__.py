"""Private Scoped Infrastructure"""

from pulumi import Output
from pulumi_aws_native import iam, get_region
import datalakehouse

region = get_region()
path = "capbs-private"

raw_bucket_group = iam.Group(
    "raw_bucket_group",
    group_name=f"{region}_capbs_raw_bucket_group",
    path=path,
    policies=[
        iam.GroupPolicyArgs(
            "capebs_raw_bucket_group_policy",
            policy_document=Output.json_dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:ListObjects",
                            ],
                            "Resource": datalakehouse.raw_bucket.arn,
                        },
                        {
                            "Effect": "Deny",
                            "Action": ["s3:*"],
                            "Resource": datalakehouse.raw_bucket.arn,
                        },
                    ],
                }
            ),
        )
    ],
)

curated_bucket_group = iam.Group(
    "curated_bucket_group",
    group_name=f"{region}_capbs_curated_bucket_group",
    path=path,
    policies=[
        iam.GroupPolicyArgs(
            "capebs_curated_bucket_group_policy",
            policy_document=Output.json_dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObject",
                                "s3:ListObjects",
                            ],
                            "Resource": datalakehouse.curated_bucket.arn,
                        },
                        {
                            "Effect": "Deny",
                            "Action": ["s3:*"],
                            "Resource": datalakehouse.curated_bucket.arn,
                        },
                    ],
                }
            ),
        )
    ],
)

private_admin = iam.User(
    "private_admin",
    path=path,
    groups=[raw_bucket_group.arn, curated_bucket_group.arn],
    login_profile=iam.UserLoginProfileArgs(
        password="b4dp4ssw0rd", password_reset_required=True
    ),
    usename=f"{region}_admin",
)

private_user = iam.User(
    "private_user",
    path=path,
    groups=[curated_bucket_group.arn],
    login_profile=iam.UserLoginProfileArgs(
        password="b4dp4ssw0rd", password_reset_required=True
    ),
    usename=f"{region}_private",
)
