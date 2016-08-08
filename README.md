# cfdeploy
Wraps the process of deploying an AWS CloudFormation template

Applying CloudFormation templates is fairly easy with a single CLI call, but if you want to deploy from a CI/CD pipeline there are a lot of edge cases to handle. This script wraps the actual deploy/update process to make our pipeline more robust.


usage: deploy_or_update_stack.py [-h] [-v] name template

positional arguments:

* name:     name  of the stack to deploy
* template: local file containing the CloudFormation template

optional arguments:

*  -h, --help     show this help message and exit
*  -v, --verbose  more debug messages to stdout
