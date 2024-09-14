#!/usr/bin/env python
'''
Utilities to generate MaterialX color transform definitions using OCIO.

The minimum requirement is OCIO version 2.2 which is packaged with
ACES Cg Config` and `ACES Studio Config` configurations.
'''

import PyOpenColorIO as OCIO
import MaterialX as mx
import re

class OCIOMaterialaxGenerator():
    '''
    A class to generate MaterialX color transform definitions using OCIO.
    '''

    def getBuiltinConfigs(self):
        '''
        Get the OCIO built in configurations.
        Returnes a dictionary of color spaces and the default `ACES Cg Config`.
        '''

        # As of version 2.2, `ACES Cg Config` and `ACES Studio Config` are packaged with `OCIO`, meaning that 
        # they are available to use without having to download them separately. The `getBuiltinConfigs()` 
        # API is explained [here](https://opencolorio.readthedocs.io/en/latest/releases/ocio_2_2.html)

        # Get the OCIO built in configs
        registry = OCIO.BuiltinConfigRegistry().getBuiltinConfigs()

        # Create a dictionary of configs
        configs = {}
        for item in registry:
            # The short_name is the URI-style name.
            # The ui_name is the name to use in a user interface.
            short_name, ui_name, isRecommended, isDefault = item

            # Don't present built-in configs to users if they are no longer recommended.
            if isRecommended:
                # Create a config using the Cg config
                config = OCIO.Config.CreateFromBuiltinConfig(short_name)
                colorSpaces = None
                if config:
                    colorSpaces = config.getColorSpaces()

                if colorSpaces:
                    configs[short_name] = [config, colorSpaces]

        acesCgConfigPath = 'ocio://cg-config-v1.0.0_aces-v1.3_ocio-v2.1'
        builtinCfgC = OCIO.Config.CreateFromFile(acesCgConfigPath)
        print('Built-in config:', builtinCfgC.getName())
        csnames = builtinCfgC.getColorSpaceNames()
        print('- Number of color spaces: %d' % len(csnames))

        return configs, builtinCfgC

    def printConfigs(self, configs):
        title = '| Configuration | Color Space | Aliases |\n'
        title = title + '| --- | --- | --- |\n'

        rows = ''
        for c in configs:
            config = configs[c][0]
            colorSpaces = configs[c][1]
            for colorSpace in colorSpaces:
                aliases = colorSpace.getAliases()
                rows = rows + '| ' + c + ' | ' + colorSpace.getName() + ' | ' + ', '.join(aliases) + ' |\n'

        return title + rows

    def createTransformName(self, sourceSpace, targetSpace, typeName, prefix = 'mx_'):
        '''
        Create a transform name from a source and target color space and a type name.
        @param sourceSpace: The source color space.
        @param targetSpace: The target color space.
        @param typeName: The type name.
        @param prefix: The prefix for the transform name. Default is 'mx_'.
        '''        
        transformFunctionName = prefix + mx.createValidName(sourceSpace) + "_to_" + mx.createValidName(targetSpace) + "_" + typeName 
        return transformFunctionName

    def setShaderDescriptionParameters(self, shaderDesc, sourceSpace, targetSpace, typeName):
        '''
        '''
        transformFunctionName = self.createTransformName(sourceSpace, targetSpace, typeName)
        shaderDesc.setFunctionName(transformFunctionName)
        shaderDesc.setResourcePrefix(transformFunctionName)

    def generateShaderCode(self, config, sourceColorSpace, destColorSpace, language):
        '''
        Generate shader for a transform from a source color space to a destination color space
        for a given config and shader language.

        Returns the shader code and the number of texture resources required.
        '''
        shaderCode = ''
        textureCount = 0
        if not config:
            return shaderCode, textureCount

        # Create a processor for a pair of colorspaces
        processor = None
        try:
            processor = config.getProcessor(sourceColorSpace, destColorSpace)
        except:
            print('Failed to generated code for transform: %s -> %s' % (sourceColorSpace, destColorSpace))
            return shaderCode, textureCount

        if processor:
            gpuProcessor = processor.getDefaultGPUProcessor()
            if gpuProcessor:
                shaderDesc = OCIO.GpuShaderDesc.CreateShaderDesc()
                if shaderDesc:
                    try:
                        shaderDesc.setLanguage(language)
                        if shaderDesc.getLanguage() == language:
                            self.setShaderDescriptionParameters(shaderDesc, sourceColorSpace, destColorSpace, "color4")
                            gpuProcessor.extractGpuShaderInfo(shaderDesc)                                                                 
                            shaderCode = shaderDesc.getShaderText()

                            for t in shaderDesc.getTextures():
                                textureCount += 1

                            if shaderCode:
                                shaderCode = shaderCode.replace(
                                    "// Declaration of the OCIO shader function\n", 
                                    "// " + sourceColorSpace + " to " + destColorSpace + " function. Texture count: %d\n" % textureCount)

                    except OCIO.Exception as err:
                        print(err)
        
        return shaderCode, textureCount
    
    def generateTransformGraph(self, config, sourceColorSpace, destColorSpace):
        '''
        Generate the group of transforms required to go from a source color space to a destination color space.
        The group of transforms is output from an optimized OCIO processor. 
        @param config: The OCIO configuration.
        @param sourceColorSpace: The source color space.
        @param destColorSpace: The destination color space.
        @return: The group of transforms.
        '''
        if not config:
            return None

        # Create a processor for a pair of colorspaces (namely to go to linear)
        processor = None
        groupTransform = None
        try:
            processor = config.getProcessor(sourceColorSpace, destColorSpace)
        except:
            #print('Failed to get processor for: %s -> %s' % (sourceColorSpace, destColorSpace))
            return groupTransform

        if processor:
            processor = processor.getOptimizedProcessor(OCIO.OPTIMIZATION_ALL) 
            groupTransform = processor.createGroupTransform()
        
        return groupTransform    

    def hasTextureResources(self, configs, targetColorSpace, language):
        '''
        Scan through all the color spaces on the configs to check for texture resource usage.
        Returns a set of color spaces that require texture resources.
        '''
        testedSources = set()
        textureSources = set()
        for c in configs:
            config = OCIO.Config.CreateFromBuiltinConfig(c)
            colorSpaces = config.getColorSpaces()
            for colorSpace in colorSpaces:
                colorSpaceName = colorSpace.getName()
                # Skip if the colorspace is already tested
                if colorSpaceName in testedSources:
                    continue
                testedSources.add(colorSpaceName)

                # Test for texture resource usage
                code, textureCount = self.generateShaderCode(config, colorSpace.getName(), targetColorSpace, language)
                if textureCount:
                    print('- Transform "%s" to "%s" requires %d texture resources' % (colorSpace.getName(), targetColorSpace, textureCount))
                    textureSources.add(colorSpaceName)
        
        return textureSources

    def MSL(self, config, sourceColorSpace, targetColorSpace):
        language = OCIO.GpuLanguage.GPU_LANGUAGE_MSL_2_0
        code, textureCount = self.generateShaderCode(config, sourceColorSpace, targetColorSpace, language)
        if code:
            code = code.replace("// Declaration of the OCIO shader function\n", "// " + sourceColorSpace + " to " + targetColorSpace + " function\n")
            code = '```c++\n' + code + '\n```\n'

    def OSL(self, config, sourceColorSpace, targetColorSpace):
        if OCIO.GpuLanguage.LANGUAGE_OSL_1:
            language = OCIO.GpuLanguage.LANGUAGE_OSL_1
            code, textureCount = self.generateShaderCode(config, sourceColorSpace, targetColorSpace, language)
            if code:
                # Bit of ugly patching to make the main function name consistent.
                transformName = self.createTransformName(sourceColorSpace, targetColorSpace, 'color4')
                code = code.replace('OSL_' + transformName, '__temp_name__')
                code = code.replace(transformName, transformName + '_impl')
                code = code.replace('__temp_name__', transformName)
                code = code.replace("// Declaration of the OCIO shader function\n", "// " + sourceColorSpace + " to " + targetColorSpace + " function\n")
                code = '```c++\n' + code + '\n```\n'

    def generateMaterialXDefinition(self, doc, sourceColorSpace, targetColorSpace, inputName, type):
        '''
        Create a new definition in a document for a given color space transform.
        Returns the definition.
        '''
        # Create a definition
        transformName = self.createTransformName(sourceColorSpace, targetColorSpace, type)
        nodeName = transformName.replace('mx_', 'ND_')

        comment = doc.addChildOfCategory('comment')
        docString = ' Color space %s to %s transform. Generated via OCIO. ' % (sourceColorSpace, targetColorSpace)
        comment.setDocString(docString)

        definition = doc.addNodeDef(nodeName, 'color4')
        category = sourceColorSpace + '_to_' + targetColorSpace
        definition.setNodeString(category)
        definition.setNodeGroup('colortransform')
        definition.setDocString(docString)
        definition.setVersionString('1.0')

        defaultValueString = '0.0 0.0 0.0 1.0'
        defaultValue = mx.createValueFromStrings(defaultValueString, 'color4')
        input = definition.addInput(inputName, type)
        input.setValue(defaultValue)
        output = definition.getOutput('out')
        output.setAttribute('default', 'in')

        return definition

    def writeShaderCode(self, outputPath, code, transformName, extension, target):
        '''
        Write the shader code to a file.
        '''   
        # Write source code file
        filename = outputPath / mx.FilePath(transformName + '.' + extension)
        print('Write target[%s] source file %s' % (target,filename.asString()))
        f = open(filename.asString(), 'w')
        f.write(code)
        f.close()

    def createMaterialXImplementation(self, sourceColorSpace, targetColorSpace, doc, definition, transformName, extension, target):
        '''
        Create a new implementation in a document for a given definition.
        '''
        implName = transformName + '_' + target
        filename = transformName + '.' + extension
        implName = implName.replace('mx_', 'IM_')

        # Check if implementation already exists
        impl = doc.getImplementation(implName)
        if impl:
            print('Implementation already exists: %s' % implName)
            return impl

        comment = doc.addChildOfCategory('comment')
        comment.setDocString(' Color space %s to %s transform. Generated via OCIO for target: %s' 
                            % (sourceColorSpace, targetColorSpace, target))
        impl = doc.addImplementation(implName)
        impl.setFile(filename)
        impl.setFunction(transformName)
        impl.setTarget(target)
        impl.setNodeDef(definition)

        return impl

    def generateOCIO(self, config, definitionDoc, implDoc, sourceColorSpace = 'acescg', targetColorSpace = 'lin_rec709',
                    type='color4', IN_PIXEL_STRING = 'in'):
        '''
        Generate a MaterialX definition and implementation for a given color space transform.    
        Returns the definition, implementation, source code, extension and target.
        '''

        # List of MaterialX target language, source code extensions, and OCIO GPU languages
        generationList = [
            ['genglsl', 'glsl', OCIO.GpuLanguage.GPU_LANGUAGE_GLSL_4_0]
            #, ['genmsl', 'metal', OCIO.GpuLanguage.GPU_LANGUAGE_MSL_2_0]
            ]

        definition = None
        transformName = self.createTransformName(sourceColorSpace, targetColorSpace, type)
        for gen in generationList:
            target = gen[0]
            extension = gen[1]
            language = gen[2]

            code, textureCount = self.generateShaderCode(config, sourceColorSpace, targetColorSpace, language)

            # Skip if there are texture resources
            if textureCount:
                print('- Skip generation for transform: "%s" to "%s" which requires %d texture resources' % (sourceColorSpace, targetColorSpace, textureCount))
                continue

            if code:
                # Create the definition once
                if not definition:
                    # Create color4 variant
                    definition = self.generateMaterialXDefinition(definitionDoc, sourceColorSpace, targetColorSpace, 
                                                            IN_PIXEL_STRING, type)
                    # Create color3 variant (nodegraph)
                    self.createColor3Variant(definition, definitionDoc, IN_PIXEL_STRING)
                
                # Create the implementation
                self.createMaterialXImplementation(sourceColorSpace, targetColorSpace, implDoc, definition, transformName, extension, target)

        return definition, transformName, code, extension, target     
    
    def generateOCIOGraph(self, config, sourceColorSpace = 'acescg', targetColorSpace = 'lin_rec709',
                          type='color3'):
        '''
        Generate a MaterialX nodegraph for a given color space transform.
        @param config: The OCIO configuration.
        @param sourceColorSpace: The source color space.
        @param targetColorSpace: The destination color space.
        @param type: The type of the transform.
        Returns a MaterialX document containing a functional nodegraph and nodedef pair.
        '''
        groupTransform = self.generateTransformGraph(config, sourceColorSpace, targetColorSpace)

        # To add. Proper testing of unsupported transforms...
        invalidTransforms = [ OCIO.TransformType.TRANSFORM_TYPE_LUT3D, OCIO.TransformType.TRANSFORM_TYPE_LUT1D, 
                              OCIO.TransformType.TRANSFORM_TYPE_GRADING_PRIMARY ]

        # Create a document, a nodedef and a functional graph.
        graphDoc = mx.createDocument()
        outputType = 'color3'
        xformName = sourceColorSpace + '_to_' + targetColorSpace + '_' + outputType
        
        nd = graphDoc.addNodeDef('ND_' + xformName )
        nd.setAttribute('node', xformName)
        ndInput = nd.addInput('in', 'color3')
        ndInput.setValue([0.0, 0.0, 0.0], 'color3')
        docString = f'Generated color space {sourceColorSpace} to {targetColorSpace} transform.'
        result = f'{groupTransform}'
        # Replace '<' and '>' with '()' and ')'
        result = result.replace('<', '(')
        result = result.replace('>', ')')
        result = re.sub(r'[\r\n]+', '', result)

        print(result)
        docString = docString + '. OCIO Transforms: ' + result 
        nd.setDocString(docString)

        ng = graphDoc.addNodeGraph('NG_' + xformName)
        ng.setAttribute('nodedef', nd.getName())
        convertNode = ng.addNode('convert', 'asVec', 'vector3')
        converInput = convertNode.addInput('in', 'color3')
        converInput.setInterfaceName('in')

        #print(f'Transform from: {sourceColorSpace} to {targetColorSpace}')
        if not groupTransform:
            #print(f'No group transform found for the color space transform: {sourceColorSpace} to {targetColorSpace}')
            return None
        #print(f'Number of transforms: {groupTransform.__len__()}')
        previousNode = None

        # Iterate and create appropriate nodes and connections
        for i in range(groupTransform.__len__()):
            transform = groupTransform.__getitem__(i)
            # Get type of transform
            transformType = transform.getTransformType()
            if transformType in invalidTransforms:
                print(f'- Transform[{i}]: {transformType} contains an unsupported transform type')
                continue

            #print(f'- Transform[{i}]: {transformType}')   
            if transformType == OCIO.TransformType.TRANSFORM_TYPE_MATRIX:
                matrixNode = ng.addNode('transform', ng.createValidChildName(f'matrixTransform'), 'vector3')

                # Route output from previous node as input of current node
                inInput = matrixNode.addInput('in', 'vector3')
                if previousNode:            
                    inInput.setAttribute('nodename', previousNode)
                else:
                    #if i==0:
                        inInput.setAttribute('nodename', 'asVec')
                    #else:
                    #    inInput.setValue([0.0, 0.0, 0.0], 'vector3')

                # Set matrix value
                matInput = matrixNode.addInput('mat', 'matrix33')
                matrixValue = transform.getMatrix()
                # Extract 3x3 matrix from 4x4 matrix
                matrixValue = matrixValue[0:3] + matrixValue[4:7] + matrixValue[8:11]
                matrixValue = ', '.join([str(x) for x in matrixValue])
                #print('  - Matrix:', matrixValue)
                matInput.setAttribute('value', matrixValue)        

                # Add offset value - TODO
                offsetValue = transform.getOffset()
                offsetValue = ', '.join([str(x) for x in offsetValue])
                #print('  - Offset:', offsetValue)
                # Add a add vector3 to graph

                previousNode = matrixNode.getName()
            
            # TODO: Handle other transform types
            elif transformType == OCIO.TransformType.TRANSFORM_TYPE_EXPONENT or transformType == OCIO.TransformType.TRANSFORM_TYPE_EXPONENT_WITH_LINEAR:

                hasOffset = (transformType == OCIO.TransformType.TRANSFORM_TYPE_EXPONENT_WITH_LINEAR)

                #print(f'- Transform[{i}]: {transformType} support has not been implemented yet')
                exponentNode = ng.addNode('power', ng.createValidChildName(f'exponent'), 'vector3')
                exponentInput = exponentNode.addInput('in1', 'vector3')
                if previousNode:
                    exponentInput.setAttribute('nodename', previousNode)
                else:
                    if i==0:
                        exponentInput.setAttribute('nodename', 'asVec')
                    else:
                        exponentInput.setValue([0.0, 0.0, 0.0], 'vector3')

                exponentInput2 = exponentNode.addInput('in2', 'vector3')
                exponentInput2Value = None
                if not hasOffset:
                    exponentInput2Value = transform.getValue()
                else:
                    exponentInput2Value = transform.getGamma()
                # Only want the first 3 values in the array
                exponentInput2Value = exponentInput2Value[0:3]
                exponentInput2.setValue(exponentInput2Value, 'float')

                previousNode = exponentNode.getName()

                if hasOffset:
                    # Add offset
                    offsetNode = ng.addNode('add', ng.createValidChildName(f'offset'), 'vector3')
                    offsetInput2 = offsetNode.addInput('in2', 'vector3')
                    offsetInput2.setNodeName(exponentNode.getName())
                    offsetInput = offsetNode.addInput('in1', 'vector3')
                    offsetValue = transform.getOffset()
                    # Only want the first 3 values in the array
                    offsetValue = offsetValue[0:3]
                    offsetInput.setValue(offsetValue, 'vector3')

                    previousNode = offsetNode.getName()

            else:
                print(f'- Transform[{i}]: {transformType} support has not been implemented yet')
                continue


        # Create an output for the last node if any
        convertNode2 = ng.addNode('convert', 'asColor', 'color3')
        converInput2 = convertNode2.addInput('in', 'vector3')
        if previousNode:
            converInput2.setAttribute('nodename', previousNode)
        else:
            # Pass-through
            #print('No transforms applied. Transform is a pass-through.')
            converInput2.setAttribute('nodename', 'asVec')

        out = ng.addOutput(ng.createValidChildName('out'), 'color3')
        out.setAttribute('nodename', 'asColor')

        return graphDoc

    def createColor3Variant(self, definition, definitionDoc, IN_PIXEL_STRING = 'in'):
        '''
        Create a color3 variant of a color4 definition.
        '''
        color4Name = definition.getName()
        color3Name = color4Name.replace('color4', 'color3')
        color3Def = definitionDoc.addNodeDef(color3Name)
        color3Def.copyContentFrom(definition)
        c3input = color3Def.getInput(IN_PIXEL_STRING)
        c3input.setType('color3')
        c3input.setValue([0.0, 0.0, 0.0], 'color3')
            
        ngName = color3Def.getName().replace('ND_', 'NG_')
        ng = definitionDoc.addNodeGraph(ngName)
        c4instance = ng.addNodeInstance(definition)
        c4instance.addInputsFromNodeDef()
        c4instanceIn = c4instance.getInput(IN_PIXEL_STRING)
        c3to4 = ng.addNode('convert', 'c3to4', 'color4')
        c3to4Input = c3to4.addInput('in', 'color3')
        c4to3 = ng.addNode('convert', 'c4to3', 'color3')
        c4to3Input = c4to3.addInput('in', 'color4')
        ngout = ng.addOutput('out', 'color3')
        #ngin = ng.addInput('in', 'color3')
        ng.setNodeDef(color3Def)

        c4instanceIn.setNodeName(c3to4.getName())
        c4to3Input.setNodeName(c4instance.getName())
        ngout.setNodeName(c4to3.getName())
        c3to4Input.setInterfaceName(IN_PIXEL_STRING)