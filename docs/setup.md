# Environment Setup

AITK supports both ADB and Appium for Android interaction. The ADB method is the basic method and more lightweight but it lacks features like screen recording. Appium is an open-source tool for mobile automation testing. It is more powerful but requires more setup such as installing Java and less stable. Thus installing Appium is optional (only for screen recording so far). You can choose one of them according to your needs.

## Basic Setup

### Step 1: Install Android Studio (**Required**)

For either OS, download and install Android Studio from [link](https://developer.android.com/studio), use default settings to install.

### Step 2: Setup Environment Variables

**Add `platform-tools` and `emulator` to the `PATH` environment variable.** Replace `<user>` with your username.

- In Mac, add the following line to `~/.bashrc` or `~/.zshrc`:

  ```shell
  export PATH=$PATH:/Users/<user>/Library/Android/sdk/platform-tools
  export PATH=$PATH:/Users/<user>/Library/Android/sdk/emulator
  ```

- In Linux, add the following line to `~/.bashrc` or `~/.zshrc`:

  ```shell
  export "PATH=${PATH}:/home/<user>/Android/Sdk/platform-tools/"
  export "PATH=${PATH}:/home/<user>/Android/Sdk/emulator"
  ```

- In Windows, you can follow the guide from [link](https://windowsloop.com/add-environment-variable-in-windows-10/). The path should be something like `C:\Users\<user>\AppData\Local\Android\Sdk\platform-tools` and `C:\Users\<user>\AppData\Local\Android\Sdk\emulator`.

### Step 3: Install Python dependencies

In terminal run

```shell
conda create -n aitk python=3.10
conda activate aitk
pip install -r requirements.txt
pip install -e .
```

### Step 4: Setup AVD

#### 1. Download the AVD image

Download the AVD image from [here](https://huggingface.co/datasets/Yuxiang007/A3V2-AVD-Image). Unzip the file and copy the `A3V2.avd` folder and `A3V2.ini` file to `~/.android/avd/` (on all OS). So it should be like this:

```shell
~/.android/avd/
├── A3V2.avd
├── A3V2.ini
```

#### 2. Initialize the AVD

Run `python scripts/init_avd.py` to initialize the AVD. (if the device pops up a window to let USB debugging, select "always xxxx" so that it won't pop up again)

Once the AVD is initialized and running, do the following:

1. Use your Google account to log in the Play Store (so that every Google app can be logged in). Do not back up the device!!!
2. Login to Pinterest and TripAdvisor using your Google account. Open Gmail and Youtube and sign in.
3. (You can use whatever device to do this) Send an email to `stock_notify_01@163.com` from your gmail account to get an auto-reply email for the task requirements. The subject should be "Nice to see you" and the content should be "I am OK".
4. Shut down the AVD by directly closing the AVD window (wait for the device to "saving data").

**Note that the correctly-executed tasks will not change anything in your account except for sending an email. However, if your agent misbehaves, something might happen. (hopefully nothing severe, don't blame me)**

<details>
<summary><h2>Appium Setup (Optional)</h2></summary>

Appium is only required for screen recording and customization.

### Step 1: Install Node.js

**In Linux/Mac:**

- Install `nvm` from [link](https://github.com/nvm-sh/nvm?tab=readme-ov-file#install--update-script)
- Install `node` and `npm` by `nvm` from [link](https://github.com/nvm-sh/nvm?tab=readme-ov-file#usage)

**In Windows:**

- Install `nvm-windows` from [link](https://github.com/coreybutler/nvm-windows)
- Install `node` and `npm` by `nvm-windows` from [link](https://github.com/coreybutler/nvm-windows?tab=readme-ov-file#usage)

### Step 2: Install Appium Server

```shell
npm i -g appium
```

### Step 3: Setup UIAutomator2 Driver

**SubStep 1: Install JDK-21**

In all OS:

- Install JDK-21 from [link](https://www.oracle.com/java/technologies/downloads/)

**SubStep 2: Setup Environment Variables**

In Linux:

- Add `JAVA_HOME`, `ANDROID_HOME` to the environment variable. Add the following lines to `~/.bashrc` or `~/.zshrc`:

  ```shell
  export JAVA_HOME="/usr/lib/jvm/jdk-21-oracle-x64/"
  export ANDROID_HOME="/home/<user>/Android/Sdk/"
  ```

In Mac:

- Add `JAVA_HOME`, `ANDROID_HOME` to the environment variable. Add the following lines to `~/.bashrc` or `~/.zshrc`:

  ```shell
  export JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home/"
  export ANDROID_HOME="/Users/<user>/Library/Android/sdk"
  ```

In Windows:

- Add `JAVA_HOME`, `ANDROID_HOME` to the environment variable (you can follow the guide from [link](https://windowsloop.com/add-environment-variable-in-windows-10/)). The path should be something like `C:\Program Files\Java\jdk-21` and `C:\Users\<user>\AppData\Local\Android\Sdk`.

**SubStep 3: Install UIAutomator2 Driver**

```shell
appium driver install uiautomator2
```

### Step 4: Install Appium Client

```shell
pip install Appium-Python-Client==4.2.0
```
