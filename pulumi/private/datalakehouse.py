"""An AWS Python Pulumi program"""

from pulumi import Output
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
    code=lambda_.FunctionCodeArgs(
        zip_file="""
          import csv
          import io
          import urllib.parse
          import re
          import boto3

          def csv_xform_lambda_handler(event, context):
              \"\"\"Trivial Lambda function that transforms a csv column header if needed.

              NOTE: we are not handling bad stuff now. like
              - if the file isn't actually a csv
              - if it has no header row
              - if the csv has multiple columns with the same header (this is actually
                handled the way this is implemented)
              - errors getting the raw file or writing the transformed file (which should
                cause a re-run of the lambda)
              - file being transformed more than once (upload of same file more than once)
              - etc

              :param event: The event that triggered this function
              :param context: Context for the function. Probably will not use.
              \"\"\"
              # this will end up with the contents for the xformed csv
              xformed_csv_data = []

              # the bucket in which we will place the xformed file
              curated_bucket = "capebs-private-dlh-curated-bucket"

              # name of the bucket where the upload happened to trigger this lambda.
              # NOTE: we *could* error check this if we want as this should be the value
              #       "capebs-private-dlh-raw-bucket" in this trivial example. but if AWS
              # is doing the right thing, that's the only value we should get
              raw_bucket = event['Records'][0]['s3']['bucket']['name']

              # get the name of the file that was uploaded to cause this function to run
              key = urllib.parse.unquote_plus(
                  event['Records'][0]['s3']['object']['key'],
                  encoding='utf-8'
              )

              try:
                  response = s3.get_object(Bucket=raw_bucket, Key=key)

                  with open("test.csv") as csvfile:
                      csvrdr = csv.reader(csvfile)

                      # get the current cav headers
                      headers = next(csvrdr)

                      # replace "Date of Birth" (ignore case) with "DOB". if the value is
                      # not found, then the file will go into curated as is. save this
                      # xform as the 1st row (headers) in xformed_csv_data
                      xformed_csv_data.append(
                          list(
                              map(lambda x: re.sub("(?i)date of birth", "DOB", x),
                              headers)
                          )
                      )

                      # now get the data rows into xformed_csv_data
                      for row in csvrdr:
                          xformed_csv_data.append(row)

                  # write the xformed contents to a StringIO object (S3 wants this) and
                  # put that in the curated bucket
                  with io.StringIO() as xformed_obj_file:
                      csvwriter = csv.writer(xformed_obj_file)
                      for row in xformed_csv_data:
                          csvwriter.writerow(item)

                      s3.put_object(
                          Body=xformed_obj_file.get_value(),
                          Bucket=curated_bucket,
                          Key=f"transformed-{key}"
                      )

              except Exception as e:
                  # NOTE: this is a bad handler. if we're setup for retries and there's
                  #       a simple bug in here, this could be retried a bunch. really,
                  #       this block just needs to catch things that systematic problems
                  #       like a failure to get/put files in S3 (e.g. due to connection
                  #       errors) and things that are non-systematic exceptions
                  print(e)
                  print(
                      f"Something went wrong during get, transform, or put of CSV file."
                  )
                  raise e
        """
    ),
    handler="csv_xform_lambda_hanlder",
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
            )
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
