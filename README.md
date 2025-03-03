# shift-bob
Slack app to help teams track on-call rotations.

### socket vs http mode
For HTTP mode consider ngrok for local/dev setup:
```shell
brew install ngrok
ngrok config add-authtoken <YOUR-NGROK-TOKEN>
ngrok http 3000
```

Slack docs: [Exploring HTTP vs Socket Mode](https://api.slack.com/apis/event-delivery)


### docker
Make sure you have correct Slack tokens set in `.env` (check `.env.example` for references).
```shell
docker-compose up
```

### gcp
`dev2lz` repository should exist in your project/region before running build command.
```shell
# build docker image in GCP
make gcp-build
```
