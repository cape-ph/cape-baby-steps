"""Protected Scoped Infrastructure"""

import pulumi_aws_native as aws

region = aws.get_region()
path = "capebs-protected"

protected_user = aws.iam.User(
    "protected_user",
    path=path,
    login_profile=aws.iam.UserLoginProfileArgs(
        password="b4dp4ssw0rd", password_reset_required=True
    ),
    user_name=f"{region}_protected",
)
