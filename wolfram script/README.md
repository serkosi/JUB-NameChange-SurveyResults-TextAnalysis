# WolframScript in Wolfram Cloud

This folder runs the survey charts using WolframScript's cloud execution mode. It does not install a local Wolfram Engine. A WolframScript command-line client and Wolfram Cloud account are still required.

## Authenticate

Install or configure the WolframScript CLI client using Wolfram's official [WolframScript documentation](https://reference.wolfram.com/language/ref/program/wolframscript.html). Then authenticate from a terminal; the CLI prompts for your Wolfram ID and password:

```sh
wolframscript -cloud -auth
```

Do not put the password in a command, script, or repository file.

## Run

From any directory:

```sh
"wolfram script/run_cloud.sh"
```

The script base64-encodes the anonymized workbook and sends it as standard input to one Wolfram Cloud evaluation. The cloud imports the workbook from memory and returns a 12-page PDF with the survey charts. The workbook is not created as a persistent Wolfram Cloud file. Output defaults to `wolfram script/results/survey-analysis.pdf`; an optional first argument selects a different output path:

```sh
"wolfram script/run_cloud.sh" "$HOME/survey-analysis.pdf"
```

This uploads the survey workbook contents to Wolfram Cloud for computation. Run it only if you are comfortable processing this anonymized data in the Wolfram Cloud. The cloud script does not invoke `JavaGraphics``: it is designed for cloud/headless execution and returns regular Wolfram Language charts as a PDF, which can be opened locally.

## Troubleshooting

- If `wolframscript` is not found, install/configure the WolframScript client and ensure it is on `PATH`. The cloud kernel does not require the full local Wolfram Engine.
- If authentication fails, run `wolframscript -cloud -auth` interactively and accept any Wolfram Cloud terms in the browser or prompt.
- If the XLSX layout changes, the script requires the first worksheet to retain the survey's 13 columns in their existing order.
