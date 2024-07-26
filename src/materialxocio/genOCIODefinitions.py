#!/usr/bin/env python
'''
Utility to generate MaterialX color transform definitions using OCIO.

The minimum requirement is OCIO version 2.2 which is packaged with
ACES Cg Config` and `ACES Studio Config` configurations.

The script will generate MaterialX definitions for all color spaces found in the
ACES Cg Config` and `ACES Studio Config` configurations. The definitions will be
generated for the following MaterialX targets:
    - GLSL

The output script will is:
1. A markdown file with information about the built-in configurations.
2. A color4 implementation file containing the source code generated by OCIO.
3. A color3 node graph implementation which uses the color4 implementation (nodegraph)  
4. A file with both color3 and color4 MaterialX definitions (nodedef).
5. A MaterialX file containing implementation declarations for color3 and color4 variants. 
'''

import sys, os, argparse
import PyOpenColorIO as OCIO
import MaterialX as mx

def getBuiltinConfigs():
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

def printConfigs(configs):
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

def createTransformName(sourceSpace, targetSpace, typeName):
    '''
    Create a transform name from a source and target color space and a type name.
    '''        
    transformFunctionName = "mx_" + mx.createValidName(sourceSpace) + "_to_" + mx.createValidName(targetSpace) + "_" + typeName 
    return transformFunctionName

def setShaderDescriptionParameters(shaderDesc, sourceSpace, targetSpace, typeName):
    '''
    '''
    transformFunctionName = createTransformName(sourceSpace, targetSpace, typeName)
    shaderDesc.setFunctionName(transformFunctionName)
    shaderDesc.setResourcePrefix(transformFunctionName)

def generateShaderCode(config, sourceColorSpace, destColorSpace, language):
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
                        setShaderDescriptionParameters(shaderDesc, sourceColorSpace, destColorSpace, "color4")
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

def hasTextureResources(configs, targetColorSpace, language):
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
            code, textureCount = generateShaderCode(config, colorSpace.getName(), targetColorSpace, language)
            if textureCount:
                print('- Transform "%s" to "%s" requires %d texture resources' % (colorSpace.getName(), targetColorSpace, textureCount))
                textureSources.add(colorSpaceName)
    
    return textureSources

def MSL(config, sourceColorSpace, targetColorSpace):
    language = OCIO.GpuLanguage.GPU_LANGUAGE_MSL_2_0
    code, textureCount = generateShaderCode(config, sourceColorSpace, targetColorSpace, language)
    if code:
        code = code.replace("// Declaration of the OCIO shader function\n", "// " + sourceColorSpace + " to " + targetColorSpace + " function\n")
        code = '```c++\n' + code + '\n```\n'

def OSL(config, sourceColorSpace, targetColorSpace):
    if OCIO.GpuLanguage.LANGUAGE_OSL_1:
        language = OCIO.GpuLanguage.LANGUAGE_OSL_1
        code, textureCount = generateShaderCode(config, sourceColorSpace, targetColorSpace, language)
        if code:
            # Bit of ugly patching to make the main function name consistent.
            transformName = createTransformName(sourceColorSpace, targetColorSpace, 'color4')
            code = code.replace('OSL_' + transformName, '__temp_name__')
            code = code.replace(transformName, transformName + '_impl')
            code = code.replace('__temp_name__', transformName)
            code = code.replace("// Declaration of the OCIO shader function\n", "// " + sourceColorSpace + " to " + targetColorSpace + " function\n")
            code = '```c++\n' + code + '\n```\n'

def generateMaterialXDefinition(doc, sourceColorSpace, targetColorSpace, inputName, type):
    '''
    Create a new definition in a document for a given color space transform.
    Returns the definition.
    '''
    # Create a definition
    transformName = createTransformName(sourceColorSpace, targetColorSpace, type)
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

def writeShaderCode(outputPath, code, transformName, extension, target):
    '''
    Write the shader code to a file.
    '''   
    # Write source code file
    filename = outputPath / mx.FilePath(transformName + '.' + extension)
    print('Write target[%s] source file %s' % (target,filename.asString()))
    f = open(filename.asString(), 'w')
    f.write(code)
    f.close()

def createMaterialXImplementation(sourceColorSpace, targetColorSpace, doc, definition, transformName, extension, target):
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

def generateOCIO(config, definitionDoc, implDoc, sourceColorSpace = 'acescg', targetColorSpace = 'lin_rec709',
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
    transformName = createTransformName(sourceColorSpace, targetColorSpace, type)
    for gen in generationList:
        target = gen[0]
        extension = gen[1]
        language = gen[2]

        code, textureCount = generateShaderCode(config, sourceColorSpace, targetColorSpace, language)

        # Skip if there are texture resources
        if textureCount:
            print('- Skip generation for transform: "%s" to "%s" which requires %d texture resources' % (sourceColorSpace, targetColorSpace, textureCount))
            continue

        if code:
            # Create the definition once
            if not definition:
                # Create color4 variant
                definition = generateMaterialXDefinition(definitionDoc, sourceColorSpace, targetColorSpace, 
                                                        IN_PIXEL_STRING, type)
                # Create color3 variant (nodegraph)
                createColor3Variant(definition, definitionDoc, IN_PIXEL_STRING)
            
            # Create the implementation
            createMaterialXImplementation(sourceColorSpace, targetColorSpace, implDoc, definition, transformName, extension, target)

    return definition, transformName, code, extension, target     

def createColor3Variant(definition, definitionDoc, IN_PIXEL_STRING = 'in'):
    '''
    Create a color3 variant of a color4 definition.
    '''
    color4Name = definition.getName()
    color3Name = color4Name.replace('color4', 'color3')
    color3Def = definitionDoc.addNodeDef(color3Name)
    color3Def.copyContentFrom(definition)
    c3input = color3Def.getInput(IN_PIXEL_STRING)
    c3input.setType('color3')
    c3input.setValue(mx.createValueFromStrings('0.0 0.0 0.0', 'color3'))
        
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

def main():
    parser = argparse.ArgumentParser(description="Create Materialx definitions using OCIO.")
    parser.add_argument('--outputPath', dest='outputPath', help='File path to output material files to.')

    opts = parser.parse_args()
    outputPath = mx.FilePath("./OCIO_output/")
    if opts.outputPath:
        outputPath = mx.FilePath(opts.outputPath)

    # Check OCIO version
    ver = OCIO.GetVersion()
    ocioVersion = ver.split('.')
    if len(ocioVersion) < 2:
        print('OCIO version is not in the expected format.')
        return
    if int(ocioVersion[0]) < 2 or int(ocioVersion[1]) < 2:
        print('OCIO version 2.2 or greater is required.')
        return
    
    print('OCIO version:', ver)
    print('MaterialX version:', mx.getVersionString())

    # Get the OCIO built in configs and write out the configuration information
    # to a markdown file.
    configs, aconfig = getBuiltinConfigs()
    md = printConfigs(configs)
    # Save configuration information as markdown
    configInfoFile = outputPath / mx.FilePath('OCIO_configurations.md')
    print('Write out OCIO configurations to: ' + configInfoFile.asString())
    f = open(configInfoFile.asString(), 'w')
    f.write(md)

    sourceColorSpace = "acescg"
    targetColorSpace = 'lin_rec709'

    # All code has the same input name
    # It is possible to use a different name than the name used in the generated function ('inPixel')
    IN_PIXEL_STRING = 'in'

    # Generate MaterialX definitions and implementations for all color spaces
    # found in the ACES Cg Config and ACES Studio Config configurations.
    for c in configs:
        config = configs[c][0]
        for colorSpace in config.getColorSpaces():
            aliases = colorSpace.getAliases()
            trySource = ''
            for alias in aliases:
                # Get alias if it does not contain a space
                if ' ' not in alias:
                    trySource = alias
            if not trySource:
                trySource = colorSpace.getName()
            if trySource:
                sourceColorSpace = trySource

                # Skip if the source and target are the same
                if sourceColorSpace == targetColorSpace:
                    continue

                print('--- Generate transform for source color space:', trySource, '---')

                definitionDoc = mx.createDocument()
                implDoc = mx.createDocument()

                definition, transformName, code, extension, target = generateOCIO(aconfig, definitionDoc, implDoc, sourceColorSpace, targetColorSpace, 'color4')

                # Write the definition, implementation and source code files 
                if definition:

                    filename = outputPath / mx.FilePath(definition.getName() + '.' + 'mtlx')
                    print('Write MaterialX definition file:', filename.asString())
                    mx.writeToXmlFile(definitionDoc, filename)

                    # Write the implementation document
                    implFileName = outputPath / mx.FilePath('IM_' + transformName + '.' + 'mtlx')
                    print('Write MaterialX implementation file:', implFileName.asString())
                    result = mx.writeToXmlFile(implDoc, implFileName)

                    writeShaderCode(outputPath, code, transformName, extension, target)

            else:
                print('Could not find suitable color space name to use: ', colorSpace.getName())


if __name__ == '__main__':
    main()