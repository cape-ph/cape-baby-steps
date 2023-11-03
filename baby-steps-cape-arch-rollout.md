# Baby Steps CAPE Arch Rollout

This is a proposed set pf phases for rolling out the CAPE architecture we have 
proposed. **NOTE** this doesn't necessarily end in the actual system, but gets 
us experience in all the moving parts to build a toy system for demonstration 
purposes. 

At any point, we could decide to stop the toy implementation and switch to the 
real thing. That will require a lot of questions to be answered and decisions to 
be made however, and this proposed set of phases allows us to get the experience 
needed to deploy and connect these things without being held up waiting for 
those answers. 

Even if we were to start with the Real Thing (tm) today, this is probably a 
decent order to go about things at least given what is known at this time.

Following the phases below, there is a listing of unallocated functions. These
are intended to be brought into phases as things become clearer.

## Roll Out Phases

### Baby - "Hello-World" Phase 1

This phase would be to get the ball rolling, and will focus on minimal items to 
get deployment and interaction going. The main functions included would be 
simple data transfer (uploading of specifically formatted CSVs via S3 upload),
a super simple data transform (e.g. if the csv has a "Date of Birth" column, 
change to "DOB" or something equally as trivial), basic lakehouse (raw and 
curated buckets), and a way to view data in the buckets (e.g. S3 download).

This will serve as our initial foray into this stuff and will give us a way to 
start testing deployments with CloudFormation. It will also serve as a place to 
set up repos and automation for deployment when repo contents change (given some
appropriate trigger, not just on any repo change).

#### Management Tools (IAM Users)
* (reg_user) a private regular user - can do things at the edges (produce and 
  consume data)
* (admin_user) a private admin user - can manage the stack
* (partner_user) a protected (partner) user - in this phase, this is used to 
  ensure they cannot access anything

#### VPC
* "Private" swimlane only. (At present, thinking the different scope resolutions
  are each a VPC. This assumes things like the set of users that need access to 
  the left and right protected swimlanes are the same set)...but for phase 1, 
  only talking private swimlane and thus one private vpc)

#### Data Transfer
For phase 1, we want to see that
* raw data can come into the system by private VPC users (partner_user should 
  not have access to anything)
* some raw data forces a transform to occur (something very simple)
* both raw and transformed data are stored in the correct location (raw bucket 
  and curated bucket)
* raw and curated data can be accessed by private users (e.g. via S3 
  download)

##### Ingest
* simple S3 upload allowed by private users
* this would be limited to specifically formatted CSV files (that can have one 
  of 2 formats: the expected one and the one that would force the transform)

##### Transform
* a very simple transform under very specific conditions. E.g., if a csv comes 
  in with a "Date of Birth" column, change to "DOB". 
* This transform can be done with something like Lambda for now

#### Data Lakehouse
* this would only have 2 buckets (raw and curated) for now with no metastore
* during ingest, data as is goes into raw bucket no matter what
* during ingest, check if transform needed
  * if the transform trigger is hit, then transform runs and the result goes 
    into curated bucket. 
  * if transform trigger is not hit, then data goes directly into curated bucket

##### File Interface
* though our arch diagram has this as a protected function, we'll want to test
  with private only till the protected is sorted out
* want to make sure that only private users can access the raw and curated data 
  (partner_user cannot)

### Great Ape - Phase 2

This is one we should make a priority decision on. I would see the next baby 
step as either:
* go down the metastore and query engine route building on phase 1
  * This is probably the logical option as we don't need to worry about getting
    tower sorted or what triggers pipeline execution (or what users can do this)
  * we will need this no matter what pipeline arch we end up with
  * buys us time to get pipeline stuff better defined
  * doesn't require us to add new storage buckets
  * **probably way simpler than pipelines**
  * allows us to put together a simple analysis demo as well (using the query 
    engine to show something an end user might actually do, though not with 
    pipeline results)
* go down the running pipeline route building on phase 1
  * this is more of a whizbang that gets users interested and is far sexier than
    metastores and query engines (well, to normal folk at least). Stated another 
    way, **this demos better**
  * this is more complicated and will require us getting a container registry of 
    some sort together (suppose we could use dockerhub for testing, but it's not 
    a very useful thing to put on dockerhub for public consumption)
  * would require us to get a compute engine together (Batch, SLURM, etc)
  * if we did this, would think it would entail some really contrived 2 stage 
    pipeline (so we can see a pipeline actually going instead of a single stage 
    that may give us a false sense of something working)

The actual parts of what this entails depend on which route we go, so  **TBD**

### Kamehameha - Phase 3
This would take the outcome of Phase 2 and add the route we did not go in that.

The end result would be the ability to do an analysis on a pipeline result

### Kaioken (Over 9000) - Phase 4
**TBD**

### 100x Gravity - Phase 5
**TBD**

### Spirit Bomb - Phase 6
**TBD**

### Super Saiyan - Phase 7
**TBD**

## Unallocated Functions
These are things that we think we need, but that have not been allocated to a 
phase yet. In fact the only phase that's really spelled out well is Phase 1. As 
we set targets for future phases, these functions should be moved into those 
phases in a manner that allows their addition to build on previous phases.

### VPC
* protected swimlanes (if the 2 protected swimlanes we have end up not being the 
  same VPC, then this is actually 2 functions)
* public swimlane
* moving private shims for protected functions into protected VPC - in phase 1, 
  the `File Interface` function is put in the private VPC for testing purposes.
  This is a protected function however. This is for getting any protected items 
  that were put in the private VPC for testing into the protected VPC(s) as 
  needed. **May become multiple items if it needs to be split between phases**

### Data Transfer
* Ingest via non-S3 file upload
  * SFTP
  * **OTHER??**
* Schema detection (not real sure where this fits in, but it's somewhere)
* More realistic transforms
  * Putting data into queryable formats (e.g. delta lake, ORC, parquet, etc) - 
    this probably goes with Schema detection
  * **OTHER??**

### Data Lakehouse
* Pipline Result storage
* Analysis Result storage
* Archival

### Pipeline Execution
* More realistic pipelines
* Wire up to orchestrator (e.g. Tower)
* Pipeline intermediate storage

### Management Tools
* Tower or whatevs
* Introduction of authz roles
* Introduction of connections between swimlanes.

### Bioinformatics
* **TBD**

### Legal/Compliance
* **TBD**

### File Interface
* Consumption via non-S3 file download
  * SFTP
  * **OTHER??**

### Visualization & Analytics
* **TBD**

### Business Intelligence
* **TBD**

### Machine Learning
* **TBD**

