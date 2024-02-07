"""An AWS Python Pulumi program"""

import os
from pulumi import Output
import pulumi_aws_native as aws

account_id = aws.get_account_id().account_id

bs_lambda_form_role = aws.iam.Role(
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

lambda_function = os.path.join(
    os.path.dirname(__file__), "bs_form_function", "lambda_function.py"
)
with open(lambda_function) as f:
    bs_lambda_form_function = aws.lambda_.Function(
        "bs_lambda_form_function",
        code=aws.lambda_.FunctionCodeArgs(zip_file=f.read()),
        handler="csv_xform_handler",
        role=bs_lambda_form_role.arn,
        runtime="python3.9",
        timeout=120,
    )


# Create an AWS resource (S3 Bucket)
raw_bucket = aws.s3.Bucket(
    "capebs-private-dlh-raw-bucket",
    versioning_configuration=aws.s3.BucketVersioningConfigurationArgs(
        status=aws.s3.BucketVersioningConfigurationStatus.ENABLED
    ),
    notification_configuration=aws.s3.BucketNotificationConfigurationArgs(
        lambda_configurations=[
            aws.s3.BucketLambdaConfigurationArgs(
                event="s3:ObjectCreated:*",
                function=bs_lambda_form_function.arn,
                filter=aws.s3.BucketNotificationFilterArgs(
                    s3_key=aws.s3.BucketS3KeyFilterArgs(
                        rules=[
                            aws.s3.BucketFilterRuleArgs(name="suffix", value=".csv"),
                        ]
                    )
                ),
            ),
        ]
    ),
)

raw_bucket_policy = aws.iam.RolePolicy(
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

bs_lambda_form_permission = aws.lambda_.Permission(
    "bs_lambda_form_permission",
    action="lambda:InvokeFunction",
    function_name=bs_lambda_form_function.arn,
    principal="s3.amazonaws.com",
    source_arn=raw_bucket.arn,
    source_account=account_id,
)

curated_bucket = aws.s3.Bucket(
    "capebs-private-dlh-curated-bucket",
    versioning_configuration=aws.s3.BucketVersioningConfigurationArgs(
        status=aws.s3.BucketVersioningConfigurationStatus.ENABLED
    ),
)

curated_bucket_policy = aws.iam.RolePolicy(
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
