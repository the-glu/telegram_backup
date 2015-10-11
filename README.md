# telegram_backup
Small python 3 script to backup your telegram logs.

**Not fully tested, use at your own risk !**

Each chat is dump to yaml files in the `logs` folder. Logs are regrouped by date (year.month.yaml)

Medias are downloaded into `files` folders.

A symlink is created with the printable name of each conversation.

## Checkpoint

**You have to check output of logs for any error during download of messages**

The script cannot make the difference between `No messages` and `Error retriving messages` without any doubts and sometime lost older messages.

If you have an error with one of your contact and the script just continue by processing messages instead of trying again, delete the `_checkpoint.yaml` file to ensure all history will be checked again.

## Usage

* You will need [telegram-cli](https://github.com/vysheng/tg) and [pytg](https://github.com/luckydonald/pytg) and python 3. Check others repos for specific instructions.
* Setup `telegram-cli` (connect it to your account :))
* Grab a copy of the script (e.g git clone this repo)
* Create a `logs` folder
* Run telegram-cli using `telegram-cli -P 4458 -W --json`
* Run the script: `python dump.py`

## TODOs

* Check that everything is saved
* Remove dirty hack `str(e) == "Result parser does not allow exceptions."`
* Easy install (setup.py ?)
* Probably dosen't works with Windows
