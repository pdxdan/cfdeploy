# Summary: Wraps the process of deploying a CloudFormation template
#
# Status: Creates and updates for most situations. Waiters seem to be working.
# To do: handle errors where CF template has not changed
#
# example testing:
# python deploy_or_update_stack.py HelloBucket3 CFTemplateSamples/HelloBucket.template

import boto3
import argparse
import os
import botocore.exceptions

parser = argparse.ArgumentParser(description="Wraps the process of deploying a CloudFormation template")
parser.add_argument("name", help="name of the stack to deploy")
parser.add_argument("template", help="local file containing the CloudFormation template")
parser.add_argument("-v", "--verbose", action="store_true", help="more debug messages to stdout")
args = parser.parse_args()
cfn_stack_params = []

cf = boto3.client('cloudformation', region_name='us-west-2')


def create_or_update_stack(sn):
    print "Creating or updating stack for " + sn + " with file " + args.template
    if stack_exists(sn):
        status=cf.describe_stacks(StackName=sn)['Stacks'][0]['StackStatus']
        debug("Stack status = " + status)
        if status.endswith('COMPLETE'):
            update_stack(sn)
        elif status == 'CREATE_IN_PROGRESS':
            cf.get_waiter('stack_create_complete').wait(StackName=sn)
            update_stack(sn)
        elif status == 'ROLLBACK_IN_PROGRESS':
            cf.get_waiter('stack_create_complete').wait(StackName=sn)
            create_stack(sn)
        elif status.startswith('UPDATE') and status.endswith('PROGRESS'): # Handles UPDATE_IN_PROGRESS, UPDATE_COMPLETE_CLEANUP_IN_PROGRESS, UPDATE_ROLLBACK_IN_PROGRESS & UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS
            cf.get_waiter('stack_update_complete').wait(StackName=sn)
            update_stack(sn)
        elif status == 'DELETE_IN_PROGRESS':
            cf.get_waiter('stack_delete_complete').wait(StackName=sn)
            create_stack(sn)
    else:
        print("Stack name " + sn + " does not exist, so I'll create it")
        create_stack(sn)


def stack_exists(sn):
    exists = False
    try:
        cf.describe_stacks(StackName=sn)
    except botocore.exceptions.ClientError as e:
        # AWS returns ValidationError when the stack doesn't exist
        if ( str(e.response['Error']['Code'])    == "ValidationError" and
             str(e.response['Error']['Message']).endswith("does not exist")
            ):
            print "Stack name " + sn + " does not exist"
            debug("It looks like the stack does not exist because we received this error from AWS:\n  " + str(e))
            exists = False
        else:  # Some other unexpected error happened
            raise e
    else:
        exists = True
        print "Stack name " + sn + " exists"
    return exists


def cftemplatecontent():
    content = open(args.template, 'r').read()
    return content


def create_stack(sn):
    print "Creating new stack: " + sn
    cf.create_stack(
        StackName=sn,
        TemplateBody=cftemplatecontent(),
        Parameters=cfn_stack_params,
        Capabilities=['CAPABILITY_IAM'],
        #? Open question: what Rollback behavior do I really want here?
        DisableRollback=True )
    cf.get_waiter('stack_create_complete').wait(StackName=sn)


def update_stack(sn):
    print "Updating stack: " + sn
    try:
        cf.update_stack(
            StackName=sn,
            TemplateBody=cftemplatecontent(),
            Parameters=cfn_stack_params,
            Capabilities=['CAPABILITY_IAM'] )
    except botocore.exceptions.ClientError as e:
        # AWS returns ValidationError when there aren't any changes in the stack to update
        debug(str(e))
        if ( str(e.response['Error']['Code'])    == "ValidationError" and
             str(e.response['Error']['Message']) == "No updates are to be performed."
            ):
            debug("It looks like the template hasn't changed because we received this error from AWS:\n  " + str(e))
            print "No changes detected for template. Skipping update."
        else:  # Some other unexpected error happened
            raise e

    cf.get_waiter('stack_update_complete').wait(StackName=sn)


def debug(s):
    if args.verbose:
        print "DEBUG:  " + s


create_or_update_stack(args.name)
