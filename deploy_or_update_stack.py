## Status: creates new stacks fine, but fails to update existing stacks

import boto3
import argparse
import os
# import json
# import botocore.exceptions

parser = argparse.ArgumentParser()
cfn_stack_params = []

cftemplate = "CFTemplateSamples/HelloBucket.template"
# cftemplate = "AWSCloudFormation-samples/LAMP_Single_Instance.template"
cftemplatecontent = open(cftemplate, 'r').read()
cf = boto3.client('cloudformation', region_name='us-west-2')

def main():
    # print "The CF template looks like this: \n" + cftemplatecontent
    # create_or_update_stack("LAMP-Single-Instance")
    # create_or_update_stack("HelloBucket3")
    print cf.waiter_names


def create_stack(sn):
    cf.create_stack(
        StackName=sn,
        TemplateBody=cftemplatecontent,
        Parameters=cfn_stack_params,
        Capabilities=['CAPABILITY_IAM'],

        #??? Open question: what behavior do I really want here?
        DisableRollback=True
    )


def update_stack(sn):
    debug("attempting to update stack: " + sn)
    cf.update_stack(
        StackName=sn,
        TemplateBody=cftemplatecontent,
        Parameters=cfn_stack_params,
        Capabilities=['CAPABILITY_IAM']
    )


def create_or_update_stack(sn):
    print "Create or update stack: " + sn
    stacks = cf.list_stacks(
        StackStatusFilter=[
            'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE', 'UPDATE_ROLLBACK_IN_PROGRESS',
            'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
            'UPDATE_IN_PROGRESS'
        ]
    )
    stack_exists = False
    for s in stacks['StackSummaries']:
        debug("Comparing against existing stack: " + str(s['StackName']))
        if s['StackName'] == sn:
            if s['StackStatus'].endswith("COMPLETE"):
                print("Stack already exists, updating")
                update_stack(sn)
                stack_exists = True
                break
            else:
                stack_ready = False
                total_time = 0
                while stack_ready is False:
                    print(
                        "Stack exists but in state, {0} "
                        "and not ready to be updated, so I'll wait".format(s['StackStatus'])
                    )
                    stack_info = cf.describe_stacks(
                        StackName=sn
                    )['Stacks'][0]
                    if stack_info['StackStatus'].endswith("COMPLETE"):
                        update_stack(sn)
                        stack_ready = True
                    elif stack_info['StackStatus'].endswith("FAILED"):
                        raise Exception("Stack creation/update/rollback failed")
                    else:
                        total_time += 10
                        if total_time > 3600:
                            raise Exception("Stack creation/update timed out")
                        else:
                            time.sleep(10)
                            continue
    if stack_exists is False:
        print("Stack name " + sn + " does not exist, so I'll create a new one")
        create_stack(sn)

def debug(s):
    # set HSQDEBUG=true in your environment to enable verbose logging
    if str(os.getenv('HSQDEBUG')).upper() == 'TRUE':
        print "DEBUG:  " + s

main()
