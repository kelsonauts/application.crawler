#!/bin/bash -xe

#Move to directory with script
cd $(dirname $0)

STACK_NAME="crawler"
TEMPLATE_NAME="stack.yaml"

if [[ `aws cloudformation describe-stacks | jq ".Stacks[] | select(.StackName == \"${STACK_NAME}\")"` ]]; then 
	aws cloudformation update-stack --stack-name "${STACK_NAME}"  \
		--template-body file://"${TEMPLATE_NAME}" --capabilities CAPABILITY_IAM
	aws cloudformation wait stack-update-complete --stack-name "${STACK_NAME}"
else
	aws cloudformation create-stack --stack-name "${STACK_NAME}"  \
		--template-body file://"${TEMPLATE_NAME}" --capabilities CAPABILITY_IAM
	aws cloudformation wait stack-create-complete --stack-name "${STACK_NAME}"
fi