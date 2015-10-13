from pytg.sender import Sender
from pytg.exceptions import IllegalResponseException
import os
import logging
import yaml
import datetime
import time

logging.basicConfig(level=logging.INFO)

x = Sender("127.0.0.1", 4458)


def build_dialogs_list():
    """Return the list of all dialogs"""
    base_list = []

    res = True

    while res:
        res = x.dialog_list(100, len(base_list))

        base_list += res

    return base_list


def work_on_dialog(d):
    """Backup a particular dialog"""

    logging.info("Working on %s %s %s", d['type'], d['print_name'], d['id'])

    if not d['print_name']:
        logging.error("%s has no print_name, cannot continue.", d['id'])
        return

    working_dir = "logs/by_ids/{}/".format(d['id'])

    if not os.path.isdir(working_dir):
        logging.debug("Creating working_dir %s", working_dir)
        os.mkdir(working_dir)

    symlink = "logs/{},{}".format(d['type'], d['print_name'].replace('/', ''))

    if not os.path.exists(symlink):
        logging.debug("Creating symlink %s", symlink)
        os.symlink(working_dir[5:], symlink)

    # "Eat" history until the last message, but stop at the last checkpoint
    checkpoint_file = "{}/_checkpoint.yaml".format(working_dir)
    last_checkpoint = None

    if os.path.exists(checkpoint_file):
        logging.debug("Loading checkpoing")
        with open(checkpoint_file, 'r') as checkpoint_f:
            data = yaml.load(checkpoint_f)
            last_checkpoint = data.get('checkpoint', None)

    logging.info("Last checkpoint is %s", last_checkpoint)

    messages = {}

    last_messages = True

    while last_messages and last_checkpoint not in messages:

        try:
            last_messages = x.history(d['print_name'], 250, len(messages), retry_connect=-1)
        except IllegalResponseException as e:
            last_messages = []

            if str(e) == "Result parser does not allow exceptions.":
                logging.warning("Slowing down...")
                time.sleep(5)

                last_messages = True
        if last_messages and last_messages != True:
            for message in last_messages:
                messages[message['id']] = message

        logging.info("Loading, offset %s", len(messages))

    logging.info("Found %s messages to process", len(messages))

    # Save messages by date
    loaded_data = {}

    for id, message in messages.items():
        if 'date' not in message:
            logging.error("Not date in message %s", message['id'])
            continue

        date = datetime.datetime.fromtimestamp(message['date'])

        file_key = '{}.{}.yaml'.format(date.year, date.month)

        if file_key not in loaded_data:

            file_key_name = '{}{}'.format(working_dir, file_key)

            if os.path.isfile(file_key_name):

                with open(file_key_name, 'r') as file_key_f:
                    loaded_data[file_key] = yaml.load(file_key_f)
                    logging.info("Loaded datafile %s", file_key)

            else:
                loaded_data[file_key] = {}
                logging.info("Created datafile %s", file_key)

        if message['id'] not in loaded_data[file_key]:
            if message['event'] == 'message':

                loaded_data[file_key][message['id']] = {'from': message['from']['print_name'], 'text': message.get('text', ''), 'date': message['date']}

                if 'media' in message:
                    if message['media']['type'] not in ['webpage', 'contact']:
                        result = x.load_document(message['id'])

                        if os.path.exists(result['result']):

                            file_dir = "files_{}_{}/".format(date.year, date.month)
                            file_dir_full = "{}/{}/".format(working_dir, file_dir)

                            if not os.path.isdir(file_dir_full):
                                os.mkdir(file_dir_full)

                            media_file = "{}/{}.{}".format(file_dir_full, message['id'], result['result'].split('.')[-1].replace('/', ''))
                            os.rename(result['result'], media_file)

                            loaded_data[file_key][message['id']]['media'] = '{}{}.{}'.format(file_dir, message['id'], result['result'].split('.')[-1].replace('/', ''))
                        else:
                            loaded_data[file_key][message['id']]['media'] = result['result']

            elif message['event'] == 'service':
                pass
            else:
                logging.error("Unknow type %s", message['event'])

        if not last_checkpoint or last_checkpoint < message['id']:
            last_checkpoint = message['id']

    # Save messages
    for file_key, data in loaded_data.items():
        with open('{}/{}'.format(working_dir, file_key), 'w') as file_key_f:
            yaml.dump(data, file_key_f, default_flow_style=False)
            logging.info("Saved datafile %s", file_key)

    # Save checkpoint
    with open(checkpoint_file, 'w') as checkpoint_f:
        yaml.dump({'checkpoint': last_checkpoint}, checkpoint_f)
        logging.info("Saved checkpoint")

    return True


for d in build_dialogs_list():
    work_on_dialog(d)
