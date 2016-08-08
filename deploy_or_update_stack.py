## Status: Creates and updates for most situations. Waiters seem to be working.

# To do: handle errors where CF template has not changed


import boto3
import argparse
import os
import botocore.exceptions

parser = argparse.ArgumentParser()
cfn_stack_params = []

cftemplate = "CFTemplateSamples/HelloBucket.template"
cftemplatecontent = open(cftemplate, 'r').read()
cf = boto3.client('cloudformation', region_name='us-west-2')

def main():
    # print "The CF template looks like this: \n" + cftemplatecontent
    create_or_update_stack("HelloBucket3")

    # print cf.waiter_names
    # stack_exists('HelloBucket3')

    # print cf.describe_stacks(StackName='HelloBucket33')

def create_or_update_stack(sn):
    print "Creating or updating stack: " + sn
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
        elif status.startswith('UPDATE') and status.endswith('PROGRESS'):
            # Handles UPDATE_IN_PROGRESS, UPDATE_COMPLETE_CLEANUP_IN_PROGRESS, UPDATE_ROLLBACK_IN_PROGRESS & UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS
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
        if str(e.response['Error']['Code']) == "ValidationError":
            print "stack name " + sn + " does not exist"
            debug("It looks like the stack does not exist because we received this error from AWS:\n  " + str(e))
            exists = False
        else:
            # Some other unexpected error happened
            raise e
    else:
        exists = True
        print "stack name " + sn + " exists"
    return exists


def create_stack(sn):
    debug("attempting to create stack: " + sn)
    cf.create_stack(
        StackName=sn,
        TemplateBody=cftemplatecontent,
        Parameters=cfn_stack_params,
        Capabilities=['CAPABILITY_IAM'],
        #??? Open question: what Rollback behavior do I really want here?
        DisableRollback=True )
    cf.get_waiter('stack_create_complete').wait(StackName=sn)


def update_stack(sn):
    debug("attempting to update stack: " + sn)
    cf.update_stack(
        StackName=sn,
        TemplateBody=cftemplatecontent,
        Parameters=cfn_stack_params,
        Capabilities=['CAPABILITY_IAM'] )
    # waiter = cf.get_waiter('stack_update_complete')
    # waiter.wait(StackName=sn)
    cf.get_waiter('stack_update_complete').wait(StackName=sn)


def debug(s):
    # set HSQDEBUG=true in your environment to enable verbose logging
    if str(os.getenv('HSQDEBUG')).upper() == 'TRUE':
        print "DEBUG:  " + s

main()
