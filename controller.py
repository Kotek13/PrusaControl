# -*- coding: utf-8 -*-
import logging

import functools

import time

import sceneData
from gui import PrusaControllView
from projectFile import ProjectFile
from sceneData import AppScene, ModelTypeStl
from sceneRender import GLWidget
from copy import deepcopy

import xml.etree.cElementTree as ET
from zipfile import ZipFile

from PyQt4 import QtCore

#Mesure
def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        logging.debug('%s function took %0.3f ms' % (f.func_name, (time2-time1)*1000.0))
        return ret
    return wrap

class Controller:
    def __init__(self):
        logging.info('Controller instance created')

        #TODO:Reading settings from file
        self.printing_settings = {}
        self.settings = {}
        if not self.settings:
            self.settings['debug'] = False
            self.settings['automatic_placing'] = True
            self.settings['language'] = 'en'
            self.settings['printer'] = 'prusa_i3_v2'
            self.settings['toolButtons'] = {
                'moveButton': False,
                'rotateButton': False,
                'scaleButton': False
                #'selectButton': True
        }

        self.printing_settings = {
            'materials': ['abs', 'pla', 'flex'],
            'abs': {
                'speed': 25,
                'quality': ['draft', 'low', 'medium'],
                'infill': 65,
                'infillRange': [20, 80]
            },
            'pla': {
                'speed': 10,
                'infill': 20,
                'infillRange': [0, 100]
            },
            'default': {
                'bed': 100,
                'hotEnd': 250,
                'quality': ['draft', 'low', 'medium', 'high', 'ultra_high'],
                'speed': 20,
                'infill': 20,
                'infillRange': [0, 100]
            }
        }

        self.enumeration = {
            'language': {
                'cs': 'Czech',
                'en': 'English'
            },
            'printer': {
                'prusa_i3': 'Prusa i3',
                'prusa_i3_v2': 'Prusa i3 v2'
            },
            'materials': {
                'pla': 'PLA',
                'abs': 'ABS',
                'flex': 'FLEX'
            },
            'quality': {
                'draft': 'Draft',
                'low': 'Low',
                'medium': 'Medium',
                'high': 'High',
                'ultra_high': 'Ultra high'
            }
        }

        '''
            #language
            'cs': 'Czech',
            'en': 'English',
            #printer
            'prusa_i3': 'Prusa i3',
            'prusa_i3_v2': 'Prusa i3 v2',
            #materials
            'pla': 'PLA',
            'abs': 'ABS',
            'flex': 'FLEX',
            #quality
            'draft':'Draft',
            'low':'Low',
            'medium':'Medium',
            'high':'High',
            'ultra_high':'Ultra high'
        '''

        #variables for help
        self.last_pos = QtCore.QPoint()
        self.ray_start = [.0, .0, .0]
        self.ray_end = [.0, .0, .0]
        self.res_old = []

        self.view = PrusaControllView(self)
        self.view.disable_save_g_code_button()
        self.scene = AppScene()

    def get_enumeration(self, section, enum):
        return self.enumeration[section][enum] if section in self.enumeration and enum in self.enumeration[section] else str(section)+':'+str(enum)

    def get_printer_name(self):
        #TODO:Add code for read and detect printer name
        return "Original Prusa i3"

    def get_firmware_version_number(self):
        #TODO:Add code for download firmware version
        return '1.0.1'

    def tab_selected(self, n):
        if n==1:
            self.clear_tool_button_states()
            self.view.clear_tool_buttons()

    def get_printing_materials(self):
        return self.printing_settings['materials']

    def get_printing_settings_for_material(self, material_id):
        material = self.printing_settings['materials'][material_id]
        #Deep copy, very important
        printing_settings_tmp = deepcopy(self.printing_settings['default'])
        printing_settings_tmp.update(self.printing_settings[material] if material in self.printing_settings else {})
        return printing_settings_tmp

    def update_gui(self):
        self.view.update_gui()

    def get_view(self):
        return self.view

    def get_model(self):
        return self.scene

    def open_printer_info(self):
        self.view.open_printer_info_dialog()

    def open_update_firmware(self):
        self.view.open_firmware_dialog()

    def open_project_file(self, url=None):
        if url:
            data =url
        else:
            data = self.view.open_project_file_dialog()
        logging.debug('open project file %s' %data)
        self.import_project(data)

    def save_project_file(self):
        data = self.view.save_project_file_dialog()
        logging.debug('save project file %s' %data)
        self.save_project(data)

    def save_gcode_file(self):
        data = self.view.save_gcode_file_dialog()
        print(str(data))

    def open_model_file(self):
        data = self.view.open_model_file_dialog()
        logging.debug('open model file %s' %data)
        self.import_model(data)

    def import_model(self, path):
        self.view.statusBar().showMessage('Load file name: ' + path)
        self.scene.models.append(ModelTypeStl().load(path))
        if self.settings['automatic_placing']:
            self.scene.automatic_models_position()
        self.view.update_scene()

    def import_project(self, path):
        #TODO:Add code for read zip file, in memory open it and read xml file scene(with transformations of objects) and object files in stl
        #open zip file
        project_file = ProjectFile(self.scene, path)
        self.view.update_scene()

    def save_project(self, path):
        #TODO:Save project file
        project_file = ProjectFile(self.scene)
        project_file.save(path)

    def update_firmware(self):
        #TODO:Add code for update of firmware
        pass

    def open_settings(self):
        self.settings = self.view.open_settings_dialog()

    def open_about(self):
        self.view.open_about_dialog()

    def generate_button_pressed(self):
        logging.debug('Generate button pressed')
        self.scene.save_whole_scene_to_one_stl_file("/home/tibor/projects/PrusaControll/tmp/tmp.stl")
        self.view.enable_save_gcode_button()


    def close(self):
        exit()

    def wheel_event(self, event):
        self.view.set_zoom(event.delta()/120)
        self.view.statusBar().showMessage("Zoom = %s" % self.view.get_zoom())
        self.view.update_scene()

    def mouse_press_event(self, event):
        self.last_pos = QtCore.QPoint(event.pos())
        newRayStart, newRayEnd = self.view.get_cursor_position(event)
        #if event.buttons() & QtCore.Qt.LeftButton:
        #    logging.debug("hledani objektu na oznaceni")
        #    self.hit_first_object_by_color(event)
        self.hit_tool_button_by_color(event)
        if event.buttons() & QtCore.Qt.LeftButton & (self.settings['toolButtons']['moveButton']):
            self.res_old = sceneData.intersection_ray_plane(newRayStart, newRayEnd)
            self.hit_first_object_by_color(event)
        elif event.buttons() & QtCore.Qt.LeftButton & (self.settings['toolButtons']['rotateButton']):
            self.find_object_and_rotation_axis_by_color(event)
        elif event.buttons() & QtCore.Qt.LeftButton & (self.settings['toolButtons']['scaleButton']):
            self.find_object_and_scale_axis_by_color(event)
        self.view.update_scene()

    def mouse_release_event(self, event):
        self.scene.clear_selected_models()
        self.view.update_scene()

    def mouse_move_event(self, event):
        dx = event.x() - self.last_pos.x()
        dy = event.y() - self.last_pos.y()
        newRayStart, newRayEnd = self.view.get_cursor_position(event)

        if event.buttons() & QtCore.Qt.LeftButton & self.settings['toolButtons']['moveButton']:

            res = sceneData.intersection_ray_plane(newRayStart, newRayEnd)
            if res is not None:
                res_new = sceneData.Vector.minusAB(res, self.res_old)
                for model in self.scene.models:
                    if model.selected:
                        model.pos = [p+n for p, n in zip(model.pos, res_new)]
                    self.res_old = res


        elif event.buttons() & QtCore.Qt.LeftButton & self.settings['toolButtons']['rotateButton']:
            res = [.0,.0,.0]
            #find plane(axis) in which rotation will be made
            #newRayStart, newRayEnd = self.view.get_cursor_position(event)
            for model in self.scene.models:
                if model.selected and model.rotationAxis:
                    #position = [i+o for i,o in zip(model.boundingSphereCenter, model.pos)]
                    if model.rotationAxis == 'y':
                        model.rot[0] = model.rot[0] + dy*0.25
                    elif model.rotationAxis == 'z':
                        model.rot[1] = model.rot[1] + dy*0.25
                    elif model.rotationAxis == 'x':
                        model.rot[2] = model.rot[2] + dx*0.25
                    else:
                        res = [.0,.0,.0]
                self.res_old = res
            #self.view.updateScene()


        elif event.buttons() & QtCore.Qt.LeftButton & self.settings['toolButtons']['scaleButton']:
            res = [.0,.0,.0]
            #find axis(), set scale on model instance
            for model in self.scene.models:
                if model.selected and model.scaleAxis:
                    #position = [i+o for i,o in zip(model.boundingSphereCenter, model.pos)]
                    if model.scaleAxis == 'x':
                        model.scale[0] = model.scale[0] + dx*0.25
                    elif model.scaleAxis == 'y':
                        model.scale[1] = model.scale[1] + dx*0.25
                    elif model.scaleAxis == 'z':
                        model.scale[2] = model.scale[2] + dy*0.25
                    elif model.scaleAxis == 'xyz':
                        model.scale = [ i + dy*0.25 for i in model.scale]
                    else:
                        res = [.0,.0,.0]
                self.res_old = res


        elif event.buttons() & QtCore.Qt.RightButton:
            #TODO:Add controll of camera instance
            self.view.set_x_rotation(self.view.get_x_rotation() + 8 * dy)
            self.view.set_z_rotation(self.view.get_z_rotation() + 8 * dx)

        self.last_pos = QtCore.QPoint(event.pos())
        self.view.update_scene()

    def hit_objects(self, event):
        possible_hit = []
        nSelected = 0

        self.ray_start, self.ray_end = self.view.get_cursor_position(event)

        for model in self.scene.models:
            if model.intersection_ray_bounding_sphere(self.ray_start, self.ray_end):
                possible_hit.append(model)
                nSelected+=1
            else:
                model.selected = False

        if not nSelected:
            return False

        for model in possible_hit:
            if model.intersection_ray_model(self.ray_start, self.ray_end):
                model.selected = not model.selected
            else:
                model.selected = False

        return False

    def hit_first_object(self, event):
        possible_hit = []
        nSelected = 0
        self.ray_start, self.ray_end = self.view.get_cursor_position(event)
        self.scene.clear_selected_models()

        for model in self.scene.models:
            if model.intersection_ray_bounding_sphere(self.ray_start, self.ray_end):
                possible_hit.append(model)
                nSelected+=1

        if not nSelected:
            return False

        for model in possible_hit:
            if model.intersection_ray_model(self.ray_start, self.ray_end):
                model.selected = True
                return True

        return False

#    @timing
    def hit_tool_button_by_color(self, event):
        color = self.view.get_cursor_pixel_color(event)
        find_id = color[0] + (color[1]*256) + (color[2]*256*256)
        if find_id == 0:
            return False
        for toolButton in self.view.get_tool_buttons():
            if find_id == toolButton.id:
                if toolButton.pressed:
                    toolButton.unpress_button()
                else:
                    for t in self.view.get_tool_buttons():
                        t.unpress_button()
                    toolButton.press_button()
                    toolButton.run_callback()


    def hit_first_object_by_color(self, event):
        self.scene.clear_selected_models()
        color = self.view.get_cursor_pixel_color(event)
        #color to id
        find_id = color[0] + (color[1]*256) + (color[2]*256*256)
        if find_id == 0:
            return False
        for model in self.scene.models:
            if model.id == find_id:
                model.selected = True
                return True



    def find_object_and_rotation_axis_by_color(self, event):
        color = self.view.get_cursor_pixel_color(event)
        #color to id
        find_id = color[0] + (color[1]*256) + (color[2]*256*256)
        if find_id == 0:
            return False
        for model in self.scene.models:
            if model.rotateXId == find_id:
                model.selected = True
                model.rotationAxis = 'x'
                return True
            elif model.rotateYId == find_id:
                model.selected = True
                model.rotationAxis = 'y'
                return True
            elif model.rotateZId == find_id:
                model.selected = True
                model.rotationAxis = 'z'
                return True
            else:
                model.rotationAxis = []


    def find_object_and_scale_axis_by_color(self, event):
        color = self.view.get_cursor_pixel_color(event)
        #color to id
        find_id = color[0] + (color[1]*256) + (color[2]*256*256)
        if find_id == 0:
            return False
        for model in self.scene.models:
            if model.scaleXId == find_id:
                model.selected = True
                model.scaleAxis = 'x'
                return True
            elif model.scaleYId == find_id:
                model.selected = True
                model.scaleAxis = 'y'
                return True
            elif model.scaleZId == find_id:
                model.selected = True
                model.scaleAxis = 'z'
                return True
            elif model.scaleXYZId == find_id:
                model.selected = True
                model.scaleAxis = 'xyz'
                return True
            else:
                model.scaleAxis = None

    def reset_scene(self):
        self.scene.clearScene()
        self.view.update_scene(True)

    def import_image(self, path):
        #TODO:Add importing of image(just plane with texture?)
        pass

    def select_button_pressed(self):
        self.clear_tool_button_states()
        self.settings['toolButtons']['moveButton'] = True
        self.view.update_scene()

    def move_button_pressed(self):
        self.clear_tool_button_states()
        self.settings['toolButtons']['moveButton'] = True
        self.view.update_scene()

    def rotate_button_pressed(self):
        self.clear_tool_button_states()
        self.settings['toolButtons']['rotateButton'] = True
        self.view.update_scene()

    def scale_button_pressed(self):
        self.clear_tool_button_states()
        self.settings['toolButtons']['scaleButton'] = True
        self.view.update_scene()

    def clear_tool_button_states(self):
        self.settings['toolButtons'] = {a: False for a in self.settings['toolButtons']}


    def open_file(self, url):
        '''
        function for resolve which file type will be loaded
        '''
        #self.view.statusBar().showMessage('Load file name: ')

        urlSplited = url.split('.')
        if len(urlSplited)>1:
            fileEnd = urlSplited[1]
        else:
            fileEnd=''

        if fileEnd in ['stl', 'STL', 'Stl']:
            print('import model')
            self.import_model(url)
        elif fileEnd in ['prus']:
            print('open project')
            self.open_project_file(url)
        elif fileEnd in ['jpeg', 'jpg', 'png', 'bmp']:
            print('import image')
            self.import_image(url)




