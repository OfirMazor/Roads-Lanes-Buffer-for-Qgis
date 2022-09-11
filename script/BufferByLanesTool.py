# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

# Libraries
from qgis.PyQt.QtCore import QCoreApplication
from qgis.processing import run as QgisRun
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessingParameterVectorDestination as ParameterVectorDestination,
                       QgsProcessingParameterFeatureSource as ParameterFeatureSource,
                       QgsProcessingParameterNumber as ProcessingParameterNumber,
                       QgsProcessingAlgorithm as ProcessingAlgorithm,
                       QgsCoordinateReferenceSystem as QgisCRS,
                       QgsProcessing,
                       QgsProperty)




class BufferByLanes(ProcessingAlgorithm):
    """
    Class defination of the algorithm tool
    """

    InputLineLayer      = 'InputLineLayer'
    Lane_Weight         = 'Lane_Weight'
    OutputRoadLayer     = 'OutputRoadLayer'
    Sidewalk_distance   = 'Sidewalk_distance'
    OutputSidewalkLayer = 'OutputSidewalkLayer'



    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Returns the class instance.
        """
        return BufferByLanes()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return 'Buffer By Lanes'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Buffer By Lanes')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Road Tools')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'Paved & Unpaved Roads'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. 
        """
        ToolHelp = '''
                    The algorithm takes line geometry layer with 2 numeric columns of lanes number (FT, TF) as weights for and side-buffering the lines where each side get it's weight.
                    In addition, a new layer of sidewalk, for each road, is been calculated.
                   |
                   |
                    Parameters:
                        
                        - Input Line Layer : Line geometry file, the must contains numeric fields of lanes as "FT" & "TF".
                        
                        - Lane Weight : The distance to multiply a lane field by (Defualt is 2.5).
                        
                        - Output Road layer : Polygon geometry file as algorithm roads output.
                        
                        - Output Sidewalk Layer : Polygon geometry file as algorithm  sidewalk output (Defualt is 2.5)."
                        
                        |
                        |
                        |
                        |
                        |
                    Developed by Ofir Mazor (ofir@mapi.gov.il)
                    https://github.com/OfirMazor/Roads-Lanes-Buffer-for-Qgis
                    '''
                        
        return self.tr(ToolHelp)
        
    def icon(self):
        return QIcon('https://github.com/OfirMazor/Roads-Lanes-Buffer-for-Qgis/blob/main/Logo/buffer-svgrepo-com.svg')



    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm.
        """
        
        # Input line geometry layer
        self.addParameter(ParameterFeatureSource(name = self.InputLineLayer,
                                                 description = self.tr('Input Line Layer'),
                                                 types = [QgsProcessing.TypeVectorLine],
                                                 optional = False))
        
        
        #Lanes weight
        self.addParameter(ProcessingParameterNumber(name = self.Lane_Weight,
                                                    description = self.tr('Lane Weight'),
                                                    type = ProcessingParameterNumber.Double,
                                                    defaultValue = 2.5,
                                                    optional = True))

        #Output Road Layer
        self.addParameter(ParameterVectorDestination(name = self.OutputRoadLayer,
                                                     description = self.tr('Output Road layer'),
                                                     optional = False))
                                                     
        #Sidewalk width                                            
        self.addParameter(ProcessingParameterNumber(name = self.Sidewalk_distance,
                                                    description = self.tr('Sidewalk Width'),
                                                    type = ProcessingParameterNumber.Double,
                                                    defaultValue = 2.5,
                                                    optional = True))
        #Output SideWalk Layer                                            
        self.addParameter(ParameterVectorDestination(name = self.OutputSidewalkLayer,
                                                     description = self.tr('Output Sidewalk Layer'),
                                                     optional = False))



    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        
        lane_weight = self.parameterAsDouble(parameters, self.Lane_Weight, context)
        
        FromTo_paramas = {'INPUT'        : parameters[self.InputLineLayer],
                          'FIELD_NAME'      : 'WFT_LANES',
                          'FIELD_TYPE'      : 0,    #float type
                          'FIELD_LENGTH'    : 4,
                          'FIELD_PRECISION' : 4,
                          'FORMULA'         : f'"FT_LANES" * {lane_weight}',
                          'OUTPUT'          : 'memory:'}
        FT_weights = QgisRun("native:fieldcalculator", FromTo_paramas, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']


        ToFrom_params = {'INPUT'         : FT_weights,
                         'FIELD_NAME'       : 'WTF_LANES',
                         'FIELD_TYPE'       : 0,    #float type
                         'FIELD_LENGTH'     : 4,
                         'FIELD_PRECISION'  : 4,
                         'FORMULA'          : f'"TF_LANES" * {lane_weight}',
                         'OUTPUT'           : 'memory:'}
        weights_layer = QgisRun("native:fieldcalculator", ToFrom_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']
        
        
        right_buffer_params = {'INPUT'       : weights_layer,
                               'DISTANCE'    : QgsProperty.fromExpression('"WFT_LANES"'),
                               'SIDE'        : 1,       #right,
                               'SEGMENTS'    : 8,
                               'JOIN_STYLE'  : 0,
                               'MITER_LIMIT' : 2,
                               'OUTPUT'      : 'memory:'}
        right_buffer = QgisRun("native:singlesidedbuffer", right_buffer_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']

        
        left_buffer_params = {'INPUT'       : weights_layer,
                              'DISTANCE'    : QgsProperty.fromExpression('"WTF_LANES"'),
                              'SIDE'        : 0,       #Left,
                              'SEGMENTS'    : 8,
                              'JOIN_STYLE'  : 0,
                              'MITER_LIMIT' : 2,
                              'OUTPUT'      : 'memory:'}
        left_buffer = QgisRun("native:singlesidedbuffer", left_buffer_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']
        
        
        merge_params = {'LAYERS' : [left_buffer, right_buffer],
                        'CRS'    : QgisCRS('EPSG:2039'),
                        'OUTPUT' : 'memory:'}
        merged = QgisRun("native:mergevectorlayers", merge_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']


        dissolve_params = {'INPUT'  : merged,
                           'FIELD'  : ['UNIQ_ID'],
                           'OUTPUT' : 'memory:'}
        dissolved = QgisRun("native:dissolve", dissolve_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']
        
        
        deletecolumn_params = {'INPUT'  : dissolved,
                               'COLUMN' : ["layer", "path", "WFT_LANES", "WTF_LANES"],
                               'OUTPUT' : parameters[self.OutputRoadLayer]}
        Road_results = QgisRun("qgis:deletecolumn", deletecolumn_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']
        
        
        sidewalk_buffer_params = {'INPUT'         : Road_results,
                                  'DISTANCE'      : parameters[self.Sidewalk_distance],
                                  'SEGMENTS'      : 5,
                                  'END_CAP_STYLE' : 1,#Flat style
                                  'JOIN_STYLE'    : 1,#Miter style
                                  'MITER_LIMIT'   : 2,
                                  'DISSOLVE'      : True, 
                                  'OUTPUT'        : 'memory:'}
        sidewalk_buffer = QgisRun("native:buffer", sidewalk_buffer_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']

        difference_params = {'INPUT'   : sidewalk_buffer,
                             'OVERLAY' : Road_results,
                             'OUTPUT'  : parameters[self.OutputSidewalkLayer]}
        SideWalk_results = QgisRun("native:difference", difference_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']
        
        
        
        
        return {self.OutputRoadLayer     : Road_results,
                self.OutputSidewalkLayer : SideWalk_results}
        
        
        