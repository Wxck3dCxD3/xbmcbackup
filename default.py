import sys

import xbmc
import xbmcgui
import xbmcvfs
import resources.lib.utils as utils
from resources.lib.backup import XbmcBackup
from resources.lib.authorizers import DropboxAuthorizer
from resources.lib.advanced_editor import AdvancedBackupEditor

# mode constants
BACKUP = 0
RESTORE = 1
SETTINGS = 2
ADVANCED_EDITOR = 3
LAUNCHER = 4


def authorize_cloud(cloud_provider):
    if cloud_provider == 'dropbox':
        authorizer = DropboxAuthorizer()

        if authorizer.authorize():
            xbmcgui.Dialog().ok(utils.getString(30010), f"{utils.getString(30027)} {utils.getString(30106)}")
        else:
            xbmcgui.Dialog().ok(utils.getString(30010), f"{utils.getString(30107)} {utils.getString(30027)}")


def remove_auth():
    # triggered from settings.xml — asks if user wants to delete OAuth token information
    should_delete = xbmcgui.Dialog().yesno(
        utils.getString(30093),
        f"{utils.getString(30094)}\n{utils.getString(30095)}",
        autoclose=7000,
    )

    if should_delete:
        xbmcvfs.delete(xbmcvfs.translatePath(utils.data_dir() + "tokens.json"))       # dropbox
        xbmcvfs.delete(xbmcvfs.translatePath(utils.data_dir() + "google_drive.dat"))  # google drive


def get_params():
    param = {}
    try:
        for arg in sys.argv:
            if '=' not in arg:
                continue
            if arg.startswith('?'):
                arg = arg[1:]  # strip legacy url prefix
            parts = arg.split('=', 1)  # maxsplit=1 preserves '=' inside values (e.g. base64 tokens)
            if parts[0]:
                param[parts[0]] = parts[1]
    except Exception as e:
        utils.log(f"get_params error: {e}", xbmc.LOGWARNING)

    return param


def main():
    mode = -1
    params = get_params()

    if 'mode' in params:
        if params['mode'] == 'backup':
            mode = BACKUP
        elif params['mode'] == 'restore':
            mode = RESTORE
        elif params['mode'] == 'launcher':
            mode = LAUNCHER

    # if mode wasn't passed in as arg, get from user
    if mode == -1:
        options = [utils.getString(30016), utils.getString(30017), utils.getString(30099)]

        if utils.getSettingInt('backup_selection_type') == 1:
            options.append(utils.getString(30125))

        mode = xbmcgui.Dialog().select(
            f"{utils.getString(30010)} - {utils.getString(30023)}",
            options,
        )

    if mode == -1:
        return

    if mode == SETTINGS:
        utils.openSettings()

    elif mode == ADVANCED_EDITOR and utils.getSettingInt('backup_selection_type') == 1:
        editor = AdvancedBackupEditor()
        editor.showMainScreen()

    elif mode == LAUNCHER:
        action = params.get('action', '')
        if action == 'authorize_cloud':
            authorize_cloud(params.get('provider', ''))
        elif action == 'remove_auth':
            remove_auth()
        elif action == 'advanced_editor':
            editor = AdvancedBackupEditor()
            editor.showMainScreen()
        elif action == 'advanced_copy_config':
            editor = AdvancedBackupEditor()
            editor.copySimpleConfig()

    elif mode == BACKUP or mode == RESTORE:
        backup = XbmcBackup()

        if mode == RESTORE and backup.remoteConfigured():
            restore_points = backup.listBackups()

            if restore_points:
                folder_names, point_names = zip(*restore_points)
                folder_names = list(folder_names)
                point_names = list(point_names)
            else:
                folder_names, point_names = [], []

            selected_restore = -1

            if 'archive' in params:
                try:
                    selected_restore = folder_names.index(params['archive'])
                    utils.log(f"{selected_restore} : {params['archive']}")
                except ValueError:
                    utils.showNotification(utils.getString(30045))
                    utils.log(f"{params['archive']} is not a valid restore point")
            else:
                selected_restore = xbmcgui.Dialog().select(
                    f"{utils.getString(30010)} - {utils.getString(30021)}",
                    point_names,
                )

            if selected_restore != -1:
                backup.selectRestore(restore_points[selected_restore][0])

                if 'sets' in params:
                    backup.restore(selectedSets=params['sets'].split('|'))
                else:
                    backup.restore()

        elif mode == BACKUP and backup.remoteConfigured():
            backup.backup()

        else:
            xbmcgui.Dialog().ok(utils.getString(30010), utils.getString(30045))
            utils.openSettings()

    else:
        unknown = params.get('mode', str(mode))
        xbmcgui.Dialog().ok(utils.getString(30010), f"{utils.getString(30159)} {unknown}")


if __name__ == '__main__':
    main()
