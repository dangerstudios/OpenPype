import os
import subprocess
import sys
from functools import partial

from Qt import QtWidgets, QtCore, QtGui
from Qt.QtCore import Qt

from openpype.tools.settings import (
    ProjectListWidget,
    style
)

from openpype.api import get_local_site_id
from openpype.lib import PypeLogger

from avalon.tools.delegates import pretty_timestamp
from avalon.vendor import qtawesome

from openpype.modules.sync_server.tray.models import (
    SyncRepresentationSummaryModel,
    SyncRepresentationDetailModel
)

from openpype.modules.sync_server.tray import lib

log = PypeLogger().get_logger("SyncServer")


class SyncProjectListWidget(ProjectListWidget):
    """
        Lists all projects that are synchronized to choose from
    """

    def __init__(self, sync_server, parent):
        super(SyncProjectListWidget, self).__init__(parent)
        self.sync_server = sync_server
        self.project_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.project_list.customContextMenuRequested.connect(
            self._on_context_menu)
        self.project_name = None
        self.local_site = None
        self.icons = {}

        self.layout().setContentsMargins(0, 0, 0, 0)

    def validate_context_change(self):
        return True

    def refresh(self):
        model = self.project_list.model()
        model.clear()

        project_name = None
        for project_name in self.sync_server.sync_project_settings.\
                keys():
            if self.sync_server.is_paused() or \
               self.sync_server.is_project_paused(project_name):
                icon = self._get_icon("paused")
            else:
                icon = self._get_icon("synced")

            model.appendRow(QtGui.QStandardItem(icon, project_name))

        if len(self.sync_server.sync_project_settings.keys()) == 0:
            model.appendRow(QtGui.QStandardItem(lib.DUMMY_PROJECT))

        self.current_project = self.project_list.currentIndex().data(
            QtCore.Qt.DisplayRole
        )
        if not self.current_project:
            self.current_project = self.project_list.model().item(0). \
                data(QtCore.Qt.DisplayRole)

        if project_name:
            self.local_site = self.sync_server.get_active_site(project_name)

    def _get_icon(self, status):
        if not self.icons.get(status):
            resource_path = os.path.dirname(__file__)
            resource_path = os.path.join(resource_path, "..",
                                         "resources")
            pix_url = "{}/{}.png".format(resource_path, status)
            icon = QtGui.QIcon(pix_url)
            self.icons[status] = icon
        else:
            icon = self.icons[status]
        return icon

    def _on_context_menu(self, point):
        point_index = self.project_list.indexAt(point)
        if not point_index.isValid():
            return

        self.project_name = point_index.data(QtCore.Qt.DisplayRole)

        menu = QtWidgets.QMenu()
        actions_mapping = {}

        if self.sync_server.is_project_paused(self.project_name):
            action = QtWidgets.QAction("Unpause")
            actions_mapping[action] = self._unpause
        else:
            action = QtWidgets.QAction("Pause")
            actions_mapping[action] = self._pause
        menu.addAction(action)

        if self.local_site == get_local_site_id():
            action = QtWidgets.QAction("Clear local project")
            actions_mapping[action] = self._clear_project
            menu.addAction(action)

        result = menu.exec_(QtGui.QCursor.pos())
        if result:
            to_run = actions_mapping[result]
            if to_run:
                to_run()

    def _pause(self):
        if self.project_name:
            self.sync_server.pause_project(self.project_name)
            self.project_name = None
        self.refresh()

    def _unpause(self):
        if self.project_name:
            self.sync_server.unpause_project(self.project_name)
            self.project_name = None
        self.refresh()

    def _clear_project(self):
        if self.project_name:
            self.sync_server.clear_project(self.project_name, self.local_site)
            self.project_name = None
        self.refresh()


class _SyncRepresentationWidget(QtWidgets.QWidget):
    """
        Summary dialog with list of representations that matches current
        settings 'local_site' and 'remote_site'.
    """
    active_changed = QtCore.Signal()  # active index changed
    message_generated = QtCore.Signal(str)

    def _selection_changed(self, _new_selected, _all_selected):
        idxs = self.selection_model.selectedRows()
        self._selected_ids = []

        for index in idxs:
            self._selected_ids.append(self.model.data(index, Qt.UserRole))

    def _set_selection(self):
        """
            Sets selection to 'self._selected_id' if exists.

            Keep selection during model refresh.
        """
        existing_ids = []
        for selected_id in self._selected_ids:
            index = self.model.get_index(selected_id)
            if index and index.isValid():
                mode = QtCore.QItemSelectionModel.Select | \
                    QtCore.QItemSelectionModel.Rows
                self.selection_model.select(index, mode)
                existing_ids.append(selected_id)

        self._selected_ids = existing_ids

    def _double_clicked(self, index):
        """
            Opens representation dialog with all files after doubleclick
        """
        _id = self.model.data(index, Qt.UserRole)
        detail_window = SyncServerDetailWindow(
            self.sync_server, _id, self.model.project)
        detail_window.exec()
        
    def _on_context_menu(self, point):
        """
            Shows menu with loader actions on Right-click.

            Supports multiple selects - adds all available actions, each
            action handles if it appropriate for item itself, if not it skips.
        """
        is_multi = len(self._selected_ids) > 1
        point_index = self.table_view.indexAt(point)
        if not point_index.isValid() and not is_multi:
            return

        if is_multi:
            index = self.model.get_index(self._selected_ids[0])
            item = self.model.data(index, lib.FullItemRole)
        else:
            item = self.model.data(point_index, lib.FullItemRole)

        action_kwarg_map, actions_mapping, menu = self._prepare_menu(item,
                                                                     is_multi)

        result = menu.exec_(QtGui.QCursor.pos())
        if result:
            to_run = actions_mapping[result]
            to_run_kwargs = action_kwarg_map.get(result, {})
            if to_run:
                to_run(**to_run_kwargs)

        self.model.refresh()

    def _prepare_menu(self, item, is_multi):
        menu = QtWidgets.QMenu()

        actions_mapping = {}
        action_kwarg_map = {}

        active_site = self.model.active_site
        remote_site = self.model.remote_site

        local_progress = item.local_progress
        remote_progress = item.remote_progress

        project = self.model.project

        for site, progress in {active_site: local_progress,
                               remote_site: remote_progress}.items():
            provider = self.sync_server.get_provider_for_site(project, site)
            if provider == 'local_drive':
                if 'studio' in site:
                    txt = " studio version"
                else:
                    txt = " local version"
                action = QtWidgets.QAction("Open in explorer" + txt)
                if progress == 1.0 or is_multi:
                    actions_mapping[action] = self._open_in_explorer
                    action_kwarg_map[action] = \
                        self._get_action_kwargs(site)
                    menu.addAction(action)

        if remote_progress == 1.0 or is_multi:
            action = QtWidgets.QAction("Re-sync Active site")
            action_kwarg_map[action] = self._get_action_kwargs(active_site)
            actions_mapping[action] = self._reset_site
            menu.addAction(action)

        if local_progress == 1.0 or is_multi:
            action = QtWidgets.QAction("Re-sync Remote site")
            action_kwarg_map[action] = self._get_action_kwargs(remote_site)
            actions_mapping[action] = self._reset_site
            menu.addAction(action)

        if active_site == get_local_site_id():
            action = QtWidgets.QAction("Completely remove from local")
            action_kwarg_map[action] = self._get_action_kwargs(active_site)
            actions_mapping[action] = self._remove_site
            menu.addAction(action)

        # # temp for testing only !!!
        # action = QtWidgets.QAction("Download")
        # action_kwarg_map[action] = self._get_action_kwargs(active_site)
        # actions_mapping[action] = self._add_site
        # menu.addAction(action)

        if not actions_mapping:
            action = QtWidgets.QAction("< No action >")
            actions_mapping[action] = None
            menu.addAction(action)

        return action_kwarg_map, actions_mapping, menu

    def _pause(self, selected_ids=None):
        log.debug("Pause {}".format(selected_ids))
        for representation_id in selected_ids:
            item = lib.get_item_by_id(self.model, representation_id)
            if item.status not in [lib.STATUS[0], lib.STATUS[1]]:
                continue
            for site_name in [self.model.active_site, self.model.remote_site]:
                check_progress = self._get_progress(item, site_name)
                if check_progress < 1:
                    self.sync_server.pause_representation(self.model.project,
                                                          representation_id,
                                                          site_name)

            self.message_generated.emit("Paused {}".format(representation_id))

    def _unpause(self, selected_ids=None):
        log.debug("UnPause {}".format(selected_ids))
        for representation_id in selected_ids:
            item = lib.get_item_by_id(self.model, representation_id)
            if item.status not in lib.STATUS[3]:
                continue
            for site_name in [self.model.active_site, self.model.remote_site]:
                check_progress = self._get_progress(item, site_name)
                if check_progress < 1:
                    self.sync_server.unpause_representation(
                        self.model.project,
                        representation_id,
                        site_name)

            self.message_generated.emit("Unpause {}".format(representation_id))

    # temporary here for testing, will be removed TODO
    def _add_site(self, selected_ids=None, site_name=None):
        log.debug("Add site {}:{}".format(selected_ids, site_name))
        for representation_id in selected_ids:
            item = lib.get_item_by_id(self.model, representation_id)
            if item.local_site == site_name or item.remote_site == site_name:
                # site already exists skip
                continue

            try:
                self.sync_server.add_site(
                    self.model.project,
                    representation_id,
                    site_name)
                self.message_generated.emit(
                    "Site {} added for {}".format(site_name,
                                                  representation_id))
            except ValueError as exp:
                self.message_generated.emit("Error {}".format(str(exp)))

    def _remove_site(self, selected_ids=None, site_name=None):
        """
            Removes site record AND files.

            This is ONLY for representations stored on local site, which
            cannot be same as SyncServer.DEFAULT_SITE.

            This could only happen when artist work on local machine, not
            connected to studio mounted drives.
        """
        log.debug("Remove site {}:{}".format(selected_ids, site_name))
        for representation_id in selected_ids:
            log.info("Removing {}".format(representation_id))
            try:
                self.sync_server.remove_site(
                    self.model.project,
                    representation_id,
                    site_name,
                    True)
                self.message_generated.emit(
                    "Site {} removed".format(site_name))
            except ValueError as exp:
                self.message_generated.emit("Error {}".format(str(exp)))

        self.model.refresh(
            load_records=self.model._rec_loaded)

    def _reset_site(self, selected_ids=None, site_name=None):
        """
            Removes errors or success metadata for particular file >> forces
            redo of upload/download
        """
        log.debug("Reset site {}:{}".format(selected_ids, site_name))
        for representation_id in selected_ids:
            item = lib.get_item_by_id(self.model, representation_id)
            check_progress = self._get_progress(item, site_name, True)

            # do not reset if opposite side is not fully there
            if check_progress != 1:
                log.debug("Not fully available {} on other side, skipping".
                          format(check_progress))
                continue

            self.sync_server.reset_provider_for_file(
                self.model.project,
                representation_id,
                site_name=site_name,
                force=True)

        self.model.refresh(
            load_records=self.model._rec_loaded)

    def _open_in_explorer(self, selected_ids=None, site_name=None):
        log.debug("Open in Explorer {}:{}".format(selected_ids, site_name))
        for selected_id in selected_ids:
            item = lib.get_item_by_id(self.model, selected_id)
            if not item:
                return

            fpath = item.path
            project = self.model.project
            fpath = self.sync_server.get_local_file_path(project,
                                                         site_name,
                                                         fpath)

            fpath = os.path.normpath(os.path.dirname(fpath))
            if os.path.isdir(fpath):
                if 'win' in sys.platform:  # windows
                    subprocess.Popen('explorer "%s"' % fpath)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.Popen(['open', fpath])
                else:  # linux
                    try:
                        subprocess.Popen(['xdg-open', fpath])
                    except OSError:
                        raise OSError('unsupported xdg-open call??')

    def _get_progress(self, item, site_name, opposite=False):
        """Returns progress value according to site (side)"""
        progress = {'local': item.local_progress,
                    'remote': item.remote_progress}
        side = 'remote'
        if site_name == self.model.active_site:
            side = 'local'
        if opposite:
            side = 'remote' if side == 'local' else 'local'

        return progress[side]

    def _get_action_kwargs(self, site_name):
        """Default format of kwargs for action"""
        return {"selected_ids": self._selected_ids, "site_name": site_name}

    def _save_scrollbar(self):
        self._scrollbar_pos = self.table_view.verticalScrollBar().value()

    def _set_scrollbar(self):
        if self._scrollbar_pos:
            self.table_view.verticalScrollBar().setValue(self._scrollbar_pos)


class SyncRepresentationSummaryWidget(_SyncRepresentationWidget):

    default_widths = (
        ("asset", 190),
        ("subset", 170),
        ("version", 60),
        ("representation", 145),
        ("local_site", 160),
        ("remote_site", 160),
        ("files_count", 50),
        ("files_size", 60),
        ("priority", 70),
        ("status", 110)
    )

    def __init__(self, sync_server, project=None, parent=None):
        super(SyncRepresentationSummaryWidget, self).__init__(parent)

        self.sync_server = sync_server

        self._selected_ids = []  # keep last selected _id

        txt_filter = QtWidgets.QLineEdit()
        txt_filter.setPlaceholderText("Quick filter representations..")
        txt_filter.setClearButtonEnabled(True)
        txt_filter.addAction(
            qtawesome.icon("fa.filter", color="gray"),
            QtWidgets.QLineEdit.LeadingPosition)
        self.txt_filter = txt_filter

        self._scrollbar_pos = None

        top_bar_layout = QtWidgets.QHBoxLayout()
        top_bar_layout.addWidget(self.txt_filter)

        table_view = QtWidgets.QTableView()
        headers = [item[0] for item in self.default_widths]

        model = SyncRepresentationSummaryModel(sync_server, headers, project)
        table_view.setModel(model)
        table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table_view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        table_view.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        table_view.horizontalHeader().setSortIndicator(
            -1, Qt.AscendingOrder)
        table_view.setAlternatingRowColors(True)
        table_view.verticalHeader().hide()

        column = table_view.model().get_header_index("local_site")
        delegate = ImageDelegate(self)
        table_view.setItemDelegateForColumn(column, delegate)

        column = table_view.model().get_header_index("remote_site")
        delegate = ImageDelegate(self)
        table_view.setItemDelegateForColumn(column, delegate)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top_bar_layout)
        layout.addWidget(table_view)

        self.table_view = table_view
        self.model = model

        horizontal_header = HorizontalHeader(self)

        table_view.setHorizontalHeader(horizontal_header)
        table_view.setSortingEnabled(True)

        for column_name, width in self.default_widths:
            idx = model.get_header_index(column_name)
            table_view.setColumnWidth(idx, width)

        table_view.doubleClicked.connect(self._double_clicked)
        self.txt_filter.textChanged.connect(lambda: model.set_word_filter(
            self.txt_filter.text()))
        table_view.customContextMenuRequested.connect(self._on_context_menu)

        model.refresh_started.connect(self._save_scrollbar)
        model.refresh_finished.connect(self._set_scrollbar)
        model.modelReset.connect(self._set_selection)

        self.selection_model = self.table_view.selectionModel()
        self.selection_model.selectionChanged.connect(self._selection_changed)

    def _prepare_menu(self, item, is_multi):
        action_kwarg_map, actions_mapping, menu = \
            super()._prepare_menu(item, is_multi)

        if item.status in [lib.STATUS[0], lib.STATUS[1]] or is_multi:
            action = QtWidgets.QAction("Pause in queue")
            actions_mapping[action] = self._pause
            # pause handles which site_name it will pause itself
            action_kwarg_map[action] = {"selected_ids": self._selected_ids}
            menu.addAction(action)

        if item.status == lib.STATUS[3] or is_multi:
            action = QtWidgets.QAction("Unpause  in queue")
            actions_mapping[action] = self._unpause
            action_kwarg_map[action] = {"selected_ids": self._selected_ids}
            menu.addAction(action)

        return action_kwarg_map, actions_mapping, menu


class SyncServerDetailWindow(QtWidgets.QDialog):
    """Wrapper window for SyncRepresentationDetailWidget

        Creates standalone window with list of files for selected repre_id.
    """
    def __init__(self, sync_server, _id, project, parent=None):
        log.debug(
            "!!! SyncServerDetailWindow _id:: {}".format(_id))
        super(SyncServerDetailWindow, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.setStyleSheet(style.load_stylesheet())
        self.setWindowIcon(QtGui.QIcon(style.app_icon_path()))
        self.resize(1000, 400)

        body = QtWidgets.QWidget()
        footer = QtWidgets.QWidget()
        footer.setFixedHeight(20)

        container = SyncRepresentationDetailWidget(sync_server, _id, project,
                                                   parent=self)
        body_layout = QtWidgets.QHBoxLayout(body)
        body_layout.addWidget(container)
        body_layout.setContentsMargins(0, 0, 0, 0)

        self.message = QtWidgets.QLabel()
        self.message.hide()

        footer_layout = QtWidgets.QVBoxLayout(footer)
        footer_layout.addWidget(self.message)
        footer_layout.setContentsMargins(0, 0, 0, 0)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(body)
        layout.addWidget(footer)

        self.setLayout(body_layout)
        self.setWindowTitle("Sync Representation Detail")


class SyncRepresentationDetailWidget(_SyncRepresentationWidget):
    """
        Widget to display list of synchronizable files for single repre.

        Args:
            _id (str): representation _id
            project (str): name of project with repre
            parent (QDialog): SyncServerDetailWindow
    """
    active_changed = QtCore.Signal()  # active index changed

    default_widths = (
        ("file", 290),
        ("local_site", 185),
        ("remote_site", 185),
        ("size", 60),
        ("priority", 60),
        ("status", 110)
    )

    def __init__(self, sync_server, _id=None, project=None, parent=None):
        super(SyncRepresentationDetailWidget, self).__init__(parent)

        log.debug("Representation_id:{}".format(_id))
        self.project = project

        self.sync_server = sync_server

        self.representation_id = _id
        self._selected_ids = []

        self.txt_filter = QtWidgets.QLineEdit()
        self.txt_filter.setPlaceholderText("Quick filter representation..")
        self.txt_filter.setClearButtonEnabled(True)
        self.txt_filter.addAction(qtawesome.icon("fa.filter", color="gray"),
                                  QtWidgets.QLineEdit.LeadingPosition)

        self._scrollbar_pos = None

        top_bar_layout = QtWidgets.QHBoxLayout()
        top_bar_layout.addWidget(self.txt_filter)

        table_view = QtWidgets.QTableView()
        headers = [item[0] for item in self.default_widths]

        model = SyncRepresentationDetailModel(sync_server, headers, _id,
                                              project)
        table_view.setModel(model)
        table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table_view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        table_view.setSelectionBehavior(
            QtWidgets.QTableView.SelectRows)
        table_view.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        table_view.horizontalHeader().setSortIndicatorShown(True)
        table_view.setAlternatingRowColors(True)
        table_view.verticalHeader().hide()

        column = model.get_header_index("local_site")
        delegate = ImageDelegate(self)
        table_view.setItemDelegateForColumn(column, delegate)

        column = model.get_header_index("remote_site")
        delegate = ImageDelegate(self)
        table_view.setItemDelegateForColumn(column, delegate)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top_bar_layout)
        layout.addWidget(table_view)

        self.model = model

        self.selection_model = table_view.selectionModel()
        self.selection_model.selectionChanged.connect(self._selection_changed)

        horizontal_header = HorizontalHeader(self)

        table_view.setHorizontalHeader(horizontal_header)
        table_view.setSortingEnabled(True)

        for column_name, width in self.default_widths:
            idx = model.get_header_index(column_name)
            table_view.setColumnWidth(idx, width)

        self.table_view = table_view

        self.txt_filter.textChanged.connect(lambda: model.set_word_filter(
            self.txt_filter.text()))
        table_view.customContextMenuRequested.connect(self._on_context_menu)

        model.refresh_started.connect(self._save_scrollbar)
        model.refresh_finished.connect(self._set_scrollbar)
        model.modelReset.connect(self._set_selection)

    def _show_detail(self, selected_ids=None):
        """
            Shows windows with error message for failed sync of a file.
        """
        detail_window = SyncRepresentationErrorWindow(self.model, selected_ids)

        detail_window.exec()

    def _prepare_menu(self, item, is_multi):
        """Adds view (and model) dependent actions to default ones"""
        action_kwarg_map, actions_mapping, menu = \
            super()._prepare_menu(item, is_multi)

        if item.status == lib.STATUS[2] or is_multi:
            action = QtWidgets.QAction("Open error detail")
            actions_mapping[action] = self._show_detail
            action_kwarg_map[action] = {"selected_ids": self._selected_ids}

            menu.addAction(action)

        return action_kwarg_map, actions_mapping, menu

    def _reset_site(self, selected_ids=None, site_name=None):
        """
            Removes errors or success metadata for particular file >> forces
            redo of upload/download
        """
        for file_id in selected_ids:
            item = lib.get_item_by_id(self.model, file_id)
            check_progress = self._get_progress(item, site_name, True)

            # do not reset if opposite side is not fully there
            if check_progress != 1:
                log.debug("Not fully available {} on other side, skipping".
                          format(check_progress))
                continue

            self.sync_server.reset_provider_for_file(
                self.model.project,
                self.representation_id,
                site_name=site_name,
                file_id=file_id,
                force=True)
        self.model.refresh(
            load_records=self.model._rec_loaded)


class SyncRepresentationErrorWindow(QtWidgets.QDialog):
    """Wrapper window to show errors during sync on file(s)"""
    def __init__(self, model, selected_ids, parent=None):
        super(SyncRepresentationErrorWindow, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.setStyleSheet(style.load_stylesheet())
        self.setWindowIcon(QtGui.QIcon(style.app_icon_path()))
        self.resize(900, 150)

        body = QtWidgets.QWidget()

        container = SyncRepresentationErrorWidget(model,
                                                  selected_ids,
                                                  parent=self)
        body_layout = QtWidgets.QHBoxLayout(body)
        body_layout.addWidget(container)
        body_layout.setContentsMargins(0, 0, 0, 0)

        message = QtWidgets.QLabel()
        message.hide()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(body)

        self.setLayout(body_layout)
        self.setWindowTitle("Sync Representation Error Detail")


class SyncRepresentationErrorWidget(QtWidgets.QWidget):
    """
        Dialog to show when sync error happened, prints formatted error message
    """
    def __init__(self, model, selected_ids, parent=None):
        super(SyncRepresentationErrorWidget, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)

        no_errors = True
        for file_id in selected_ids:
            item = lib.get_item_by_id(model, file_id)
            if not item.created_dt or not item.sync_dt or not item.error:
                continue

            no_errors = False
            dt = max(item.created_dt, item.sync_dt)

            txts = []
            txts.append("{}: {}<br>".format("<b>Last update date</b>",
                                            pretty_timestamp(dt)))
            txts.append("{}: {}<br>".format("<b>Retries</b>",
                                            str(item.tries)))
            txts.append("{}: {}<br>".format("<b>Error message</b>",
                                            item.error))

            text_area = QtWidgets.QTextEdit("\n\n".join(txts))
            text_area.setReadOnly(True)
            layout.addWidget(text_area)

        if no_errors:
            text_area = QtWidgets.QTextEdit()
            text_area.setText("<h4>No errors located</h4>")
            text_area.setReadOnly(True)
            layout.addWidget(text_area)


class ImageDelegate(QtWidgets.QStyledItemDelegate):
    """
        Prints icon of site and progress of synchronization
    """

    def __init__(self, parent=None):
        super(ImageDelegate, self).__init__(parent)
        self.icons = {}

    def paint(self, painter, option, index):
        super(ImageDelegate, self).paint(painter, option, index)
        option = QtWidgets.QStyleOptionViewItem(option)
        option.showDecorationSelected = True

        provider = index.data(lib.ProviderRole)
        value = index.data(lib.ProgressRole)
        date_value = index.data(lib.DateRole)
        is_failed = index.data(lib.FailedRole)

        if not self.icons.get(provider):
            resource_path = os.path.dirname(__file__)
            resource_path = os.path.join(resource_path, "..",
                                         "providers", "resources")
            pix_url = "{}/{}.png".format(resource_path, provider)
            pixmap = QtGui.QPixmap(pix_url)
            self.icons[provider] = pixmap
        else:
            pixmap = self.icons[provider]

        padding = 10
        point = QtCore.QPoint(option.rect.x() + padding,
                              option.rect.y() +
                              (option.rect.height() - pixmap.height()) / 2)
        painter.drawPixmap(point, pixmap)

        overlay_rect = option.rect.translated(0, 0)
        overlay_rect.setHeight(overlay_rect.height() * (1.0 - float(value)))
        painter.fillRect(overlay_rect,
                         QtGui.QBrush(QtGui.QColor(0, 0, 0, 100)))
        text_rect = option.rect.translated(10, 0)
        painter.drawText(text_rect,
                         QtCore.Qt.AlignCenter,
                         date_value)

        if is_failed:
            overlay_rect = option.rect.translated(0, 0)
            painter.fillRect(overlay_rect,
                             QtGui.QBrush(QtGui.QColor(255, 0, 0, 35)))


class TransparentWidget(QtWidgets.QWidget):
    """Used for header cell for resizing to work properly"""
    clicked = QtCore.Signal(str)

    def __init__(self, column_name, *args, **kwargs):
        super(TransparentWidget, self).__init__(*args, **kwargs)
        self.column_name = column_name
        # self.setStyleSheet("background: red;")

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.column_name)

        super(TransparentWidget, self).mouseReleaseEvent(event)


class HorizontalHeader(QtWidgets.QHeaderView):
    """Reiplemented QHeaderView to contain clickable changeable button"""
    def __init__(self, parent=None):
        super(HorizontalHeader, self).__init__(QtCore.Qt.Horizontal, parent)
        self._parent = parent
        self.checked_values = {}

        self.setModel(self._parent.model)

        self.setSectionsClickable(True)

        self.menu_items_dict = {}
        self.menu = None
        self.header_cells = []
        self.filter_buttons = {}

        self.filter_icon = qtawesome.icon("fa.filter", color="gray")
        self.filter_set_icon = qtawesome.icon("fa.filter", color="white")

        self.init_layout()

        self._resetting = False

    @property
    def model(self):
        """Keep model synchronized with parent widget"""
        return self._parent.model

    def init_layout(self):
        """Initial preparation of header's content"""
        for column_idx in range(self.model.columnCount()):
            column_name, column_label = self.model.get_column(column_idx)
            filter_rec = self.model.get_filters().get(column_name)
            if not filter_rec:
                continue

            icon = self.filter_icon
            button = QtWidgets.QPushButton(icon, "", self)

            button.setFixedSize(24, 24)
            button.setStyleSheet(
                "QPushButton::menu-indicator{width:0px;}"
                "QPushButton{border: none;background: transparent;}")
            button.clicked.connect(partial(self._get_menu,
                                           column_name, column_idx))
            button.setFlat(True)
            self.filter_buttons[column_name] = button

    def showEvent(self, event):
        """Paint header"""
        super(HorizontalHeader, self).showEvent(event)

        for i in range(len(self.header_cells)):
            cell_content = self.header_cells[i]
            cell_content.setGeometry(self.sectionViewportPosition(i), 0,
                                     self.sectionSize(i) - 1, self.height())

            cell_content.show()

    def _set_filter_icon(self, column_name):
        """Set different states of button depending on its engagement"""
        button = self.filter_buttons.get(column_name)
        if button:
            if self.checked_values.get(column_name):
                button.setIcon(self.filter_set_icon)
            else:
                button.setIcon(self.filter_icon)

    def _reset_filter(self, column_name):
        """
            Remove whole column from filter >> not in $match at all (faster)
        """
        self._resetting = True  # mark changes to consume them
        if self.checked_values.get(column_name) is not None:
            self.checked_values.pop(column_name)
            self._set_filter_icon(column_name)
        self._filter_and_refresh_model_and_menu(column_name, True, True)
        self._resetting = False

    def _apply_filter(self, column_name, values, state):
        """
            Sets 'values' to specific 'state' (checked/unchecked),
            sends to model.
        """
        if self._resetting:  # event triggered by _resetting, skip it
            return

        self._update_checked_values(column_name, values, state)
        self._set_filter_icon(column_name)
        self._filter_and_refresh_model_and_menu(column_name, True, False)

    def _apply_text_filter(self, column_name, items, line_edit):
        """
            Resets all checkboxes, prefers inserted text.
        """
        le_text = line_edit.text()
        self._update_checked_values(column_name, items, 0)  # reset other
        if self.checked_values.get(column_name) is not None or \
                le_text == '':
            self.checked_values.pop(column_name)  # reset during typing

        if le_text:
            self._update_checked_values(column_name, {le_text: le_text}, 2)
        self._set_filter_icon(column_name)
        self._filter_and_refresh_model_and_menu(column_name, True, True)

    def _filter_and_refresh_model_and_menu(self, column_name,
                                           model=True, menu=True):
        """
            Refresh model and its content and possibly menu for big changes.
        """
        if model:
            self.model.set_column_filtering(self.checked_values)
            self.model.refresh()
        if menu:
            self._menu_refresh(column_name)

    def _get_menu(self, column_name, index):
        """Prepares content of menu for 'column_name'"""
        menu = QtWidgets.QMenu(self)
        filter_rec = self.model.get_filters()[column_name]
        self.menu_items_dict[column_name] = filter_rec.values()

        # text filtering only if labels same as values, not if codes are used
        if 'text' in filter_rec.search_variants():
            line_edit = QtWidgets.QLineEdit(menu)
            line_edit.setClearButtonEnabled(True)
            line_edit.addAction(self.filter_icon,
                                QtWidgets.QLineEdit.LeadingPosition)

            line_edit.setFixedHeight(line_edit.height())
            txt = ""
            if self.checked_values.get(column_name):
                txt = list(self.checked_values.get(column_name).keys())[0]
            line_edit.setText(txt)

            action_le = QtWidgets.QWidgetAction(menu)
            action_le.setDefaultWidget(line_edit)
            line_edit.textChanged.connect(
                partial(self._apply_text_filter, column_name,
                        filter_rec.values(), line_edit))
            menu.addAction(action_le)
            menu.addSeparator()

        if 'checkbox' in filter_rec.search_variants():
            action_all = QtWidgets.QAction("All", self)
            action_all.triggered.connect(partial(self._reset_filter,
                                                 column_name))
            menu.addAction(action_all)

            action_none = QtWidgets.QAction("Unselect all", self)
            state_unchecked = 0
            action_none.triggered.connect(partial(self._apply_filter,
                                                  column_name,
                                                  filter_rec.values(),
                                                  state_unchecked))
            menu.addAction(action_none)
            menu.addSeparator()

        # nothing explicitly >> ALL implicitly >> first time
        if self.checked_values.get(column_name) is None:
            checked_keys = self.menu_items_dict[column_name].keys()
        else:
            checked_keys = self.checked_values[column_name]

        for value, label in self.menu_items_dict[column_name].items():
            checkbox = QtWidgets.QCheckBox(str(label), menu)

            # temp
            checkbox.setStyleSheet("QCheckBox{spacing: 5px;"
                                   "padding:5px 5px 5px 5px;}")
            if value in checked_keys:
                checkbox.setChecked(True)

            action = QtWidgets.QWidgetAction(menu)
            action.setDefaultWidget(checkbox)

            checkbox.stateChanged.connect(partial(self._apply_filter,
                                                  column_name, {value: label}))
            menu.addAction(action)

        self.menu = menu

        self._show_menu(index, menu)

    def _show_menu(self, index, menu):
        """Shows 'menu' under header column of 'index'"""
        global_pos_point = self.mapToGlobal(
            QtCore.QPoint(self.sectionViewportPosition(index), 0))
        menu.setMinimumWidth(self.sectionSize(index))
        menu.setMinimumHeight(self.height())
        menu.exec_(QtCore.QPoint(global_pos_point.x(),
                                 global_pos_point.y() + self.height()))

    def _menu_refresh(self, column_name):
        """
            Reset boxes after big change - word filtering or reset
        """
        for action in self.menu.actions():
            if not isinstance(action, QtWidgets.QWidgetAction):
                continue

            widget = action.defaultWidget()
            if not isinstance(widget, QtWidgets.QCheckBox):
                continue

            if not self.checked_values.get(column_name) or \
                    widget.text() in self.checked_values[column_name].values():
                widget.setChecked(True)
            else:
                widget.setChecked(False)

    def _update_checked_values(self, column_name, values, state):
        """
            Modify dictionary of set values in columns for filtering.

            Modifies 'self.checked_values'
        """
        copy_menu_items = dict(self.menu_items_dict[column_name])
        checked = self.checked_values.get(column_name, copy_menu_items)
        set_items = dict(values.items())  # prevent dict change during loop
        for value, label in set_items.items():
            if state == 2 and label:  # checked
                checked[value] = label
            elif state == 0 and checked.get(value):
                checked.pop(value)

        self.checked_values[column_name] = checked

    def paintEvent(self, event):
        self._fix_size()
        super(HorizontalHeader, self).paintEvent(event)

    def _fix_size(self):
        for column_idx in range(self.model.columnCount()):
            vis_index = self.visualIndex(column_idx)
            index = self.logicalIndex(vis_index)
            section_width = self.sectionSize(index)

            column_name = self.model.headerData(column_idx,
                                                QtCore.Qt.Horizontal,
                                                lib.HeaderNameRole)
            button = self.filter_buttons.get(column_name)
            if not button:
                continue

            pos_x = self.sectionViewportPosition(
                index) + section_width - self.height()

            pos_y = 0
            if button.height() < self.height():
                pos_y = int((self.height() - button.height()) / 2)
            button.setGeometry(
                pos_x,
                pos_y,
                self.height(),
                self.height())
