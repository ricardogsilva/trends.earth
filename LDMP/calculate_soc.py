# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LDMP - A QGIS plugin
 This plugin supports monitoring and reporting of land degradation to the UNCCD 
 and in support of the SDG Land Degradation Neutrality (LDN) target.
                              -------------------
        begin                : 2017-05-23
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Conservation International
        email                : trends.earth@conservation.org
 ***************************************************************************/
"""

import json

from qgis.utils import iface
mb = iface.messageBar()

from PyQt4 import QtGui

from LDMP import log
from LDMP.calculate import DlgCalculateBase, get_script_slug
from LDMP.calculate_lc import lc_setup_widget
from LDMP.gui.DlgCalculateSOC import Ui_DlgCalculateSOC
from LDMP.api import run_script


class DlgCalculateSOC(DlgCalculateBase, Ui_DlgCalculateSOC):
    def __init__(self, parent=None):
        super(DlgCalculateSOC, self).__init__(parent)

        self.setupUi(self)
        
        self.regimes = [('Temperate dry (Fl = 0.80)', .80),
                        ('Temperate moist (Fl = 0.69)', .69),
                        ('Tropical dry (Fl = 0.58)', .58),
                        ('Tropical moist (Fl = 0.48)', .48),
                        ('Tropical montane (Fl = 0.64)', .64)]

        self.fl_chooseRegime_comboBox.addItems([r[0] for r in self.regimes])
        self.fl_chooseRegime_comboBox.setEnabled(False)
        self.fl_custom_lineEdit.setEnabled(False)
        # Setup validator for lineedit entries
        validator = QtGui.QDoubleValidator()
        validator.setBottom(0)
        validator.setDecimals(3)
        self.fl_custom_lineEdit.setValidator(validator)
        self.fl_radio_default.toggled.connect(self.fl_radios_toggled)
        self.fl_radio_chooseRegime.toggled.connect(self.fl_radios_toggled)
        self.fl_radio_custom.toggled.connect(self.fl_radios_toggled)

    def showEvent(self, event):
        super(DlgCalculateSOC, self).showEvent(event)

        self.lc_setup_tab = lc_setup_widget
        self.TabBox.insertTab(0, self.lc_setup_tab, self.tr('Land Cover Setup'))

        if self.reset_tab_on_showEvent:
            self.TabBox.setCurrentIndex(0)

    def fl_radios_toggled(self):
        if self.fl_radio_custom.isChecked():
            self.fl_chooseRegime_comboBox.setEnabled(False)
            self.fl_custom_lineEdit.setEnabled(True)
        elif self.fl_radio_chooseRegime.isChecked():
            self.fl_chooseRegime_comboBox.setEnabled(True)
            self.fl_custom_lineEdit.setEnabled(False)
        else:
            self.fl_chooseRegime_comboBox.setEnabled(False)
            self.fl_custom_lineEdit.setEnabled(False)

    def get_fl(self):
        if self.fl_radio_custom.isChecked():
            return float(self.fl_custom_lineEdit.text())
        elif self.fl_radio_chooseRegime.isChecked():
            return [r[1] for r in self.regimes if r[0] == self.fl_chooseRegime_comboBox.currentText()][0]
        else:
            return 'per pixel'

    def btn_calculate(self):
        # Note that the super class has several tests in it - if they fail it
        # returns False, which would mean this function should stop execution
        # as well.
        ret = super(DlgCalculateSOC, self).btn_calculate()
        if not ret:
            return

        self.close()

        payload = {'year_start': self.lc_setup_tab.use_esa_bl_year.date().year(),
                   'year_end': self.lc_setup_tab.use_esa_tg_year.date().year(),
                   'fl': self.get_fl(),
                   'download_annual_lc': self.download_annual_lc.isChecked(),
                   'geojson': json.dumps(self.aoi.bounding_box_gee_geojson()),
                   'remap_matrix': self.lc_setup_tab.dlg_esa_agg.get_agg_as_list(),
                   'task_name': self.options_tab.task_name.text(),
                   'task_notes': self.options_tab.task_notes.toPlainText()}

        resp = run_script(get_script_slug('soil-organic-carbon'), payload)

        if resp:
            mb.pushMessage(QtGui.QApplication.translate("LDMP", "Submitted"),
                           QtGui.QApplication.translate("LDMP", "Soil organic carbon submitted to Google Earth Engine."),
                           level=0, duration=5)
        else:
            mb.pushMessage(QtGui.QApplication.translate("LDMP", "Error"),
                           QtGui.QApplication.translate("LDMP", "Unable to submit soil organic carbon task to Google Earth Engine."),
                           level=0, duration=5)
