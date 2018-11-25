#!/bin/bash -xe

STACK_NAME="crawler"
TEMPLATE_NAME="stack.yaml"

if [[ `aws cloudformation describe-stacks | jq ".Stacks[] | select(.StackName == \"${STACK_NAME}\")"` ]]; then 
	aws cloudformation update-stack --stack-name "${STACK_NAME}"  \
		--template-body file://"${TEMPLATE_NAME}"
	aws cloudformation wait stack-update-complete --stack-name "${STACK_NAME}"
else
	aws cloudformation create-stack --stack-name "${STACK_NAME}"  \
		--template-body file://"${TEMPLATE_NAME}"
	aws cloudformation wait stack-create-complete --stack-name "${STACK_NAME}"
fi