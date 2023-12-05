# CAPE Babysteps Cost Breakdown

## Phase 1

This section is specific to phase 1 of the bab-steps rollout.

### Stack Hierarchy

Below is the breakdown of the stack and nested stacks. Each item prefixed with 
`(*)` has an associated cost. Those will broken down in the section that follows 
the hierarchy. Each item is also prefixed with the type of resource (e.g. stack, 
iam user, iam group, lambda function, etc) in the format `/type/`.

If items do not have a specific name (not counting the identifier used in the 
CFN template only), the placeholder `NO NAME` will be used.

* /stack/ NO NAME (main stack)
  * /stack/ capebs-protected-stack
    * /stack/ capebs-protected-iam-stack
      * /iam user/ us-east-1_protected-partner
  * /stack/ capebs-private-stack
    * /stack/ capebs-private-iam-stack
      * /iam group/ us-east-1_capebs-raw-bucket-group
        * /iam group policy/ capebs-raw-bucket-group-policy
      * /iam group/ us-east_capebs-curated-bucket-group
        * /iam group policy/ capebs-curated-bucket-group-policy
      * /iam user/ us-east-1_private-admin
      * /iam user/ us-east-1_private-unpriv
    * /stack/ capebs-private-dlh-stack
      * (*) /s3 bucket/ capebs-private-dlh-raw-bucket
      * (*) /s3 bucket/ capebs-private-dlh-curated-bucket
      * /lambda permission/ NO NAME
      * /iam role/ NO NAME
        * /lambda policy/ capebs-xform-lambda-raw-bucket-policy
        * /lambda policy/ capebs-xform-lambda-curated-bucket-policy
      * (*) /lambda function/ NO NAME
    * /vpc/ NO NAME

### Cost breakdown

The only things that seem to have cost in this phase 1 are S3 and Lambdas. 
Stacks, IAM resources and VPCs do not have additional cost. 

We may require some additional VPC related things (like a VPN) that do have 
associated cost. For phase 1, we are using a single VPC (the private one) and 
unless we need a VPN available for testing that out, we wouldn't have more cost.

If we're building this in the GTRI AWS to start, I would guess we'd already be 
covered by the GTRI VPN for access (**I do not know that to be true** at this 
time) and would not need to worry about traffic from the public internet. Going
forward, we may need a VPN unless wherever we are testing builds is already 
behind a VPN.

**CAVEAT:** We will certainly be spinning up and tearing down resources a bunch 
in the short term. This is the learning function for the team. The costs 
outlined below are for a stable, running set of resources. During the initial 
phases, we may in fact be charged a full month for every cost-accruing resource 
we create, even if we tear it down seconds later. So we need to keep that in 
mind.

* pricing as of 12/04/2024
  * [S3 pricing](https://aws.amazon.com/s3/pricing/)
  * [Lambda pricing](https://aws.amazon.com/lambda/pricing/)
* Lambda Function
  * Assumptions
    * Default memory size of 128MB. Cost increases as a function of memory (as 
      does CPU allocation, but that is not controllable)
    * We'll assume a runtime of 10 seconds. This is real high for a small csv. 
      Especially since we only process the header row and do no error checking.
  * Cost
    * $0.0000000021/ms * (10s * 1000ms) = $0.000021 per run

* S3 buckets
  * Assumptions
    * Standard S3 (no intelligent tiering, etc)
    * Only the 2 buckets for now
    * We won't exceed 1GB per bucket in this test case. Versioning is enabled, 
      so if a single file is drastically changed repeatedly with huge 
      differences, we may consume more than this (versioning requires multiple 
      copies of objects with the differences between changes), but we would 
      really have to abuse the phase 1 setup (or store way more than 
      anticipated).
    * All data transfer between buckets and services is in the same AWS region
    * I believe all of our data tranfer is not chargeable. This is based on a 
      reading of the `Data Transfer` tab of the s3 pricing page linked above.
      I can't imagine we'll hit the xfer out cap of 100GB/month that starts 
      accruing cost (comes into play when downloading files from s3), xfer in is 
      free of charge (comes into ply when uploading csv), and all the other xfer 
      is within region and falls under the `except`'s called out on the 
      `Data Transfer` tab.
  * Cost
    * 2 * ($0.023/GB/month) = $0.046/month
  
