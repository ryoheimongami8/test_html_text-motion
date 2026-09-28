# ビーンズ！ 15秒CM

Canvas 2D + Web Audio で作った、128BPM・15秒のモーショングラフィックスCM。動画ファイルではなく、
1本の HTML がその場で毎フレーム描画し、音楽もその場で合成している。

## 見る

- **GitHub Pages（何もインストールせず見るだけ）**: このリポジトリを Pages で公開しているURLを開くだけ
- **ローカルで編集しながら**: `serve.bat`（Windows）を実行するか `python serve.py` を実行してから、表示されるURLを開く
  - `index.html` を `file://` で直接開くと、MP4書き出しができない（ブラウザのセキュリティ制限）ので、必ずどちらかのサーバー経由で開くこと

## 編集する

画面右上の「✎ 編集」ボタンから、テキスト・色・キャラクター画像・動画を差し替えられる。

- `serve.py` 経由で開いている場合: 変更は自動的に `config.json` / `assets/` に保存され、次回開いたときも反映される
- サーバーなし（GitHub Pages など静的ホスティング）で開いている場合: その場のプレビューと MP4 書き出しには使えるが、変更は保存されない（リロードすると元に戻る）

コードを直接いじりたい場合は `config.json`（テキスト・色・タイミング・素材ファイル名）と `assets/`（画像・動画）を見ればよい。`index.html` 本体は描画エンジンだけで、値は埋め込んでいない。

## 構成

```
index.html       描画エンジン（Canvas + Web Audio + WebCodecs書き出し）
config.json      編集可能なパラメータ（テキスト・色・BPM・素材パス）
assets/          差し替え可能な画像・動画
  goblins_alpha.webm   背景を透過処理した集合動画
  sheet_alpha.png      背景を透過処理した集合絵
  char_1〜5.png        個別に切り抜いたキャラクター
key.py           Wan動画の背景を透過処理するスクリプト（assets/goblins_alpha.webm を再生成）
key_sheet.py     キャラクターシートから個別画像を切り抜くスクリプト（assets/ に出力）
serve.py / .bat  ローカルサーバー（保存・アップロード機能つき）
```

## MP4として書き出す

「● MP4書き出し」ボタンでブラウザ内で30fps・H.264+AACのMP4にレンダリングする（WebCodecs使用、Chrome/Edge推奨）。
`serve.py` 経由なら `out/` に保存、それ以外（GitHub Pagesなど）ならブラウザのダウンロードとして保存される。
