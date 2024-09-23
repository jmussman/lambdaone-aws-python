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
* Demonstrating local unit and integration testing
* Build a deployable Lambda using either a container or zip file

Start with the [AWS Lambda](https://docs.aws.amazon.com/lambda/) documentation and the
[Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html).
Information on building functions is buried farther along the page under "Configuring Functions" which
is not such an obvious place.
There are two paths, one for [containers](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
and the other for deploying [zp files](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html).

This project provides a structure for setting up the lambda code, and performing both unit and integration tests.
The Lambda is very simple, it simply returns a line of text.

AWS assumes in the Boto3 library that you will use AWS as the IdP for for authorizing the application to the Lambda,
if necessary.
This project addresses using a more robust IdP for customer identity, such as Otka CIC
(formally Auth0),
or for internal applications perhaps a workforce identity product, such as Okta WIC.

A full set of example unit and integration tests are provided, that cover
both the lambda function iteself the authorization code.
These are necessary for maintaining a robust lambda project and performing regression testing
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

### Tests

Run the unit and integration tests from the *Run and Debug* panel using the *All Tests* or *Coverage All Tests* launch configuration.
The tests will run in the terminal window labeled *Python Debug Console*.
If coverage is selected, the code coverage report will open in another terminal window.

The integration test for *lambda_function* requires a JWKS server to provide the key in JSON format.
This is handled by creating a Python HTTP server with a SimpleHTTPRequestHandler for the requests that serves files from
the test/resources folder.
The hardwired JSON key is in the resources folder.
The server starts when the test class is loaded, and is shut down when the test class ends.

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
