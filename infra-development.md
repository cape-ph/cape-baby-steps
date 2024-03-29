# CAPE Infra Development

**WIP: THIS COULD CHANGE ANYTIME**

Much of this came out of reading the 
[CF user manual](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide)
in full. The [best practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
section in particular has a lot of good content.

## Tooling

### CloudFormation
* DevSide Linting `https://github.com/aws-cloudformation/cfn-lint` (editor 
  plugins exist for folks that want them and that use supported editors)
* Deployment Testing `https://github.com/aws-ia/taskcat`
* pre-commit hook to run linter (***NOTE*** we will want this run before trying 
  to commit in most cases. Running when you commit just slows things down, but 
  this would be a uaseful thing to implement to keep people from getting bad 
  stuff in) `https://aws.amazon.com/blogs/mt/git-pre-commit-validation-of-aws-cloudformation-templates-with-cfn-lint/`
  Client side hooks can be a bit of a pain to manage (unless things have changed 
  since i last looked at them), so we should think of an intelligent way to 
  handle making sure people are using it right
* there should be no specific developer constraints (e.g. editor mandates), but
  you'd be on your own to get things going correctly for your editor. VIM 
  (regular or neo) will almost certainly be supported by more than one person.
* i propose that all docs be written against the aws cli (as opposed to 
  documenting how to do things in their ui). for infra, this makes sense. the 
  UI may change and will be far more verbose to describe than cli, and the cli
  operations can be included in scripts where UI cannot.
* [cfn-guard](https://github.com/aws-cloudformation/cloudformation-guard) can
  be used to ensure templates adhere to policies defined as code. (e.g. if there
  is a rule that all s3 buckets created by a deployment must be encrypted, this
  can be checked developer side using this tool). probably a good thing for us 
  to use, and we can bake it into CI/CD as well.
* we should look into [custom resource types](https://docs.aws.amazon.com/cloudformation-cli/latest/userguide/resource-types.html),
  [modules](https://docs.aws.amazon.com/cloudformation-cli/latest/userguide/modules.html), 
  and [hooks](https://docs.aws.amazon.com/cloudformation-cli/latest/userguide/hooks.html)
  to see how we can use these reusable things. Third-party resource types may be 
  publicly available that we can use for some things. [See here for examples.](https://aws.amazon.com/blogs/aws/introducing-a-public-registry-for-aws-cloudformation/)

## Process

### Conventions
* standard gitflow for each repo:
  * main/release branch - tagged releases merged from develop when certain 
    conditions met. act of creating tag can kick off any needed CI/CD
  * development branch - integration branch that should be usable at any given 
    time (NO MERGES SHOULD BREAK IT). releases are created from this by merging 
    state to main/release and creating a tag
  * feature branches:
    * tied to issues
    * one person, one feature, one branch
    * for sanity, these should only be made off develop (no FB off an FB if 
      possible). this means getting reviews and merges done in a reliably 
      expedient manner so as to not hold others up
    * require an approved review to merge. 2 reviewers would be awesome, if the 
      team can support that (tho reviews by people that don't understand what 
      they're reviewing are often dangerous)
* propose that all CF templates be YML instead of JSON. the ability to comment 
  YML makes it superior for things humans have to do (json wins for machine to 
  machine interop)
* **HOW WILL WE HANDLE CM AND VERSIONING? WHAT DOES VERSIOINING MEAN IN AN AWS DEPLOYMENT ENVIRONMENT???**
* It is almost certain we will need to share values between stacks (e.g., ip 
  addrs, service ids, etc). there are a few ways to handle this and they all 
  have pros/cons. They are listed below, but tl;dr is that we may want to start
  with the SSM Parameter Store. All the below assumes we're pretty much using
  nested stacks under a top level main stack.
  * copy/paste all the things - i think this is a non-starter, but it is an 
    option. take service ids as the example, once an id is deployed and has an
    id, we copy it and paste it where we need it next. this will become 
    crazypants quickly and things will break when someone forgets to C/P 
    somewhere in the bowels of a not oft used service.
  * stack outputs and stack parameters - define outputs for substacks and then 
    reference those outputs in the parameters for other substacks. seems 
    perfectly valid but adds some nuance in nested stack land. e.g., if a 
    substack using an output from another fails to deploy, both stacks are 
    rolled back. also as far as i can tell lacks good support for secret values.
  * export/import - stacks can export and import values maintained per region 
    in aws for an account. so one substack can export a value, then anything 
    else in that account and region can import that value and use it. also seems
    legit, but has the drawback that exports are immutable and versioned. so if
    a value changes, other substacks have to be modified to grab a new version 
    and then be redeployed. so if things change a lit, this gets harder to 
    manage.
  * AWS System Manager Parameter Store - essentially a key/value store that 
    exists outside stacks. this can handle secrets. templates are coded to grab 
    the current value from the store. seems pretty simple and flexible. for 
    `standard` paremeters (params < 4kb, up to 10000 of them), there is no 
    charge. for `advanced` params (4kb - 8kb), there is a monthly charge per 
    param (currently $0.05 per param per month). the 10000 cap is per account, 
    so if the customer has a ton of params already, we could be racking up a 
    charge for what would normally be a standard param.

### Repos
* we'll want one main repo for infra for sure to start. may want to go the route
  of a repo per stack down the road. but if we go pure nested, then we can still
  maintain one repo
* may want additional repos for reusable parts (template snippets or modules 
  maybe? not sure yet)
* probably a repo per lambda function or similar things

### Stack Repo Layout
This is just an initial proposal. We could go with it and refactor later if 
needed, or this could be shot down from the start. 

This proposal assumes we're going to want the infra as a whole all the time 
(never deploying just a piece for any given customer). Note this does not mean
that we would never deploy just a piece when we already have the whole deployed
as a start (imagine an update that only affects one substack, we wouldn't deploy
the entire thing again, just the update...but that would be managed for us, we 
would still do the deploy as though we were deploying the whole things). As 
such, there is one repo for all the stacks.

There is a main stack template that is the root for all the others. Substacks
are divided up by access scopes (think VPCs) and then those are further divided
by plumbing and porcelain (following the git pattern). Plumbing are things 
behind the scenes that need to exist before porcelain can be used (e.g., IAM
setup, VPCs, security or network setup, etc.) while porcelain includes things
like the services users will interact with (explicitly or implicitly).

***NOTE:*** In the repo layout below, no `.yml` files are definite except for 
the `cape-infra.yml` top-level stack. All the others are just provided for 
example's sake.

```
repo-root/
  substacks/
    common/
      plumbing/
        load-balancer.yml
        vpc-peering.yml
        ...
      porcelain/
        container-registry.yml
        data-transfer.yml
        ...
    private/
      plumbing/
        vpc.yml
        security-groups.yml
        network.yml
        ...
      porcelain/
        storage.yml
        data-transfer.yml
        data-lakehouse.yml
        ...
    protected/
      plumbing/
        vpc.yml
        security-groups.yml
        network.yml
        ...
      porcelain/
        data-sets.yml
        api.yml
    public/
      plumbing/
        vpc.yml
        security-groups.yml
        network.yml
        ...
      porcelain/
        dashboards.yml
  cape-infra.yml
  README.md
```

### CI/CD
* for sure, we'll want the `cfn-lint` pre-commit hook (though again, peeps 
  should be runninng that before any commit is attempted), but as stated above, 
  client side hooks can be a bit of a pain to manage unless things have changed.
* for anything that yields a container image, we'll need CI/CD to kick off those 
  builds and get things into a registry
* for anything that yields an installable package or lambda funciton, we'll need 
  CI/CD to kick off  those builds and get things into a registry
* we may want to look at our CI/CD automating the CD more than we have in the 
  past (actually deploying to integration if we can). ***note*** this may be
  a bad idea as we should get in the habit of making change sets before 
  deploying as that is probably the way staging and prod will be in reality. an
  automated deployment may not give us the ability to do that
* if we really wish to have CD, we need a reasonable test apparatus that can 
  fail on any error. this is a time/$ concern (may be able to automate some 
  stuff using [codepipeline](https://docs.aws.amazon.com/codepipeline/latest/userguide/welcome.html) 
  at additional cost 

### Users/Access
* drew and micah need to be able to deploy for sure, as well as be owners of the 
  infra repo(s). We can discuss others, but not everyone should be able to do 
  this stuff.

### Deployments
* staging and prod (at a minimum) should not deploy without generating and 
  reviewing a change set (i.e. no blind automated deployments of these 
  environments by CI/CD). 
* all changes need to go through CF if we use it. manually mucking with 
  resources could cause further deployments to fail. if manual mucking is really 
  necessary, we need to have a procedure to unmuck before deploying again.
* we should look into [stack policies](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html)
  to protect critical resources from oopsies.
* nested stacks seem to be how you can separate stacks that are used together, 
  as we will probably have
* stack sets are used when similar stacks are needed in different accounts or 
  regions, managed by the same command. it's an all for one model where updating
  the set updates all related stacks in the same way (really for regional 
  redundancy it seems, though you can delete a region and leave others intact)
* we need to be aware of drift [detection capabilities](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-drift.html) 
  in AWS (and when it will give bunk results)
* [refactoring stacks](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/refactor-stacks.html)
  is a thing


## Arch Considerations
* There are things we will require outside of stack definitions in this repo:
  * An IAM user to actually deploy the stack (e.g. a deployment user). This 
    could end up being multiple users or one or more groups. Unknown at this 
    point
  * One or more S3 buckets for deployments. With CF, if you manage your 
    templates outside AWS land (like we are in GH), they need to end up in an 
    S3 bucket to be deployed. This should not be part of any S3 exposed to the 
    system as a whole, and is just for the deployment scenario.
  * Whatever we're going to use to manage certs/keys and secret management. 
  * ***More TBD***
* this system will have a ton of moving parts. we need to be really careful 
  about versions of things staying in sync between all of our environments. e.g.
  if we have an integration EC2 instance that has been `yum update`d a bunch
  and that doesn't happen on the staging or prod system for whatever reason, we 
  could have issues. manging versions and updates will be a risky concern.
* we may have certain constraints levied at times by customer requirements (e.g.
  CF will be used and all deployments must happen within a VPC as a theoretical 
  customer mandated requirement). we do need to be careful however that one 
  customer's desires do not drive things such that they become unworkable by 
  others (e.g. if we want this to be usable by more than GDPH, we cannot let 
  their rules affect the ability for USVI to deploy in their own set of rules.
* we need to read up on [AWS service quotas](https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html)
  before doing any real detailed design. There are limits of the AWS system 
  itself as well as its services that we will need to be aware of. if the system 
  is deployed into an existing AWS account, we could hit limits as a result of 
  other things in their account that we have no control over (e.g. 
  each account can support a max of 2000 CF stacks oer region, only one glue 
  catalog can exist per region in any aws account, or the max number of 
  provisioned DPUs for Batch is 1000 at any time per account, etc)
* need to figure out how we want to handle dev/integration/staging/prod setups.
  we will at a minimum need 2 environments (prod and some lower tier). 
  depending how other parts of the system go, we may want more. it's somewhat 
  unclear right now what the needs are of non-infra development (e.g. team 
  members making pipelines or something as part of our work) and so it's not 
  clear yet if we need some development environment, or if we could get by with 
  an integration env. we would like a place to test deployments/do integration 
  tests and another to do pre-prod deployments as well. we could also look into 
  using the [blue/green deployment](https://docs.aws.amazon.com/whitepapers/latest/overview-deployment-options/bluegreen-deployments.html)
  or other things aws makes available, but will need to see what the best bang 
  for buck route is.
* we should get up to speed on the [CF Registry](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/registry.html)
  and how to break things up into [modules](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/modules.html).
  ***NOTE*** modules are different than resuable template snippets
* get up to speed on [ec2 helper scripts]9https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-helper-scripts-reference.html)
  if we do any EC2 specific work
* we may need [VPC Interface Endpoints](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/vpc-interface-endpoints.html)
  for the VPC to reach CloudFormation. Not clear to me yet that this is 
  definitely needed in all cases (like this is needed for CF to function at 
  all), or only if needed if something within the VPC needs to do CF stuff. If 
  we can deploy from outside the VPC (so like from our laptops without being on 
  a VPN or anything) without these endpoints, we may be ok. Also need to work 
  out what constraints we will have imposed on us by customer network 
  requirements (in GPHL inv, we have to ssh to a specific box on the VPC in 
  order to deploy with ansible, but that may because we're not going a pure AWS 
  `cfn-init` route.
* we're going to want to look at [VPC Peering](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html)
  when it somce time to do the interaction between public/private/protected 
  swimlanes.
* documentation fo CF suggests a lifecycle and ownership division of large 
  stacks into smaller ones. that may be a good thing to consider long term, but 
  we may well start with one stack and then break up as needed. this is another 
  place we need to consider constraints levied by customer requirements.
  * for this to work, we would need to identify "who owns what" from the 
    perspective of long term responsibility. the owners are essentially those 
    responsible for updating their stuff on their schedule. obviously when parts
    of one stack are dependent on parts of another (e.g. a website in one stack
    is reliant on the database of another), there is a share responsibility when
    it comes to changing/updating parts.
  * our functional boxen on the arch diagram may be the start of stack 
    separation (or it could seem that way but be a poor division). given the 
    functional breakdown of that diagram, it's more of a service oriented arch 
    (each functional block is a "service" and the services communicate between 
    as needed).
* The user guide for CF contains a [snippets section](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/CHAP_TemplateQuickRef.html)
  with a lot of reusable patterns for various services and general use.

