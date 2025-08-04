# Environment Setup

- [Step 1: Install Android Studio](#step-1-install-android-studio)
- [Step 2: Install Appium Server](#step-2-install-appium-server)
  - [For Linux/Mac](#for-linuxmac)
  - [For Windows](#for-windows)
- [Step 3: Install Appium Driver](#step-3-install-appium-driver)
- [Step 4: Install Appium client and other dependencies](#step-4-install-appium-client-and-other-dependencies)

## Step 1: Install Android Studio

For either OS, download and install Android Studio from [link](https://developer.android.com/studio), use default settings to install.

## Step 2: Install Appium Server

### For Linux/Mac

#### 1. Install Node.js

- Install `nvm` from [link](https://github.com/nvm-sh/nvm?tab=readme-ov-file#install--update-script)

- Install `node` and `npm` by `nvm` from [link](https://github.com/nvm-sh/nvm?tab=readme-ov-file#usage)

#### 2. Install Appium Server

official website: [link](https://appium.io/docs/en/2.4/quickstart/install/)

#### 3. Setup requirements for UIAutomator2 Driver

- Install JDK from [link](https://www.oracle.com/java/technologies/downloads/)
- Add `JAVA_HOME` to the environment variable. In Linux or Mac, add the following line to `~/.bashrc` or `~/.zshrc`:

  ```shell
  export JAVA_HOME="/path/to/jdk"
  ```

  For example, in Mac, add the following line to `~/.zshrc`:

  ```shell
  export JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home/"
  ```

- Add `ANDROID_HOME` to the environment variable. In Linux or Mac, add the following line to `~/.bashrc` or `~/.zshrc`:

  ```shell
  export ANDROID_HOME="/path/to/Android/Sdk"
  ```

  For example, in Mac, add the following line to `~/.zshrc`:

  ```shell
  export ANDROID_HOME="/Users/<user>/Library/Android/sdk"
  ```

- Add `platform-tools` and `build-tools` to the `PATH` environment variable. In Linux or Mac, add the following line to `~/.bashrc` or `~/.zshrc`:

  ```shell
  export PATH=$PATH:$ANDROID_HOME/platform-tools
  export PATH=$PATH:$ANDROID_HOME/build-tools/34.0.0
  ```

  For example, in Mac, add the following line to `~/.zshrc`:

  ```shell
  export PATH=$PATH:/Users/<user>/Library/Android/sdk/platform-tools
  export PATH=$PATH:/Users/<user>/Library/Android/sdk/build-tools/34.0.0
  ```

Linux example:

```shell
export ANDROID_HOME="/home/<user>/Android/Sdk/"
export JAVA_HOME="/usr/lib/jvm/jdk-21-oracle-x64/"
export "PATH=${PATH}:/home/<user>/Android/Sdk/build-tools/34.0.0/"
export "PATH=${PATH}:/home/<user>/Android/Sdk/platform-tools/"
```

Mac example:

```shell
export ANDROID_HOME="/Users/<user>/Library/Android/sdk/"
export JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home/"
export "PATH=${PATH}:/Users/<user>/Library/Android/sdk/build-tools/34.0.0/"
export "PATH=${PATH}:/Users/<user>/Library/Android/sdk/platform-tools/"
```

### For Windows

#### 1. Install Node.js

1. install `nvm-windows` from [link](https://github.com/coreybutler/nvm-windows)
2. install `node` and `npm` by `nvm-windows` from [link](https://github.com/coreybutler/nvm-windows?tab=readme-ov-file#usage)

#### 2. Install Appium Server

official website: [link](https://appium.io/docs/en/2.4/quickstart/install/)

#### 3. Setup requirements for UIAutomator2 Driver

- Install JDK from [link](https://www.oracle.com/java/technologies/downloads/)
- Add `JAVA_HOME` to the environment variable. Your can follow the guide from [link](https://windowsloop.com/add-environment-variable-in-windows-10/). The path should be something like `C:\Program Files\Java\jdk-21`
- Add `ANDROID_HOME` to the environment variable. The path should be something like `C:\Users\<user>\AppData\Local\Android\Sdk`, which can be checked from Android Studio -> Settings -> SDK Manager.

## Step 3: Install Appium Driver

In terminal run

```shell
appium driver install uiautomator2
```

## Step 4: Install Appium client and other dependencies

In terminal run

```shell
conda create -n aitk python=3.10
conda activate aitk
pip install -r requirements.txt
```
