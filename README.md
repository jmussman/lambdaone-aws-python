[//]: # (README.md)
[//]: # (Copyright © 2024 Joel A Mussman. All rights reserved.)
[//]: #

![Banner Light](./.assets/lambdaone-aws-python-light.png#gh-light-mode-only)
![banner Dark](./.assets/lambdaone-aws-python-dark.png#gh-dark-mode-only)

# LambdaOne-AWS-Python

## Synopsis

LambdaOne is a simple AWS lambda project with the goal of:

* Providing a template building an AWS Lambda function locally
* Using a third-party identity provider (IdP) for authorization
* Demonstrating local unit and integration testing, especially the dificulties of mocking class definitions
* Build a deployable Lambda using either a container or zip file

Start with the [AWS Lambda](https://docs.aws.amazon.com/lambda/) documentation and the
[Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html), but
almost nobody uses the embedded editor because developers rarely have access to deploy labda functions.
Information about building functions is farther along along the page, not necessarily obvious under "Configuring Functions".
There are two paths, one for [containers](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
and the other for deploying [zp files](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html).

This project provides a well defined structure for setting up the lambda code, performing both unit and integration tests,
and integrating third-party identity.
The lambda is very simple, simplying returning a line of of text.

The Boto3 library onbly supports AWS as the IdP for the application to the lambda authorization.
This project addresses using a more robust, third-party IdP for customer identity.
THis could be someline like Otka CIC (formally Auth0) for customer identity,
or for internal applications perhaps a workforce identity product such as Okta WIC.

A full set of example unit and integration tests are provided that cover
both the lambda function and the authorization code.
Deployment of lambda functions is normally the responsibility of the cloud administrators, not the developers, so
it is necessary as developers to have a full set of tests that make sure the project is robust and will work when deployed.
These tests are also necessary for performing regression testing
when new features are added or issues are fixed.

The Lambda Development Project section will explore how to build, test, and extend the template, and the
[Deploy to AWS](#deploy-to-aws) section below will address deployment using Docker or a zip file.

## Lambda Development Project Template

This section explores the layout of the project, the features, and how to test it.
The ulitmate goal is to build on this project as a template for real-world functions.

### Project Layout

The project layout is visible in the repository before setting up the project, so it is addressed first.

To start, AWS Lambda requires that the entry function be at the top of the task folder.
It is not possible to move this, but it may be named anything that you like.
If a more complex lambda scenario is decomposed into multiple files, place the remaining code under an appropriate package name
at the top level.
In this example, the main entry point is *lambda_function.py*, and the additional concerns
are separated into files under the *lambdaone* package.
The tests occupy a parallel structure under *test*.
Separating the tests makes it simpler to exclude them from the deployment container or zip file:

```
lambda_function.py
lambdaone/
    authz.py
    fixed_key.py
    hello_world.py
    jwt_key.py
test/
    integration/
        test_lambda_function.py
    unit/
        test_lambda_function.py
        test_lambdaone/
            test_authz.py
            test_fixed_key.py
            test_hello_world.py
            test_jwt_key.py
````

### Initializing the local development environment.

If you prefer, development may also be done in a [GitHub Codespaces](#run-the-tests-in-github-codespaces) environment, which is discussed in the next section.

The requirements for local development are:

* Python 3.8 or later; any distribution, e.g. Anaconda, should be fine.
The project was built and tested with Python 3.12.2 via Anaconda.
* Visual Studio Code
    * Add the Microsoft "Python extension for Visual Studio Code".
    This should also add the Microsoft "Python Debugger extension for Visual Studio Code", but
    if it does not make sure this is added too.

#### Instructions

1. Clone this project locally with *get clone [git@github.com:jmussman/lambdaone-aws-python.git](it@github.com:jmussman/lambdaone-aws-python.git)*.
1. Open the project in VS Code.
1. Open an integrated terminal with with View &rarr; Terminal.
Create a virtual python environment from the terminal.
The folder name .venv is important ($ is the command prompt):
    ```
    $ python -m venv .venv
    ```
1. Open the command palette with View &rarr; Command Palette...
Seach for *Python: Select Interpreter* and click on it.
Pick the python in the .venv folder, e.g. *Python 3.12.2 ('.venv') ./.venv/bin/python*.
1. Recommended: open VS Code settings, search for *Python Terminal Activate Environment*, and make sure it is checked.
It should be checked by default.
This will run the virtual environment activation script in each terminal window opened, which is necessary for the *Run and Debug* panel commands.
1. There are two sets of module requirements for the project, one for production and a second one with development dependencies.
Install both of these to the virtual environment (./.venv/lib) with pip at the command line:
    ```
    $ pip install -r requirements.txt
    $ pip install -r devrequirements.txt
    ```
1. The environment is ready to begin development or run the existing tests.
Skip over the next section on *GitHub Codespaces* and continue with [*Tests*](#tests).

#### Run the project in GitHub Codespaces

The button will replace the repository page in this tab with the Codespace, so read all the instructions first!

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=858797673) 

Click the button above (after reading the instructions) to open the project in GitHub Codespaces.
On the project configuration page presented click the *Create codespace* button to proceed.
The codespace will go through several initialization steps.
After the README.md file is displayed a terminal window named *Codespace* will open to run the script which finishes installation.

When the *pip* commands launched by the script finish in this window, and when the terminal window is left at a command prompt,
it is safe to close the terminal and start working with the project.

#### Tests

Open the VS Code *Run and Debug* panel from the toolbar and execute either task *All Tests* or *Coverage All Tests*".
A new terminal window named *Python* will open to display the resultsof the tests.
If code coverage is selected, the report will open in its own terminal window.

The integration test for *lambda_function, test_lambda_function.py*, requires a
JWKS endpoint at an authorization server to provide the public signing keys in JSON format.
This is handled internally in the test fixture by creating a Python HTTP server with a SimpleHTTPRequestHandler for the requests that serves files from
the test/resources folder.
The hardwired JSON key is in the resources folder.
The server starts when the test class is loaded, and is shut down when the test class ends.

*test_jwt_key* includes an example of mocking out a class definition.
The *jwt_key* module uses the *jwt.jwks_client.PyJWKClient* class to retrieve the JWKS
public keys from the IdP.
The problem is there are three ways the class could be referenced by the code under test (CUT).
The class is referenced in two places and can be used with a full qualified name from either
location: jwt.jwks_client.PyJWKClient or jwt.PyJWKClient.
the third way is for the CUT could load the class as a property using the form
"from jwt.jwks_client import PyJWKClient" or "from jwt import PYJWKClient".
In that case the reference to the class becomes a property of jwt_key.

To perform an opqaue-view test both of the references in the *jwt* module must be mocked, along
with the property that could be imported into jwt_key.
The *setUpClass* method in *test_jwt* mocks the two references, and then hoists them above the
import in the *jwt_key* module by reloading the module, causing the class reference to be reloaded in that module.
The setup method preserves the reference to the original class definition, and in the *teearDownClass* method
the original reference is put back and and both the *jwt* and *jwt_key* modules are reloaded to reset them.

#### Extending the template and using third-party authorization

One of the goals is for authorization from another IdP, such as Okta CIC (formally Auth0).
The *.env* file contains the externalized configuration for the authorization server, e.g.:

```
AUDIENCE=https://treasure
ISSUER=https://pid.pyrates.live
JWKSPATH=https://pid.pyrates.live/oauth2/v1/keys
REQUIRE=treasure:read
SIGNATUREKEYPATH=public.pem
```

Authorization from a JSON Web Token (JWT) will only be performed by the lambda if the *REQUIRE* property is set to
one or more scopes.
Separate multiple scopes with commas (spaces are allowed).

When authorization is used, the token granting those scopes must be sent as the authorization header property in
the HTTP request in the form of a bearer token:

```
authorization: bearer <token string>.
```

When tokens are used, the *AUDIENCE* and *ISSUER* properties must match what the IdP is expected to include in the JWT.

If the signatures are to be obtained with JWKS, the *JWKSPATH* property must be the URI of the JWKS endpoint at the authorization server.
The parallel *SIGNATUREKEYPATH* property references a local file for a PEM format key.
Because AWS Lambda requires that all the files be at the top of
the Docker image, that is where it must be placed and it always be just a file name.

The signature key path and the JWKS path are mutually exclusive, and the jwt_key module will refuse a configuration with both.


If the *REQUIRE* property is not set, a token is not required for the lambda to return a value.

## Deploy to AWS

### Building a container deployment

The advantage of a container deployment is the image may locally be tested in Docker.

This project originates from the [AWS Base Image for Lambda](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions).
There is not much point in repeating the details for deployement,
they can be found on the [Create a Lambda function using a container image](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html#runtimes-images-lp) page.
[Deploy Python Lambda functions with container images](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html) also reiterates the requirements,
covers building the application, the Dockerfile, using Docker to build and test the docker image, and most importantly,
connecting to and deploying the Docker project to AWS.

### Building a zip file deployment

A zip file is the simplest form of deploying a lambda function to AWS.

The base image is irrelevant if a zip file will be used for deployment; only the code is necessary.
[Working with .zip file archives for Python Lambda functions](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html) provides
the details of putting the deployment together.
The section on *Creating a .zip deployment package with dependencies* goes through the process of creating the zip file.

Per the instructions the packages in requirements.txt but be included at the root of the zip file.
The instructions use pip to install the packages into a separate folder, *.packages*.
However the packages are already installed into the *.venv/lib* folder so the packages found there may be added to the root of the zip file.
