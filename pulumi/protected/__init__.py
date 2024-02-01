"""Protected Scoped Infrastructure"""

from pulumi_aws_native import iam, get_region

region = get_region()
path = "capebs-protected"

protected_user = iam.User(
    "protected_user",
    path=path,
    login_profile=iam.UserLoginProfileArgs(
        password="b4dp4ssw0rd", password_reset_required=True
    ),
    usename=f"{region}_protected",
)
