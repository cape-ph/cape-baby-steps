"""CAPE Infrastructure"""

from pulumi import export

import private.datalakehouse as datalakehouse

# use something in datalakehouse so linter is happy
export("raw_bucket_name", datalakehouse.raw_bucket.id)
export("curated_bucket_name", datalakehouse.curated_bucket.id)
