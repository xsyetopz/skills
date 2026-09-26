# Load variables from a named dotenv file; fail if it is missing.

set dotenv-load
set dotenv-filename := "example.env"
set dotenv-required

show-token:
    @echo "token=$API_TOKEN"
