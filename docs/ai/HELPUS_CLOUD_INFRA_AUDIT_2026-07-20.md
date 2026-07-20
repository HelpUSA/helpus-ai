# Auditoria Real da Infraestrutura Cloud HelpUS

Data: 2026-07-20

Base auditada: `ba48f3e4ba5fa1ad9eeb8b7475583e8cccd8dd7a`

## Resumo

- situação: `completa`;
- GitHub: `True`;
- Vercel: `True`;
- Railway: `True`;
- domínio público: `True`;
- status HTTP: `200`;
- serviços cloud alterados: `False`;
- valores de variáveis consultados: `False`;
- secrets registrados: `False`.

## Configuração existente

- railway.json: `True`;
- vercel.json: `True`;
- Dockerfile do backend: `True`;
- Dockerfile do roteador: `True`;
- configuração LiteLLM: `True`;
- Compose multi-IA: `True`.

## GitHub

### Autenticação GitHub

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Program Files\GitHub CLI\gh.exe auth status`.

```text
github.com
  ✓ Logged in to github.com account HelpUSA (keyring)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_************************************
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'
```

### Repositório GitHub

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Program Files\GitHub CLI\gh.exe repo view HelpUSA/helpus-ai --json nameWithOwner,defaultBranchRef,visibility,url`.

```text
{"defaultBranchRef":{"name":"main"},"nameWithOwner":"HelpUSA/helpus-ai","url":"https://github.com/HelpUSA/helpus-ai","visibility":"PUBLIC"}
```

### Workflows GitHub

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Program Files\GitHub CLI\gh.exe workflow list --repo HelpUSA/helpus-ai`.

```text
Local audit safety	active	312457877
Multi-AI foundation	active	315928034
```

## Vercel

### Identidade Vercel

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Users\wmsjp\AppData\Roaming\npm\vercel.cmd whoami`.

```text
helpusecommerce-7210

Vercel CLI 54.9.1 (Node.js 22.20.0)
```

### Projetos Vercel

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Users\wmsjp\AppData\Roaming\npm\vercel.cmd project ls`.

```text
Vercel CLI 54.9.1 (Node.js 22.20.0)
Fetching projects in help-us
> Projects found under help-us  [2s]

  Project Name           Latest Production URL                            Updated   Node Version
  marciotopbarber        https://marciotopbarber.vercel.app               17m       22.x
  helpus-ai              https://ai.helpusbr.com                          2h        24.x
  web                    https://web-puce-seven-83.vercel.app             6d        24.x
  pizza                  https://pizza.helpusbr.com                       7d        24.x
  cvss                   https://cvss.helpusbr.com                        16d       24.x
  helpus-site            https://www.helpusbr.com                         19d       22.x
  brayyan                https://brayyan.vercel.app                       47d       24.x
  trading                https://trading.helpusbr.com                     47d       24.x
  nexosai-frontend       https://nexoai.helpusbr.com                      51d       24.x
  wagnerdriver-site      https://wagnerdriver.helpusa.com.br              56d       22.x
  escolaestacaomusical   https://escolaestacaomusical.vercel.app          56d       22.x
  plural-locacoes        https://plural-locacoes.vercel.app               56d       22.x
  bluebox                https://bluebox.helpusa.com.br                   56d       22.x
  drmatheusbomfim        https://drmatheusbomfim.vercel.app               57d       24.x
  energisa               https://energisa.helpusbr.com                    57d       24.x
  jobs                   https://jobs.helpusbr.com                        57d       24.x
  visa                   https://visa.helpusbr.com                        58d       24.x
  publicarte             https://publicarte-git-main-help-us.vercel.app   58d       22.x
  usmle                  https://usmle.helpusbr.com                       59d       24.x
  vivasuacura            https://vivasuacura.vercel.app                   60d       24.x

> To display the next page, run `vercel project ls --next 1779443934695`
```

### Domínios Vercel

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Users\wmsjp\AppData\Roaming\npm\vercel.cmd domains ls`.

```text
Vercel CLI 54.9.1 (Node.js 22.20.0)
Fetching Domains under help-us
> 5 Domains found under help-us [284ms]

  Domain             Registrar           Nameservers         Expiration Date    Creator                     Age
  helpus.com         Third Party         Third Party         -                  helpusecommerce-7210        173d
  helpusbr.com       Third Party         Third Party         -                  helpusecommerce-7210        308d
  hlepusa.com.br     Third Party         Third Party         -                  helpusecommerce-7210        375d
  helpus.com.br      Third Party         Third Party         -                  helpusecommerce-7210        377d
  helpusa.com.br     Third Party         Third Party         -                  helpusecommerce-7210        389d
```

### Deployments Vercel

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Users\wmsjp\AppData\Roaming\npm\vercel.cmd ls`.

```text
https://helpus-na3kkbc9n-help-us.vercel.app
https://helpus-f8g3wli1y-help-us.vercel.app
https://helpus-roia04fu8-help-us.vercel.app
https://helpus-nf52cj3by-help-us.vercel.app
https://helpus-juzzge17p-help-us.vercel.app
https://helpus-fcd5fcxol-help-us.vercel.app
https://helpus-i76tu0t75-help-us.vercel.app
https://helpus-ev1otx90e-help-us.vercel.app
https://helpus-boups44lz-help-us.vercel.app
https://helpus-2sfq96e5y-help-us.vercel.app
https://helpus-823xzov3a-help-us.vercel.app
https://helpus-4no6i6686-help-us.vercel.app
https://helpus-2qg2jkoav-help-us.vercel.app
https://helpus-cratulhg3-help-us.vercel.app
https://helpus-igk0j6wsw-help-us.vercel.app
https://helpus-25ff0x6bu-help-us.vercel.app
https://helpus-pj8lse7kz-help-us.vercel.app
https://helpus-27xgv7haq-help-us.vercel.app
https://helpus-j8n9ruv38-help-us.vercel.app
https://helpus-oksigqynr-help-us.vercel.app

Vercel CLI 54.9.1 (Node.js 22.20.0)
Retrieving project…
Fetching deployments in help-us
> Deployments for help-us/helpus-ai [339ms]

  Age     Project               Deployment                                      Status      Environment     Duration     Username
  2h      help-us/helpus-ai     https://helpus-na3kkbc9n-help-us.vercel.app     ● Ready     Production      25s          helpusecommerce-7210
  3h      help-us/helpus-ai     https://helpus-f8g3wli1y-help-us.vercel.app     ● Ready     Production      31s          helpusecommerce-7210
  2d      help-us/helpus-ai     https://helpus-roia04fu8-help-us.vercel.app     ● Ready     Production      24s          helpusecommerce-7210
  2d      help-us/helpus-ai     https://helpus-nf52cj3by-help-us.vercel.app     ● Ready     Production      20s          helpusecommerce-7210
  3d      help-us/helpus-ai     https://helpus-juzzge17p-help-us.vercel.app     ● Ready     Production      32s          helpusecommerce-7210
  6d      help-us/helpus-ai     https://helpus-fcd5fcxol-help-us.vercel.app     ● Ready     Production      24s          helpusecommerce-7210
  6d      help-us/helpus-ai     https://helpus-i76tu0t75-help-us.vercel.app     ● Ready     Production      24s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-ev1otx90e-help-us.vercel.app     ● Ready     Production      19s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-boups44lz-help-us.vercel.app     ● Ready     Production      25s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-2sfq96e5y-help-us.vercel.app     ● Ready     Production      19s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-823xzov3a-help-us.vercel.app     ● Ready     Production      19s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-4no6i6686-help-us.vercel.app     ● Ready     Production      21s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-2qg2jkoav-help-us.vercel.app     ● Ready     Production      20s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-cratulhg3-help-us.vercel.app     ● Ready     Production      25s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-igk0j6wsw-help-us.vercel.app     ● Ready     Production      26s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-25ff0x6bu-help-us.vercel.app     ● Ready     Production      19s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-pj8lse7kz-help-us.vercel.app     ● Ready     Production      21s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-27xgv7haq-help-us.vercel.app     ● Ready     Production      26s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-j8n9ruv38-help-us.vercel.app     ● Ready     Production      27s          helpusecommerce-7210
  7d      help-us/helpus-ai     https://helpus-oksigqynr-help-us.vercel.app     ● Ready     Production      20s          helpusecommerce-7210

> To display the next page, run `vercel ls --next 1783982984703`
```

Valores das variáveis Vercel consultados: `False`.

## Railway

### Identidade Railway

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Users\wmsjp\AppData\Roaming\npm\railway.cmd whoami`.

```text
Logged in as helpus.ecommerce@gmail.com 👋
```

### Projetos Railway

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Users\wmsjp\AppData\Roaming\npm\railway.cmd list`.

```text
helpusa's Projects
  helpus-whatsapp-ia
  beneficial-warmth
  helpus-ai
  brayyan
  trading
  jobs
  pizza-helpusbr
  ai-bridge-v2
  helpus-jobs
  cvss-environmental-dashboard
  energisa
  proud-education
  ample-perception
  helpus-aut-api
```

### Status Railway

- CLI disponível: `True`;
- comando aprovado: `True`;
- código: `0`;
- comando: `C:\Users\wmsjp\AppData\Roaming\npm\railway.cmd status`.

```text
Workspace:       helpusa's Projects

Project:         helpus-ai
Project ID:      acceb075-b024-4756-9ec8-ab158544c079

Environment:     production
Environment ID:  6527765c-2a35-4852-a7b2-b6daf352d14f

Linked service

helpus-api
    status:        ● Online
    repo:          HelpUSA/helpus-ai
    url:           https://helpus-api-production.up.railway.app
    region:        US East
    deployment ID: 7b8d305b-8e5d-4363-aa3b-7f6e68467746
    service ID:    d7fa0359-64fe-43d0-9e4b-4586f1cd6c9a

────────────────────────────────────────────────

All resources

    Services
      - helpus-api: ● Online · https://helpus-api-production.up.railway.app
    Databases
      - Postgres: ● Online · postgres-volume
```

Valores das variáveis Railway consultados: `False`.

## Domínio público

- URL: `https://ai.helpusbr.com/`;
- respondeu: `True`;
- status HTTP: `200`;
- DNS: `216.198.79.65, 64.29.17.65`;
- erro sanitizado: ``.

## Conclusão

GitHub, Vercel, Railway e o domínio público foram auditados sem alteração dos serviços cloud.

## Próximas atividades

1. identificar os serviços exatos no Railway;
2. confirmar o projeto Vercel do domínio;
3. preparar staging;
4. preparar Dockerfile cloud do LiteLLM;
5. preparar o Multi-AI Router para `$PORT`;
6. configurar rede privada;
7. cadastrar secrets no Railway;
8. implantar com a feature flag desligada;
9. executar smoke tests;
10. ativar gradualmente.
