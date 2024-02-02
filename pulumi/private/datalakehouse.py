"""An AWS Python Pulumi program"""

from pulumi import Output, AssetArchive, FileArchive
from pulumi_aws_native import s3, lambda_, iam, get_account_id

account_id = get_account_id()

bs_lambda_form_role = iam.Role(
    "bs_lambda_form_role",
    assume_role_policy_document=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": ["lambda.amazonaws.com"]},
                    "Action": ["sts:AssumeRole"],
                }
            ],
        }
    ),
)

bs_lambda_form_function = lambda_.Function(
    "bs_lambda_form_function",
    code=AssetArchive({".": FileArchive("./bs_form_function")}),
    handler="lambda_function.csv_xform_handler",
    role=bs_lambda_form_role.arn,
    runtime="python3.9",
    timeout=120,
)


# Create an AWS resource (S3 Bucket)
raw_bucket = s3.Bucket(
    "capebs-private-dlh-raw-bucket",
    versioning_configuration=s3.BucketVersioningConfigurationArgs(
        status=s3.BucketVersioningConfigurationStatus.ENABLED
    ),
    notification_configuration=s3.BucketNotificationConfigurationArgs(
        lambda_configurations=[
            s3.BucketLambdaConfigurationArgs(
                event="s3:ObjectCreated:*",
                function=bs_lambda_form_function.arn,
                filter=s3.BucketNotificationFilterArgs(
                    s3_key=s3.BucketS3KeyFilterArgs(
                        rules=[
                            s3.BucketFilterRuleArgs(name="suffix", value=".csv"),
                        ]
                    )
                ),
            ),
        ]
    ),
)

raw_bucket_policy = iam.RolePolicy(
    "capebs-xform-lambda-raw-bucket-policy",
    role_name=bs_lambda_form_role.arn,
    policy_document=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject"],
                    "Resource": f"{raw_bucket.arn}/*",
                }
            ],
        }
    ),
)

bs_lambda_form_permission = lambda_.Permission(
    "bs_lambda_form_permission",
    action="lambda:InvokeFunction",
    FunctionName=bs_lambda_form_function.arn,
    principal="s3.amazonaws.com",
    source_arn=raw_bucket.arn,
    source_account=account_id,
)

curated_bucket = s3.Bucket(
    "capebs-private-dlh-curated-bucket",
    versioning_configuration=s3.BucketVersioningConfigurationArgs(
        status=s3.BucketVersioningConfigurationStatus.ENABLED
    ),
)

curated_bucket_policy = iam.RolePolicy(
    "capebs-xform-lambda-curated-bucket-policy",
    role_name=bs_lambda_form_role.arn,
    policy_document=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:PutObject"],
                    "Resource": f"{curated_bucket.arn}/*",
                }
            ],
        }
    ),
)
