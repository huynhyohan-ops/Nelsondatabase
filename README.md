# 📁 Project Structure

```
App/
├── .streamlit/
│   ├── config.toml
├── DATA/
│   ├── Data.xlsx
│   ├── Shipments.xlsx
│   ├── convert_data_to_shipments.py
│   ├── debug_columns.py
├── RAW/
├── common/
│   ├── __init__.py
│   ├── cost_engine.py
│   ├── data_loader.py
│   ├── generator.py
│   ├── helpers.py
│   ├── kpi_calculator.py
│   ├── models.py
│   ├── plot_utils.py
│   ├── schedule_engine.py
│   ├── shipment_analyzer.py
│   ├── style.py
├── e2e/
│   ├── node_modules/
│   │   ├── .bin/
│   │   │   ├── playwright
│   │   │   ├── playwright-core
│   │   │   ├── playwright-core.cmd
│   │   │   ├── playwright-core.ps1
│   │   │   ├── playwright.cmd
│   │   │   ├── playwright.ps1
│   │   ├── @playwright/
│   │   │   ├── test/
│   │   │   │   ├── LICENSE
│   │   │   │   ├── NOTICE
│   │   │   │   ├── README.md
│   │   │   │   ├── cli.js
│   │   │   │   ├── index.d.ts
│   │   │   │   ├── index.js
│   │   │   │   ├── index.mjs
│   │   │   │   ├── package.json
│   │   │   │   ├── reporter.d.ts
│   │   │   │   ├── reporter.js
│   │   │   │   ├── reporter.mjs
│   │   ├── playwright/
│   │   │   ├── lib/
│   │   │   │   ├── agents/
│   │   │   │   │   ├── copilot-setup-steps.yml
│   │   │   │   │   ├── generateAgents.js
│   │   │   │   │   ├── playwright-test-coverage.prompt.md
│   │   │   │   │   ├── playwright-test-generate.prompt.md
│   │   │   │   │   ├── playwright-test-generator.agent.md
│   │   │   │   │   ├── playwright-test-heal.prompt.md
│   │   │   │   │   ├── playwright-test-healer.agent.md
│   │   │   │   │   ├── playwright-test-plan.prompt.md
│   │   │   │   │   ├── playwright-test-planner.agent.md
│   │   │   │   ├── common/
│   │   │   │   │   ├── config.js
│   │   │   │   │   ├── configLoader.js
│   │   │   │   │   ├── esmLoaderHost.js
│   │   │   │   │   ├── expectBundle.js
│   │   │   │   │   ├── expectBundleImpl.js
│   │   │   │   │   ├── fixtures.js
│   │   │   │   │   ├── globals.js
│   │   │   │   │   ├── ipc.js
│   │   │   │   │   ├── poolBuilder.js
│   │   │   │   │   ├── process.js
│   │   │   │   │   ├── suiteUtils.js
│   │   │   │   │   ├── test.js
│   │   │   │   │   ├── testLoader.js
│   │   │   │   │   ├── testType.js
│   │   │   │   │   ├── validators.js
│   │   │   │   ├── isomorphic/
│   │   │   │   │   ├── events.js
│   │   │   │   │   ├── folders.js
│   │   │   │   │   ├── stringInternPool.js
│   │   │   │   │   ├── teleReceiver.js
│   │   │   │   │   ├── teleSuiteUpdater.js
│   │   │   │   │   ├── testServerConnection.js
│   │   │   │   │   ├── testServerInterface.js
│   │   │   │   │   ├── testTree.js
│   │   │   │   │   ├── types.d.js
│   │   │   │   ├── loader/
│   │   │   │   │   ├── loaderMain.js
│   │   │   │   ├── matchers/
│   │   │   │   │   ├── expect.js
│   │   │   │   │   ├── matcherHint.js
│   │   │   │   │   ├── matchers.js
│   │   │   │   │   ├── toBeTruthy.js
│   │   │   │   │   ├── toEqual.js
│   │   │   │   │   ├── toHaveURL.js
│   │   │   │   │   ├── toMatchAriaSnapshot.js
│   │   │   │   │   ├── toMatchSnapshot.js
│   │   │   │   │   ├── toMatchText.js
│   │   │   │   ├── mcp/
│   │   │   │   │   ├── browser/
│   │   │   │   │   │   ├── tools/
│   │   │   │   │   │   │   ├── common.js
│   │   │   │   │   │   │   ├── console.js
│   │   │   │   │   │   │   ├── dialogs.js
│   │   │   │   │   │   │   ├── evaluate.js
│   │   │   │   │   │   │   ├── files.js
│   │   │   │   │   │   │   ├── form.js
│   │   │   │   │   │   │   ├── install.js
│   │   │   │   │   │   │   ├── keyboard.js
│   │   │   │   │   │   │   ├── mouse.js
│   │   │   │   │   │   │   ├── navigate.js
│   │   │   │   │   │   │   ├── network.js
│   │   │   │   │   │   │   ├── pdf.js
│   │   │   │   │   │   │   ├── runCode.js
│   │   │   │   │   │   │   ├── screenshot.js
│   │   │   │   │   │   │   ├── snapshot.js
│   │   │   │   │   │   │   ├── tabs.js
│   │   │   │   │   │   │   ├── tool.js
│   │   │   │   │   │   │   ├── tracing.js
│   │   │   │   │   │   │   ├── utils.js
│   │   │   │   │   │   │   ├── verify.js
│   │   │   │   │   │   │   ├── wait.js
│   │   │   │   │   │   ├── actions.d.js
│   │   │   │   │   │   ├── browserContextFactory.js
│   │   │   │   │   │   ├── browserServerBackend.js
│   │   │   │   │   │   ├── codegen.js
│   │   │   │   │   │   ├── config.js
│   │   │   │   │   │   ├── context.js
│   │   │   │   │   │   ├── response.js
│   │   │   │   │   │   ├── sessionLog.js
│   │   │   │   │   │   ├── tab.js
│   │   │   │   │   │   ├── tools.js
│   │   │   │   │   │   ├── watchdog.js
│   │   │   │   │   ├── extension/
│   │   │   │   │   │   ├── cdpRelay.js
│   │   │   │   │   │   ├── extensionContextFactory.js
│   │   │   │   │   │   ├── protocol.js
│   │   │   │   │   ├── sdk/
│   │   │   │   │   │   ├── bundle.js
│   │   │   │   │   │   ├── exports.js
│   │   │   │   │   │   ├── http.js
│   │   │   │   │   │   ├── inProcessTransport.js
│   │   │   │   │   │   ├── proxyBackend.js
│   │   │   │   │   │   ├── server.js
│   │   │   │   │   │   ├── tool.js
│   │   │   │   │   ├── test/
│   │   │   │   │   │   ├── browserBackend.js
│   │   │   │   │   │   ├── generatorTools.js
│   │   │   │   │   │   ├── plannerTools.js
│   │   │   │   │   │   ├── seed.js
│   │   │   │   │   │   ├── streams.js
│   │   │   │   │   │   ├── testBackend.js
│   │   │   │   │   │   ├── testContext.js
│   │   │   │   │   │   ├── testTool.js
│   │   │   │   │   │   ├── testTools.js
│   │   │   │   │   ├── config.d.js
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── log.js
│   │   │   │   │   ├── program.js
│   │   │   │   ├── plugins/
│   │   │   │   │   ├── gitCommitInfoPlugin.js
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── webServerPlugin.js
│   │   │   │   ├── reporters/
│   │   │   │   │   ├── versions/
│   │   │   │   │   │   ├── blobV1.js
│   │   │   │   │   ├── base.js
│   │   │   │   │   ├── blob.js
│   │   │   │   │   ├── dot.js
│   │   │   │   │   ├── empty.js
│   │   │   │   │   ├── github.js
│   │   │   │   │   ├── html.js
│   │   │   │   │   ├── internalReporter.js
│   │   │   │   │   ├── json.js
│   │   │   │   │   ├── junit.js
│   │   │   │   │   ├── line.js
│   │   │   │   │   ├── list.js
│   │   │   │   │   ├── listModeReporter.js
│   │   │   │   │   ├── markdown.js
│   │   │   │   │   ├── merge.js
│   │   │   │   │   ├── multiplexer.js
│   │   │   │   │   ├── reporterV2.js
│   │   │   │   │   ├── teleEmitter.js
│   │   │   │   ├── runner/
│   │   │   │   │   ├── dispatcher.js
│   │   │   │   │   ├── failureTracker.js
│   │   │   │   │   ├── lastRun.js
│   │   │   │   │   ├── loadUtils.js
│   │   │   │   │   ├── loaderHost.js
│   │   │   │   │   ├── processHost.js
│   │   │   │   │   ├── projectUtils.js
│   │   │   │   │   ├── rebase.js
│   │   │   │   │   ├── reporters.js
│   │   │   │   │   ├── sigIntWatcher.js
│   │   │   │   │   ├── taskRunner.js
│   │   │   │   │   ├── tasks.js
│   │   │   │   │   ├── testGroups.js
│   │   │   │   │   ├── testRunner.js
│   │   │   │   │   ├── testServer.js
│   │   │   │   │   ├── uiModeReporter.js
│   │   │   │   │   ├── vcs.js
│   │   │   │   │   ├── watchMode.js
│   │   │   │   │   ├── workerHost.js
│   │   │   │   ├── third_party/
│   │   │   │   │   ├── pirates.js
│   │   │   │   │   ├── tsconfig-loader.js
│   │   │   │   ├── transform/
│   │   │   │   │   ├── babelBundle.js
│   │   │   │   │   ├── babelBundleImpl.js
│   │   │   │   │   ├── compilationCache.js
│   │   │   │   │   ├── esmLoader.js
│   │   │   │   │   ├── portTransport.js
│   │   │   │   │   ├── transform.js
│   │   │   │   ├── worker/
│   │   │   │   │   ├── fixtureRunner.js
│   │   │   │   │   ├── testInfo.js
│   │   │   │   │   ├── testTracing.js
│   │   │   │   │   ├── timeoutManager.js
│   │   │   │   │   ├── util.js
│   │   │   │   │   ├── workerMain.js
│   │   │   │   ├── fsWatcher.js
│   │   │   │   ├── index.js
│   │   │   │   ├── internalsForTest.js
│   │   │   │   ├── mcpBundleImpl.js
│   │   │   │   ├── program.js
│   │   │   │   ├── util.js
│   │   │   │   ├── utilsBundle.js
│   │   │   │   ├── utilsBundleImpl.js
│   │   │   ├── types/
│   │   │   │   ├── test.d.ts
│   │   │   │   ├── testReporter.d.ts
│   │   │   ├── LICENSE
│   │   │   ├── NOTICE
│   │   │   ├── README.md
│   │   │   ├── ThirdPartyNotices.txt
│   │   │   ├── cli.js
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── index.mjs
│   │   │   ├── jsx-runtime.js
│   │   │   ├── jsx-runtime.mjs
│   │   │   ├── package.json
│   │   │   ├── test.d.ts
│   │   │   ├── test.js
│   │   │   ├── test.mjs
│   │   ├── playwright-core/
│   │   │   ├── bin/
│   │   │   │   ├── install_media_pack.ps1
│   │   │   │   ├── install_webkit_wsl.ps1
│   │   │   │   ├── reinstall_chrome_beta_linux.sh
│   │   │   │   ├── reinstall_chrome_beta_mac.sh
│   │   │   │   ├── reinstall_chrome_beta_win.ps1
│   │   │   │   ├── reinstall_chrome_stable_linux.sh
│   │   │   │   ├── reinstall_chrome_stable_mac.sh
│   │   │   │   ├── reinstall_chrome_stable_win.ps1
│   │   │   │   ├── reinstall_msedge_beta_linux.sh
│   │   │   │   ├── reinstall_msedge_beta_mac.sh
│   │   │   │   ├── reinstall_msedge_beta_win.ps1
│   │   │   │   ├── reinstall_msedge_dev_linux.sh
│   │   │   │   ├── reinstall_msedge_dev_mac.sh
│   │   │   │   ├── reinstall_msedge_dev_win.ps1
│   │   │   │   ├── reinstall_msedge_stable_linux.sh
│   │   │   │   ├── reinstall_msedge_stable_mac.sh
│   │   │   │   ├── reinstall_msedge_stable_win.ps1
│   │   │   ├── lib/
│   │   │   │   ├── cli/
│   │   │   │   │   ├── driver.js
│   │   │   │   │   ├── program.js
│   │   │   │   │   ├── programWithTestStub.js
│   │   │   │   ├── client/
│   │   │   │   │   ├── android.js
│   │   │   │   │   ├── api.js
│   │   │   │   │   ├── artifact.js
│   │   │   │   │   ├── browser.js
│   │   │   │   │   ├── browserContext.js
│   │   │   │   │   ├── browserType.js
│   │   │   │   │   ├── cdpSession.js
│   │   │   │   │   ├── channelOwner.js
│   │   │   │   │   ├── clientHelper.js
│   │   │   │   │   ├── clientInstrumentation.js
│   │   │   │   │   ├── clientStackTrace.js
│   │   │   │   │   ├── clock.js
│   │   │   │   │   ├── connection.js
│   │   │   │   │   ├── consoleMessage.js
│   │   │   │   │   ├── coverage.js
│   │   │   │   │   ├── dialog.js
│   │   │   │   │   ├── download.js
│   │   │   │   │   ├── electron.js
│   │   │   │   │   ├── elementHandle.js
│   │   │   │   │   ├── errors.js
│   │   │   │   │   ├── eventEmitter.js
│   │   │   │   │   ├── events.js
│   │   │   │   │   ├── fetch.js
│   │   │   │   │   ├── fileChooser.js
│   │   │   │   │   ├── fileUtils.js
│   │   │   │   │   ├── frame.js
│   │   │   │   │   ├── harRouter.js
│   │   │   │   │   ├── input.js
│   │   │   │   │   ├── jsHandle.js
│   │   │   │   │   ├── jsonPipe.js
│   │   │   │   │   ├── localUtils.js
│   │   │   │   │   ├── locator.js
│   │   │   │   │   ├── network.js
│   │   │   │   │   ├── page.js
│   │   │   │   │   ├── platform.js
│   │   │   │   │   ├── playwright.js
│   │   │   │   │   ├── selectors.js
│   │   │   │   │   ├── stream.js
│   │   │   │   │   ├── timeoutSettings.js
│   │   │   │   │   ├── tracing.js
│   │   │   │   │   ├── types.js
│   │   │   │   │   ├── video.js
│   │   │   │   │   ├── waiter.js
│   │   │   │   │   ├── webError.js
│   │   │   │   │   ├── webSocket.js
│   │   │   │   │   ├── worker.js
│   │   │   │   │   ├── writableStream.js
│   │   │   │   ├── generated/
│   │   │   │   │   ├── bindingsControllerSource.js
│   │   │   │   │   ├── clockSource.js
│   │   │   │   │   ├── injectedScriptSource.js
│   │   │   │   │   ├── pollingRecorderSource.js
│   │   │   │   │   ├── storageScriptSource.js
│   │   │   │   │   ├── utilityScriptSource.js
│   │   │   │   │   ├── webSocketMockSource.js
│   │   │   │   ├── protocol/
│   │   │   │   │   ├── serializers.js
│   │   │   │   │   ├── validator.js
│   │   │   │   │   ├── validatorPrimitives.js
│   │   │   │   ├── remote/
│   │   │   │   │   ├── playwrightConnection.js
│   │   │   │   │   ├── playwrightServer.js
│   │   │   │   ├── server/
│   │   │   │   │   ├── android/
│   │   │   │   │   │   ├── android.js
│   │   │   │   │   │   ├── backendAdb.js
│   │   │   │   │   ├── bidi/
│   │   │   │   │   │   ├── third_party/
│   │   │   │   │   │   │   ├── bidiCommands.d.js
│   │   │   │   │   │   │   ├── bidiDeserializer.js
│   │   │   │   │   │   │   ├── bidiKeyboard.js
│   │   │   │   │   │   │   ├── bidiProtocol.js
│   │   │   │   │   │   │   ├── bidiProtocolCore.js
│   │   │   │   │   │   │   ├── bidiProtocolPermissions.js
│   │   │   │   │   │   │   ├── bidiSerializer.js
│   │   │   │   │   │   │   ├── firefoxPrefs.js
│   │   │   │   │   │   ├── bidiBrowser.js
│   │   │   │   │   │   ├── bidiChromium.js
│   │   │   │   │   │   ├── bidiConnection.js
│   │   │   │   │   │   ├── bidiExecutionContext.js
│   │   │   │   │   │   ├── bidiFirefox.js
│   │   │   │   │   │   ├── bidiInput.js
│   │   │   │   │   │   ├── bidiNetworkManager.js
│   │   │   │   │   │   ├── bidiOverCdp.js
│   │   │   │   │   │   ├── bidiPage.js
│   │   │   │   │   │   ├── bidiPdf.js
│   │   │   │   │   ├── chromium/
│   │   │   │   │   │   ├── appIcon.png
│   │   │   │   │   │   ├── chromium.js
│   │   │   │   │   │   ├── chromiumSwitches.js
│   │   │   │   │   │   ├── crBrowser.js
│   │   │   │   │   │   ├── crConnection.js
│   │   │   │   │   │   ├── crCoverage.js
│   │   │   │   │   │   ├── crDevTools.js
│   │   │   │   │   │   ├── crDragDrop.js
│   │   │   │   │   │   ├── crExecutionContext.js
│   │   │   │   │   │   ├── crInput.js
│   │   │   │   │   │   ├── crNetworkManager.js
│   │   │   │   │   │   ├── crPage.js
│   │   │   │   │   │   ├── crPdf.js
│   │   │   │   │   │   ├── crProtocolHelper.js
│   │   │   │   │   │   ├── crServiceWorker.js
│   │   │   │   │   │   ├── defaultFontFamilies.js
│   │   │   │   │   │   ├── protocol.d.js
│   │   │   │   │   │   ├── videoRecorder.js
│   │   │   │   │   ├── codegen/
│   │   │   │   │   │   ├── csharp.js
│   │   │   │   │   │   ├── java.js
│   │   │   │   │   │   ├── javascript.js
│   │   │   │   │   │   ├── jsonl.js
│   │   │   │   │   │   ├── language.js
│   │   │   │   │   │   ├── languages.js
│   │   │   │   │   │   ├── python.js
│   │   │   │   │   │   ├── types.js
│   │   │   │   │   ├── dispatchers/
│   │   │   │   │   │   ├── androidDispatcher.js
│   │   │   │   │   │   ├── artifactDispatcher.js
│   │   │   │   │   │   ├── browserContextDispatcher.js
│   │   │   │   │   │   ├── browserDispatcher.js
│   │   │   │   │   │   ├── browserTypeDispatcher.js
│   │   │   │   │   │   ├── cdpSessionDispatcher.js
│   │   │   │   │   │   ├── debugControllerDispatcher.js
│   │   │   │   │   │   ├── dialogDispatcher.js
│   │   │   │   │   │   ├── dispatcher.js
│   │   │   │   │   │   ├── electronDispatcher.js
│   │   │   │   │   │   ├── elementHandlerDispatcher.js
│   │   │   │   │   │   ├── frameDispatcher.js
│   │   │   │   │   │   ├── jsHandleDispatcher.js
│   │   │   │   │   │   ├── jsonPipeDispatcher.js
│   │   │   │   │   │   ├── localUtilsDispatcher.js
│   │   │   │   │   │   ├── networkDispatchers.js
│   │   │   │   │   │   ├── pageDispatcher.js
│   │   │   │   │   │   ├── playwrightDispatcher.js
│   │   │   │   │   │   ├── streamDispatcher.js
│   │   │   │   │   │   ├── tracingDispatcher.js
│   │   │   │   │   │   ├── webSocketRouteDispatcher.js
│   │   │   │   │   │   ├── writableStreamDispatcher.js
│   │   │   │   │   ├── electron/
│   │   │   │   │   │   ├── electron.js
│   │   │   │   │   │   ├── loader.js
│   │   │   │   │   ├── firefox/
│   │   │   │   │   │   ├── ffBrowser.js
│   │   │   │   │   │   ├── ffConnection.js
│   │   │   │   │   │   ├── ffExecutionContext.js
│   │   │   │   │   │   ├── ffInput.js
│   │   │   │   │   │   ├── ffNetworkManager.js
│   │   │   │   │   │   ├── ffPage.js
│   │   │   │   │   │   ├── firefox.js
│   │   │   │   │   │   ├── protocol.d.js
│   │   │   │   │   ├── har/
│   │   │   │   │   │   ├── harRecorder.js
│   │   │   │   │   │   ├── harTracer.js
│   │   │   │   │   ├── recorder/
│   │   │   │   │   │   ├── chat.js
│   │   │   │   │   │   ├── recorderApp.js
│   │   │   │   │   │   ├── recorderRunner.js
│   │   │   │   │   │   ├── recorderSignalProcessor.js
│   │   │   │   │   │   ├── recorderUtils.js
│   │   │   │   │   │   ├── throttledFile.js
│   │   │   │   │   ├── registry/
│   │   │   │   │   │   ├── browserFetcher.js
│   │   │   │   │   │   ├── dependencies.js
│   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   ├── nativeDeps.js
│   │   │   │   │   │   ├── oopDownloadBrowserMain.js
│   │   │   │   │   ├── trace/
│   │   │   │   │   │   ├── recorder/
│   │   │   │   │   │   │   ├── snapshotter.js
│   │   │   │   │   │   │   ├── snapshotterInjected.js
│   │   │   │   │   │   │   ├── tracing.js
│   │   │   │   │   │   ├── test/
│   │   │   │   │   │   │   ├── inMemorySnapshotter.js
│   │   │   │   │   │   ├── viewer/
│   │   │   │   │   │   │   ├── traceViewer.js
│   │   │   │   │   ├── utils/
│   │   │   │   │   │   ├── image_tools/
│   │   │   │   │   │   │   ├── colorUtils.js
│   │   │   │   │   │   │   ├── compare.js
│   │   │   │   │   │   │   ├── imageChannel.js
│   │   │   │   │   │   │   ├── stats.js
│   │   │   │   │   │   ├── ascii.js
│   │   │   │   │   │   ├── comparators.js
│   │   │   │   │   │   ├── crypto.js
│   │   │   │   │   │   ├── debug.js
│   │   │   │   │   │   ├── debugLogger.js
│   │   │   │   │   │   ├── env.js
│   │   │   │   │   │   ├── eventsHelper.js
│   │   │   │   │   │   ├── expectUtils.js
│   │   │   │   │   │   ├── fileUtils.js
│   │   │   │   │   │   ├── happyEyeballs.js
│   │   │   │   │   │   ├── hostPlatform.js
│   │   │   │   │   │   ├── httpServer.js
│   │   │   │   │   │   ├── imageUtils.js
│   │   │   │   │   │   ├── linuxUtils.js
│   │   │   │   │   │   ├── network.js
│   │   │   │   │   │   ├── nodePlatform.js
│   │   │   │   │   │   ├── pipeTransport.js
│   │   │   │   │   │   ├── processLauncher.js
│   │   │   │   │   │   ├── profiler.js
│   │   │   │   │   │   ├── socksProxy.js
│   │   │   │   │   │   ├── spawnAsync.js
│   │   │   │   │   │   ├── task.js
│   │   │   │   │   │   ├── userAgent.js
│   │   │   │   │   │   ├── wsServer.js
│   │   │   │   │   │   ├── zipFile.js
│   │   │   │   │   │   ├── zones.js
│   │   │   │   │   ├── webkit/
│   │   │   │   │   │   ├── protocol.d.js
│   │   │   │   │   │   ├── webkit.js
│   │   │   │   │   │   ├── wkBrowser.js
│   │   │   │   │   │   ├── wkConnection.js
│   │   │   │   │   │   ├── wkExecutionContext.js
│   │   │   │   │   │   ├── wkInput.js
│   │   │   │   │   │   ├── wkInterceptableRequest.js
│   │   │   │   │   │   ├── wkPage.js
│   │   │   │   │   │   ├── wkProvisionalPage.js
│   │   │   │   │   │   ├── wkWorkers.js
│   │   │   │   │   ├── artifact.js
│   │   │   │   │   ├── browser.js
│   │   │   │   │   ├── browserContext.js
│   │   │   │   │   ├── browserType.js
│   │   │   │   │   ├── callLog.js
│   │   │   │   │   ├── clock.js
│   │   │   │   │   ├── console.js
│   │   │   │   │   ├── cookieStore.js
│   │   │   │   │   ├── debugController.js
│   │   │   │   │   ├── debugger.js
│   │   │   │   │   ├── deviceDescriptors.js
│   │   │   │   │   ├── deviceDescriptorsSource.json
│   │   │   │   │   ├── dialog.js
│   │   │   │   │   ├── dom.js
│   │   │   │   │   ├── download.js
│   │   │   │   │   ├── errors.js
│   │   │   │   │   ├── fetch.js
│   │   │   │   │   ├── fileChooser.js
│   │   │   │   │   ├── fileUploadUtils.js
│   │   │   │   │   ├── formData.js
│   │   │   │   │   ├── frameSelectors.js
│   │   │   │   │   ├── frames.js
│   │   │   │   │   ├── harBackend.js
│   │   │   │   │   ├── helper.js
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── input.js
│   │   │   │   │   ├── instrumentation.js
│   │   │   │   │   ├── javascript.js
│   │   │   │   │   ├── launchApp.js
│   │   │   │   │   ├── localUtils.js
│   │   │   │   │   ├── macEditingCommands.js
│   │   │   │   │   ├── network.js
│   │   │   │   │   ├── page.js
│   │   │   │   │   ├── pipeTransport.js
│   │   │   │   │   ├── playwright.js
│   │   │   │   │   ├── progress.js
│   │   │   │   │   ├── protocolError.js
│   │   │   │   │   ├── recorder.js
│   │   │   │   │   ├── screenshotter.js
│   │   │   │   │   ├── selectors.js
│   │   │   │   │   ├── socksClientCertificatesInterceptor.js
│   │   │   │   │   ├── socksInterceptor.js
│   │   │   │   │   ├── transport.js
│   │   │   │   │   ├── types.js
│   │   │   │   │   ├── usKeyboardLayout.js
│   │   │   │   ├── third_party/
│   │   │   │   │   ├── pixelmatch.js
│   │   │   │   ├── utils/
│   │   │   │   │   ├── isomorphic/
│   │   │   │   │   │   ├── ariaSnapshot.js
│   │   │   │   │   │   ├── assert.js
│   │   │   │   │   │   ├── colors.js
│   │   │   │   │   │   ├── cssParser.js
│   │   │   │   │   │   ├── cssTokenizer.js
│   │   │   │   │   │   ├── headers.js
│   │   │   │   │   │   ├── locatorGenerators.js
│   │   │   │   │   │   ├── locatorParser.js
│   │   │   │   │   │   ├── locatorUtils.js
│   │   │   │   │   │   ├── manualPromise.js
│   │   │   │   │   │   ├── mimeType.js
│   │   │   │   │   │   ├── multimap.js
│   │   │   │   │   │   ├── protocolFormatter.js
│   │   │   │   │   │   ├── protocolMetainfo.js
│   │   │   │   │   │   ├── rtti.js
│   │   │   │   │   │   ├── selectorParser.js
│   │   │   │   │   │   ├── semaphore.js
│   │   │   │   │   │   ├── stackTrace.js
│   │   │   │   │   │   ├── stringUtils.js
│   │   │   │   │   │   ├── time.js
│   │   │   │   │   │   ├── timeoutRunner.js
│   │   │   │   │   │   ├── traceUtils.js
│   │   │   │   │   │   ├── types.js
│   │   │   │   │   │   ├── urlMatch.js
│   │   │   │   │   │   ├── utilityScriptSerializers.js
│   │   │   │   ├── utilsBundleImpl/
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── xdg-open
│   │   │   │   ├── vite/
│   │   │   │   │   ├── htmlReport/
│   │   │   │   │   │   ├── index.html
│   │   │   │   │   ├── recorder/
│   │   │   │   │   │   ├── assets/
│   │   │   │   │   │   │   ├── codeMirrorModule-BoWUGj0J.js
│   │   │   │   │   │   │   ├── codeMirrorModule-C3UTv-Ge.css
│   │   │   │   │   │   │   ├── codicon-DCmgc-ay.ttf
│   │   │   │   │   │   │   ├── index-DJqDAOZp.js
│   │   │   │   │   │   │   ├── index-Ri0uHF7I.css
│   │   │   │   │   │   ├── index.html
│   │   │   │   │   │   ├── playwright-logo.svg
│   │   │   │   │   ├── traceViewer/
│   │   │   │   │   │   ├── assets/
│   │   │   │   │   │   │   ├── codeMirrorModule-Bucv2d7q.js
│   │   │   │   │   │   │   ├── defaultSettingsView-BEpdCv1S.js
│   │   │   │   │   │   │   ├── xtermModule-CsJ4vdCR.js
│   │   │   │   │   │   ├── codeMirrorModule.C3UTv-Ge.css
│   │   │   │   │   │   ├── codicon.DCmgc-ay.ttf
│   │   │   │   │   │   ├── defaultSettingsView.ConWv5KN.css
│   │   │   │   │   │   ├── index.BxQ34UMZ.js
│   │   │   │   │   │   ├── index.C4Y3Aw8n.css
│   │   │   │   │   │   ├── index.html
│   │   │   │   │   │   ├── manifest.webmanifest
│   │   │   │   │   │   ├── playwright-logo.svg
│   │   │   │   │   │   ├── snapshot.html
│   │   │   │   │   │   ├── sw.bundle.js
│   │   │   │   │   │   ├── uiMode.BWTwXl41.js
│   │   │   │   │   │   ├── uiMode.Btcz36p_.css
│   │   │   │   │   │   ├── uiMode.html
│   │   │   │   │   │   ├── xtermModule.DYP7pi_n.css
│   │   │   │   ├── androidServerImpl.js
│   │   │   │   ├── browserServerImpl.js
│   │   │   │   ├── inProcessFactory.js
│   │   │   │   ├── inprocess.js
│   │   │   │   ├── outofprocess.js
│   │   │   │   ├── utils.js
│   │   │   │   ├── utilsBundle.js
│   │   │   │   ├── zipBundle.js
│   │   │   │   ├── zipBundleImpl.js
│   │   │   ├── types/
│   │   │   │   ├── protocol.d.ts
│   │   │   │   ├── structs.d.ts
│   │   │   │   ├── types.d.ts
│   │   │   ├── LICENSE
│   │   │   ├── NOTICE
│   │   │   ├── README.md
│   │   │   ├── ThirdPartyNotices.txt
│   │   │   ├── browsers.json
│   │   │   ├── cli.js
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── index.mjs
│   │   │   ├── package.json
│   │   ├── .package-lock.json
│   ├── playwright-report/
│   │   ├── data/
│   │   │   ├── 148cf44fe6d811e2b43279f4caf70a0160e26087.zip
│   │   │   ├── 2f7bb605aedf2d7aa52d19aacc5766544b6a3ad3.webm
│   │   │   ├── 2f86f1e1419a5d5cce396009eee74b0cab6e8160.webm
│   │   │   ├── 32abab4f4fc0a0dfdcc22f1f0523f3980f1d7761.zip
│   │   │   ├── 39c6a3a78ea2e5c4623037445a4c1caa5e0984fd.webm
│   │   │   ├── 552c8a88ec36856e1ec1700d371da1fd0319ce00.webm
│   │   │   ├── 6c32b447d4a614b8d83cd3903c66958c102ceee8.webm
│   │   │   ├── 6db672299cded53631a8dfb83cadab4fc640b797.png
│   │   │   ├── 71b8afbb5e87f68b2835c4cb23c2f5bd2ac9e04d.md
│   │   │   ├── 730846d18304ee84ded89420ef141f5fe6425307.zip
│   │   │   ├── 761c81454e2621fe10997a6c133d0bd76b98ab9f.webm
│   │   │   ├── 7a476537c44ae564bb50836eff95598ba3365dce.webm
│   │   │   ├── 819790ffebf249e814e3d0de60ef4a75141fe715.zip
│   │   │   ├── 83e057ef7da38c4a767ec79e69375e56a0791df0.webm
│   │   │   ├── a8ada7a43557b932de3882c1db585d516e526d9f.webm
│   │   │   ├── d7cb7101abf73543cb2717efbd04a9fef7c5bcb0.zip
│   │   │   ├── d94a9be55696ae4d3006255965ba7d313b1129fb.webm
│   │   ├── trace/
│   │   │   ├── assets/
│   │   │   │   ├── codeMirrorModule-Bucv2d7q.js
│   │   │   │   ├── defaultSettingsView-BEpdCv1S.js
│   │   │   ├── codeMirrorModule.C3UTv-Ge.css
│   │   │   ├── codicon.DCmgc-ay.ttf
│   │   │   ├── defaultSettingsView.ConWv5KN.css
│   │   │   ├── index.BxQ34UMZ.js
│   │   │   ├── index.C4Y3Aw8n.css
│   │   │   ├── index.html
│   │   │   ├── manifest.webmanifest
│   │   │   ├── playwright-logo.svg
│   │   │   ├── snapshot.html
│   │   │   ├── sw.bundle.js
│   │   │   ├── uiMode.BWTwXl41.js
│   │   │   ├── uiMode.Btcz36p_.css
│   │   │   ├── uiMode.html
│   │   │   ├── xtermModule.DYP7pi_n.css
│   │   ├── index.html
│   │   ├── junit.xml
│   │   ├── report.json
│   ├── test-results/
│   │   ├── test_ux-TC2-dynamic-custom-89ca6--updates-with-Customer-Type/
│   │   │   ├── error-context.md
│   │   │   ├── test-failed-1.png
│   │   │   ├── video.webm
│   │   ├── test_ux-TC2-dynamic-custom-89ca6--updates-with-Customer-Type-retry1/
│   │   │   ├── trace.zip
│   │   │   ├── video.webm
│   │   ├── test_ux-TC3-toggle-report-preserves-state/
│   │   │   ├── video.webm
│   │   ├── test_ux-TC3-toggle-report-preserves-state-retry1/
│   │   │   ├── trace.zip
│   │   │   ├── video.webm
│   │   ├── test_ux-TC4-metric-affects-dual-line/
│   │   │   ├── video.webm
│   │   ├── test_ux-TC4-metric-affects-dual-line-retry1/
│   │   │   ├── trace.zip
│   │   │   ├── video.webm
│   │   ├── test_ux-TC5-tolerance-updates-OTD-and-delayed-table/
│   │   │   ├── video.webm
│   │   ├── test_ux-TC5-tolerance-updates-OTD-and-delayed-table-retry1/
│   │   │   ├── trace.zip
│   │   │   ├── video.webm
│   │   ├── test_ux-TC6-rapid-changes--6ea02--and-final-state-is-correct/
│   │   │   ├── video.webm
│   │   ├── test_ux-TC6-rapid-changes--6ea02--and-final-state-is-correct-retry1/
│   │   │   ├── trace.zip
│   │   │   ├── video.webm
│   │   ├── .last-run.json
│   ├── tools/
│   │   ├── summarize.js
│   ├── global-setup.js
│   ├── package-lock.json
│   ├── package.json
│   ├── playwright.config.js
│   ├── test_ux.spec.ts
├── pages/
│   ├── luu tru/
│   │   ├── cost_engine.py
│   │   ├── pricing_quote_page - Copy - Copy - Copy.py
│   │   ├── pricing_quote_page.py
│   │   ├── shipment_dashboard_page.py
│   ├── __init__.py
│   ├── customers_crm_page.py
│   ├── customers_hub_page.py
│   ├── normalize_pricing_work.py
│   ├── pricing_hub_page.py
│   ├── pricing_quote_page.py
│   ├── pricing_schedules_page.py
│   ├── pricing_upload_page.py
│   ├── shipment_dashboard_page.py
│   ├── shipment_follow_page.py
│   ├── shipment_hub_page.py
├── themes/
│   ├── Pricing_Quote_Light.css
│   ├── Pricing_Quote_Navy.css
│   ├── dark_themes.css
│   ├── dark_themesold.css
│   ├── follow_shipment_dark.css
│   ├── navy_themes.css
├── Pipeline Pricinghub.docx
├── app.py
├── generate_readme.py
├── generate_weekly_report.py
├── menu.py
├── test_smooth_ux.py
├── theme_loader.py
```
