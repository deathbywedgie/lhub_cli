from configobj import ConfigObj


def dict_to_ini_file(dict_obj, file_path, sort_keys=True):
    config = ConfigObj(indent_type='    ', write_empty_values=True)
    config.filename = file_path
    _first_line = True
    if sort_keys:
        # Sort by connection name in order to make the credential file more readable
        dict_obj = dict(sorted(dict_obj.items()))
    for k, v in dict_obj.items():
        config[k] = v

        if _first_line:
            _first_line = False
        else:
            # Hack for adding a blank line between sections: Insert an empty comment before each section
            # https://sourceforge.net/p/configobj/mailman/message/24432354/
            config.comments[k].insert(0, '')
    config.write()
