# tools

miscellaneous tools

## slack-message-exporter

指定した Slack の Channel のメッセージをテキストファイルに出力する。
予め Slack API に必要な設定を済ませておくこと, `SLACK_API_TOKEN` 環境変数に User OAuth Token を設定しておく必要がある。

### Setup

1. Workspace の Slack API 設定をする
   1. <https://api.slack.com/apps> にアクセス
   2. Create New App > From Scratch
   3. 任意の App Name を入力し, エクスポートしたい Workspace を選択して Create App
   4. Basic Information > Building Apps for Slack > Add features and functionality > Permissions
   5. OAuth & Permissions > Scopes > User Token Scopes > Add an OAuth Scope で以下追加:
      - `channels:history`
      - `users:read`
   6. OAuth & Permissions > OAuth Tokens for Your Workspace > Install to Workspace > 許可する
   7. OAuth & Permissions > OAuth Tokens for Your Workspace の User OAuth Token を `SLACK_API_TOKEN` として利用することになる
2. Python 3.6 以上をインストールしておく

### Usage

```console
usage: slack_message_exporter.py [-h] channel_id file

Export Slack messages including threads in the specified channel. You need to set environment variable SLACK_API_TOKEN first.

positional arguments:
  channel_id  channel_id to export messages
  file        file to output messages

optional arguments:
  -h, --help  show this help message and exit
```

### Example

```sh
SLACK_API_TOKEN=xoxp-1234567890-1234567890-1234567890-abcdefghijklmnop python3 slack_message_exporter.py $CHANNEL_ID output.txt
```

出力されるテキストファイルの例は以下。
ユーザー名, タイムスタンプ (JST), スレッドも表示される。
スレッドはインデントにより表現される。

```txt
kangetsu121 2021-11-28 21:50:06.000200+09:00
<@kangetsu121>さんがチャンネルに参加しました


kangetsu121 2022-03-04 21:05:01.454799+09:00
parent 1

        kangetsu121 2022-03-04 21:05:14.045859+09:00
        child 1

        kangetsu121 2022-03-05 00:32:38.353319+09:00
        child 1-2


kangetsu121 2022-03-04 21:05:04.372529+09:00
parent2


kangetsu121 2022-03-04 21:05:06.566659+09:00
parent3

        kangetsu121 2022-03-04 21:05:24.378519+09:00
        child 3
```

### Note

- 出力ファイルの改行コードは LF
- 添付したファイルなどは対象外
