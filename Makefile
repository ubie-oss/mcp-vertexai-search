# Copyright 2025 yu-iskw
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Set up an environment
.PHONY: setup
setup: setup-python

# Set up the python environment.
.PHONY: setup-python
setup-python:
	bash ./dev/setup.sh --deps "development"

# Check all the coding style.
.PHONY: lint
lint:
	trunk check -a

# Check the coding style for the shell scripts.
.PHONY: lint-shell
lint-shell:
	shellcheck ./dev/*.sh

# Check the coding style for the python files.
.PHONY: lint-python
lint-python:
	bash ./dev/lint_python.sh

# Format source codes
.PHONY: format
format:
	trunk fmt -a

# Run the unit tests.
.PHONY: test
test:
	bash ./dev/test_python.sh

# Build the package
.PHONY: build
build:
	bash -x ./dev/build.sh

# Clean the environment
.PHONY: clean
clean:
	bash ./dev/clean.sh

all: clean lint test build

# Publish to pypi
.PHONY: publish
publish:
	bash ./dev/publish.sh "pypi"

# Publish to testpypi
.PHONY: test-publish
test-publish:
	bash ./dev/publish.sh "testpypi"


run-server:
	uv run mcp-vertexai-search serve \
		--project_id ubie-yu-sandbox \
		--location us \
		--datastore_id test-tech-docs_1739852696758

build-docker:
	docker build --rm -t mcp-vertexai-search:dev .

.PHONY: run-docker-server
run-docker-server:
	docker run -it --rm \
		-v "$(shell ${HOME}/.config/vertexai):/root/.config/vertexai" \
		-p 8080:8080 mcp-vertexai-search:dev


test-stdio-serve:
	source .env && \
		npx @modelcontextprotocol/inspector \
			uv run mcp-vertexai-search serve \
				--model_project_id $${MODEL_PROJECT_ID} \
				--model_location $${MODEL_LOCATION} \
				--datastore_project_id $${DATASTORE_PROJECT_ID} \
				--datastore_location $${DATASTORE_LOCATION} \
				--datastore_id $${DATASTORE_ID} \
				--transport stdio

test-sse-serve:
	source .env && \
		npx @modelcontextprotocol/inspector \
			uv run mcp-vertexai-search serve \
				--model_project_id $${MODEL_PROJECT_ID} \
				--model_location $${MODEL_LOCATION} \
				--datastore_project_id $${DATASTORE_PROJECT_ID} \
				--datastore_location $${DATASTORE_LOCATION} \
				--datastore_id $${DATASTORE_ID} \
				--transport sse

.PHONY: test-search
test-search:
	source .env && \
		uv run mcp-vertexai-search search \
			--model_project_id $${MODEL_PROJECT_ID} \
			--model_location $${MODEL_LOCATION} \
			--datastore_project_id $${DATASTORE_PROJECT_ID} \
			--datastore_location $${DATASTORE_LOCATION} \
			--datastore_id $${DATASTORE_ID} \
			--query "What is the segments?"
