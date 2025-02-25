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
