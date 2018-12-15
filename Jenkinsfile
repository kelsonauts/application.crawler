#!Groovy

nodeLabel = 'linux'

node(nodeLabel) {
	properties([
		parameters([
			booleanParam(name: 'deployStack', defaultValue: false, description: "Deploy crawler stack"),
			booleanParam(name: 'fillSqs', defaultValue: false, description: "Fill sqs to start crawling data. Requires stack to be deployed and storage to be available")
		])
	])
	stage('Checkout') {
		deleteDir()
		checkout scm
	}
	stage('Push scripts to s3') {
		result = sh(script: """
			aws s3 sync src/ s3://infrastructure-storages-useast1-s3bucket/src/
			aws s3 cp requirements.txt s3://infrastructure-storages-useast1-s3bucket/src/
			""",
			returnStdout: true)
	}

	stage('Deploy stack') {
		if (params.deployStack as Boolean) {
		result = sh(script: """
			./infrastructure/deploy.sh
			""",
			returnStdout: true)
		} else {
			print("Skipping stage...")
		}
	}

	stage('Fill sqs') {
		if (params.fillSqs as Boolean) {
			result = sh(script: """
			python src/filler.py
			""",
			returnStdout: true)
		} else {
			print("Skipping stage...")
		}
	}
}