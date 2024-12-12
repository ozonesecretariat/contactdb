## Install a new self-hosted GitHub actions runner

1. Create a new user for the app and add it to the docker group. Any name can be used, in this example we are using
   `contactdb`:
   ```shell
   sudo useradd --shell /bin/bash --create-home --groups docker contactdb
   ```
1. Create a directory for the action runner and change ownership to the app user:
   ```shell
   sudo mkdir -p /var/local/actions-runner
   sudo chown contactdb:contactdb /var/local/actions-runner
   ```
1. Log in as the new user and change directory to newly created one:
   ```shell
   sudo su - contactdb
   cd /var/local/actions-runner
   ```
1. Follow the steps [here](https://github.com/ozonesecretariat/contactdb/settings/actions/runners/new) to
   install a new self-hosted runner. Make sure to add a label to identify when setting up the deployment workflow when
   configuring:

   ```shell
   $ ./config.sh --url https://github.com/ozonesecretariat/contactdb --token [REDACTED]

   --------------------------------------------------------------------------------
   |        ____ _ _   _   _       _          _        _   _                      |
   |       / ___(_) |_| | | |_   _| |__      / \   ___| |_(_) ___  _ __  ___      |
   |      | |  _| | __| |_| | | | | '_ \    / _ \ / __| __| |/ _ \| '_ \/ __|     |
   |      | |_| | | |_|  _  | |_| | |_) |  / ___ \ (__| |_| | (_) | | | \__ \     |
   |       \____|_|\__|_| |_|\__,_|_.__/  /_/   \_\___|\__|_|\___/|_| |_|___/     |
   |                                                                              |
   |                       Self-hosted runner registration                        |
   |                                                                              |
   --------------------------------------------------------------------------------

   # Authentication


   √ Connected to GitHub

   # Runner Registration

   Enter the name of the runner group to add this runner to: [press Enter for Default]

   Enter the name of runner: [press Enter for rcs] contactdb-production

   This runner will have the following labels: 'self-hosted', 'Linux', 'X64'
   Enter any additional labels (ex. label-1,label-2): [press Enter to skip] contactdb-production

   √ Runner successfully added
   √ Runner connection is good

   # Runner settings

   Enter name of work folder: [press Enter for _work]

   √ Settings Saved.
   ```

1. Configuring the self-hosted runner application as a service under the app user.
   See [official documentation](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/configuring-the-self-hosted-runner-application-as-a-service).
   ```shell
   # first logout from the app user, since it will not have sudo permissions
   logout
   cd /var/local/actions-runner
   sudo ./svc.sh install contactdb
   ```
1. Start the service:
   ```shell
   sudo ./svc.sh start
   ```
1. Create the `.env` file starting from the [example provided](../.env.example):
   ```shell
   vim /home/contactdb/.env
   ```
1. Create the docker override file starting from the [example provided](../compose.override.example.yml):
   ```shell
   vim /home/contactdb/compose.override.yml
   ```
