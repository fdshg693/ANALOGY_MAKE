# Github Action からデプロイして、ページにアクセスした場合の警告

2026-04-03T06:58:57.660743513Z  Listening on http://[::]:8080
2026-04-03T06:58:59.319665278Z  [request error] [unhandled] [GET] http://169.254.129.3:8080/robots933456.txt
2026-04-03T06:58:59.319705729Z   Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
2026-04-03T06:58:59.319713504Z  Did you mean to import "file:///home/site/wwwroot/server/node_modules/unhead/node_modules/hookable"?
2026-04-03T06:58:59.319720388Z      at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
2026-04-03T06:58:59.319727192Z      ... 7 lines matching cause stack trace ...
2026-04-03T06:58:59.319733264Z      at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
2026-04-03T06:58:59.319740048Z    cause: Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
2026-04-03T06:58:59.319746691Z    Did you mean to import "file:///home/site/wwwroot/server/node_modules/unhead/node_modules/hookable"?
2026-04-03T06:58:59.319753134Z        at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
2026-04-03T06:58:59.319759026Z        at packageResolve (node:internal/modules/esm/resolve:767:81)
2026-04-03T06:58:59.319764877Z        at moduleResolve (node:internal/modules/esm/resolve:853:18)
2026-04-03T06:58:59.319770990Z        at defaultResolve (node:internal/modules/esm/resolve:983:11)
2026-04-03T06:58:59.319776851Z        at #cachedDefaultResolve (node:internal/modules/esm/loader:731:20)
2026-04-03T06:58:59.319782823Z        at ModuleLoader.resolve (node:internal/modules/esm/loader:708:38)
2026-04-03T06:58:59.319788755Z        at ModuleLoader.getModuleJobForImport (node:internal/modules/esm/loader:310:38)
2026-04-03T06:58:59.319795168Z        at ModuleJob._link (node:internal/modules/esm/module_job:182:49)
2026-04-03T06:58:59.319801340Z        at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
2026-04-03T06:58:59.319807212Z      code: 'ERR_MODULE_NOT_FOUND'
2026-04-03T06:58:59.319813164Z    },
2026-04-03T06:58:59.319819025Z    statusCode: 500,
2026-04-03T06:58:59.319825168Z    fatal: false,
2026-04-03T06:58:59.319831380Z    unhandled: true,
2026-04-03T06:58:59.319837522Z    statusMessage: undefined,
2026-04-03T06:58:59.319844046Z    data: undefined
2026-04-03T06:58:59.319850408Z  }
2026-04-03T06:58:59.321170987Z  [request error] [unhandled] [GET] http://169.254.129.3:8080/__nuxt_error?error=true&url=%2Frobots933456.txt&statusCode=500&statusMessage=Server+Error&message=Server+Error
2026-04-03T06:58:59.321217901Z   Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
2026-04-03T06:58:59.321225115Z  Did you mean to import "file:///home/site/wwwroot/server/node_modules/unhead/node_modules/hookable"?
2026-04-03T06:58:59.321230105Z      at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
2026-04-03T06:58:59.321235045Z      ... 7 lines matching cause stack trace ...
2026-04-03T06:58:59.321239153Z      at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
2026-04-03T06:58:59.321243161Z    cause: Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
2026-04-03T06:58:59.321247550Z    Did you mean to import "file:///home/site/wwwroot/server/node_modules/unhead/node_modules/hookable"?
2026-04-03T06:58:59.321252239Z        at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
2026-04-03T06:58:59.321256668Z        at packageResolve (node:internal/modules/esm/resolve:767:81)
2026-04-03T06:58:59.321261047Z        at moduleResolve (node:internal/modules/esm/resolve:853:18)
2026-04-03T06:58:59.321265225Z        at defaultResolve (node:internal/modules/esm/resolve:983:11)
2026-04-03T06:58:59.321269474Z        at #cachedDefaultResolve (node:internal/modules/esm/loader:731:20)
2026-04-03T06:58:59.321274103Z        at ModuleLoader.resolve (node:internal/modules/esm/loader:708:38)
2026-04-03T06:58:59.321278121Z        at ModuleLoader.getModuleJobForImport (node:internal/modules/esm/loader:310:38)
2026-04-03T06:58:59.321282820Z        at ModuleJob._link (node:internal/modules/esm/module_job:182:49)
2026-04-03T06:58:59.321286838Z        at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
2026-04-03T06:58:59.321291397Z      code: 'ERR_MODULE_NOT_FOUND'
2026-04-03T06:58:59.321295766Z    },
2026-04-03T06:58:59.321300185Z    statusCode: 500,
2026-04-03T06:58:59.321304463Z    fatal: false,
2026-04-03T06:58:59.321308622Z    unhandled: true,
2026-04-03T06:58:59.321312680Z    statusMessage: undefined,
2026-04-03T06:58:59.321316828Z    data: undefined
2026-04-03T06:58:59.321320736Z  }
2026-04-03T06:59:00.509242239Z  [request error] [unhandled] [GET] https://analogy-make.azurewebsites.net/
2026-04-03T06:59:00.509455014Z   Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
2026-04-03T06:59:00.509463852Z  Did you mean to import "file:///home/site/wwwroot/server/node_modules/unhead/node_modules/hookable"?
2026-04-03T06:59:00.509468551Z      at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
2026-04-03T06:59:00.509489653Z      ... 7 lines matching cause stack trace ...
2026-04-03T06:59:00.509493892Z      at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
2026-04-03T06:59:00.509545184Z    cause: Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
2026-04-03T06:59:00.509551267Z    Did you mean to import "file:///home/site/wwwroot/server/node_modules/unhead/node_modules/hookable"?
2026-04-03T06:59:00.509556036Z        at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
2026-04-03T06:59:00.509560565Z        at packageResolve (node:internal/modules/esm/resolve:767:81)
2026-04-03T06:59:00.509564924Z        at moduleResolve (node:internal/modules/esm/resolve:853:18)
2026-04-03T06:59:00.509569012Z        at defaultResolve (node:internal/modules/esm/resolve:983:11)
2026-04-03T06:59:00.509573350Z        at #cachedDefaultResolve (node:internal/modules/esm/loader:731:20)
2026-04-03T06:59:00.509577699Z        at ModuleLoader.resolve (node:internal/modules/esm/loader:708:38)
2026-04-03T06:59:00.509582118Z        at ModuleLoader.getModuleJobForImport (node:internal/modules/esm/loader:310:38)
2026-04-03T06:59:00.509586436Z        at ModuleJob._link (node:internal/modules/esm/module_job:182:49)
2026-04-03T06:59:00.509590835Z        at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
2026-04-03T06:59:00.509595194Z      code: 'ERR_MODULE_NOT_FOUND'
2026-04-03T06:59:00.509599643Z    },
2026-04-03T06:59:00.509656367Z    statusCode: 500,
2026-04-03T06:59:00.509661536Z    fatal: false,
2026-04-03T06:59:00.509812398Z    unhandled: true,
2026-04-03T06:59:00.509818540Z    statusMessage: undefined,
2026-04-03T06:59:00.509823160Z    data: undefined
2026-04-03T06:59:00.509827388Z  }
2026-04-03T06:59:00.514848849Z  [request error] [unhandled] [GET] https://analogy-make.azurewebsites.net/__nuxt_error?error=true&url=%2F&statusCode=500&statusMessage=Server+Error&message=Server+Error
2026-04-03T06:59:00.514867276Z   Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
2026-04-03T06:59:00.514872296Z  Did you mean to import "file:///home/site/wwwroot/server/node_modules/unhead/node_modules/hookable"?
2026-04-03T06:59:00.514876785Z      at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
2026-04-03T06:59:00.514881034Z      ... 7 lines matching cause stack trace ...
2026-04-03T06:59:00.514885884Z      at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
2026-04-03T06:59:00.514891214Z    cause: Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
2026-04-03T06:59:00.514896264Z    Did you mean to import "file:///home/site/wwwroot/server/node_modules/unhead/node_modules/hookable"?
2026-04-03T06:59:00.514917196Z        at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
2026-04-03T06:59:00.514922697Z        at packageResolve (node:internal/modules/esm/resolve:767:81)
2026-04-03T06:59:00.514927687Z        at moduleResolve (node:internal/modules/esm/resolve:853:18)
2026-04-03T06:59:00.514932507Z        at defaultResolve (node:internal/modules/esm/resolve:983:11)
2026-04-03T06:59:00.514936935Z        at #cachedDefaultResolve (node:internal/modules/esm/loader:731:20)
2026-04-03T06:59:00.514941394Z        at ModuleLoader.resolve (node:internal/modules/esm/loader:708:38)
2026-04-03T06:59:00.514945422Z        at ModuleLoader.getModuleJobForImport (node:internal/modules/esm/loader:310:38)
2026-04-03T06:59:00.514949260Z        at ModuleJob._link (node:internal/modules/esm/module_job:182:49)
2026-04-03T06:59:00.514953719Z        at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
2026-04-03T06:59:00.514958198Z      code: 'ERR_MODULE_NOT_FOUND'
2026-04-03T06:59:00.514962547Z    },
2026-04-03T06:59:00.514966384Z    statusCode: 500,
2026-04-03T06:59:00.514970312Z    fatal: false,
2026-04-03T06:59:00.514973990Z    unhandled: true,
2026-04-03T06:59:00.514977657Z    statusMessage: undefined,
2026-04-03T06:59:00.514981294Z    data: undefined
2026-04-03T06:59:00.514984821Z  }
2026-04-03T06:59:15.129885835Z  [request error] [unhandled] [GET] https://analogy-make.azurewebsites.net/
2026-04-03T06:59:15.129923805Z   Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
2026-04-03T06:59:15.129929155Z  Did you mean to import "file:///home/site/wwwroot/server/node_modules/unhead/node_modules/hookable"?
2026-04-03T06:59:15.129933653Z      at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
2026-04-03T06:59:15.129937800Z      ... 7 lines matching cause stack trace ...
2026-04-03T06:59:15.129942279Z      at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
2026-04-03T06:59:15.129946656Z    cause: Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable' imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs