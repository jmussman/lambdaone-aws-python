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

## Project

### Layout

To start, AWS Lambda requires that the entry function be at the top of the task folder.
If a more complex scenario requires multiple files, place the remaining code under an appropriate module name.
In this example, the main entry point is *lambda_function.py*, and the additional concerns
are separated into files under the lambdaone module.
The tests occupy a parallel structure under *test* to make it simple to exclude them from the container or zip file:

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

### Initializing the development environment.

The expected integrated development environment (IDE) for this project is visual studio code.
Python 3.8 or later is required; this project was built and tested with version 3.12.2.

If you prefer to run the project in GitHub Codespaces [jump ahead](#run-the-tests-in-github-codespaces)


#### Instructions

1. Clone this project locally with *get clone git@github.com:jmussman/lambdaone-aws-python.git*.
1. Open the project in VS Code.
1. In the project create a virtual python environment from the terminal.
The folder name .env is important:
    ```
    $ python -m venv .venv
    ```
1. From the VS Code command palette run *Python: Select Interpreter* and pick *.venv/bin/python*.
1. Recommended: open VS Code settings, search for *Python Terminal Activate Environment*, and make sure it is checked.
This will run the activation script in each terminal window opened.
1. There are two sets of module requirements for the project, one for production and a second one with development dependencies.
Install both of these with pip at the command line:
    ```
    $ pip -r requirements.txt
    $ pip -r devrequirements.txt
    ```
1. Now the environment is ready to begin development or run the existing tests.

#### Run the tests in GitHub Codespaces

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=858797673) 

Click the button to open the project in GitHub Codespaces.
Wait for codespaces to open and initialize, watch to see that the *pip* commands to install the packages finish executing.
In the VSCode Run and Debug panel execute *All Tests* or *Coverage All Tests*".
A new terminal window will open to display the results (and a second window for the report if code coverage is run).

### Tests

Run the unit and integration tests from the *Run and Debug* panel using the *All Tests* or *Coverage All Tests* launch configuration.
The tests will run in the terminal window labeled *Python Debug Console*.
If coverage is selected, the code coverage report will open in another terminal window.

The integration test for *lambda_function, test_lambda_function.py*, requires a JWKS server to provide the key in JSON format.
This is handled by creating a Python HTTP server with a SimpleHTTPRequestHandler for the requests that serves files from
the test/resources folder.
The hardwired JSON key is in the resources folder.
The server starts when the test class is loaded, and is shut down when the test class ends.

*test_jwt_key* includes an example of mocking out a class definition.
The *jwt_key* module uses the *jwt.jwks_client.PyJWKClient* class to retrieve the JWKS
public keys from the IdP.
The problem is there are six ways the class could be referenced by the code under test (CUT).
The class is referenced in two places and can be used with a full qualified name from either
location: jwt.jwks_client.PyJWKClient or jwt.PyJWKClient.
To compund the problem the CUT could load the class as a property using the form
"from jwt.jwks_client import PyJWKClient" or "from jwt import PYJWKClient".
In that case the reference becomes a property of jwt_key.

So to do an opqaue-view test both of the references in the *jwt* module must be mocked along
with the property that could be imported into jwt_key.
The *setUpClass* method in *test_jwt* mocks the two references, and then hoists them above the
import in the *jwt_key* module by reloading the module.
The reference to the original class definition is preserved, and in the *teearDownClass* method
it replaces the reference and then reloads both the *jwt* and *jwt_key* modules.

### Authorization

One of the goals is for authorization from another IdP, such as Okta CIC.
The *.env* file contains the externalized configuration for the authorization server:

```
AUDIENCE=https://treasure
ISSUER=https://pid.pyrates.live
JWKSPATH=https://pid.pyrates.live/oauth2/v1/keys
REQUIRE=treasure:read
SIGNATUREKEYPATH=
```

The audience and issuer settings must match what the IdP produces.
If the signatures are obtained with JWKS, the variable must be the URI of the server.
The signature key path and the JWKS path are mutually exclusive.
THe signature key path is used to point to a local file with the PEM public key to verify the token signature.
If require is set too one or more scopes, a token granting those scopes must be sent as the authorization header property;
this is a *bearer* token in the form *authorization: bearer \<token\>*.

If require is not set, a token is not required for the lambda to return a value.

### Building a container deployment

The project is built from the [AWS Base Image for Lambda](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions).

### Building a zip file deployment

The base image is irrelevant if a zip file will be used for deployment; only the code is necessary.
