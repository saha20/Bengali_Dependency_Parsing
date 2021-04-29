#!/usr/bin/python
# Author: Himanshu Sharma
# changes added by Pruthwik Mishra
import os
# import sys
import codecs
import re
from collections import OrderedDict


class Node():

    def __init__(self, text):
        self.text = text
        self.lex = None
        self.type = None
        self.__attributes = OrderedDict()
        self.errors = []
        self.name = None
        self.parent = None
        self.parentRelation = None
        self.alignedTo = None
        self.fsList = None
        self.analyzeNode(self.text)

    def analyzeNode(self, text):
        [token, tokenType, fsDict, fsList] = getTokenFeats(
            text.strip().split())
        attributeUpdateStatus = self.updateAttributes(
            token, tokenType, fsDict, fsList)
        if attributeUpdateStatus == 0:
            self.errors.append("Can't update attributes for node")
            self.probSent = True

    def updateAttributes(self, token, tokenType, fsDict, fsList):
        self.fsList = fsList
        self.lex = token
        self.type = tokenType
        for attribute in fsDict.keys():
            self.__attributes[attribute] = fsDict[attribute]
        self.assignName()

    def assignName(self):
        if self.__attributes.get('name'):
            self.name = self.getAttribute('name')
        else:
            self.errors.append('No name for this token Node')

    def printValue(self):
        return self.lex

    def printSSFValue(self, prefix, allFeat):
        returnValue = [prefix, self.printValue(), self.type]
        if allFeat is False:
            fs = ['<fs']
            for key in self.__attributes.keys():
                if returnValue[1] == "'" and key == 'af':
                    fs.append(key + '="' + returnValue[1] + ',punc,,,,,,"')
                elif returnValue[1] == "'" and key == 'name':
                    fs.append(key + '="' + returnValue[1] + '"')
                elif returnValue[1] == '"' and key == 'af':
                    fs.append(key + '=\'' + returnValue[1] + ",punc,,,,,,'")
                elif returnValue[1] == '"' and key == 'name':
                    fs.append(key + '=\'' + returnValue[1] + "'")
                else:
                    fs.append(key + "='" + self.getAttribute(key) + "'")
            delim = ' '
            fs[-1] = fs[-1] + '>'
            # fs.append('>')
        else:
            fs = self.fsList
            delim = '|'
        return ['\t'.join(x for x in returnValue) + '\t' + delim.join(x for x in fs)]

    def getAttribute(self, key):
        if key in self.__attributes:
            return self.__attributes[key]
        else:
            return None

    def addAttribute(self, key, value):
        self.__attributes[key] = value

    def deleteAttribute(self, key):
        del self.__attributes[key]


class ChunkNode():

    def __init__(self, header):
        self.text = []
        self.header = header
        self.footer = None
        self.nodeList = []
        self.parent = '0'
        self.__attributes = OrderedDict()
        self.parentRelation = 'root'
        self.name = None
        self.head = None
        self.isParent = False
        self.errors = []
        self.upper = None
        self.updateDrel()
        self.type = None
        self.fsList = None

    def analyzeChunk(self):
        [chunkType, chunkFeatDict, chunkFSList] = getChunkFeats(self.header)
        self.fsList = chunkFSList
        self.type = chunkType
        self.updateAttributes(chunkFeatDict)
        self.text = '\n'.join([line for line in self.text])

    def updateAttributes(self, fsDict):
        for attribute in fsDict.keys():
            self.__attributes[attribute] = fsDict[attribute]
        self.assignName()
        self.updateDrel()

    def assignName(self):
        if 'name' in self.__attributes:
            self.name = self.getAttribute('name')
        else:
            self.errors.append('No name for this chunk Node')

    def updateDrel(self):
        if 'drel' in self.__attributes:
            drelList = self.getAttribute('drel').split(':')
            if len(drelList) == 2:
                self.parent = drelList[1]
                self.parentRelation = self.getAttribute('drel').split(':')[0]
        elif 'dmrel' in self.__attributes:
            drelList = self.getAttribute('dmrel').split(':')
            if len(drelList) == 2:
                self.parent = drelList[1]
                self.parentRelation = self.getAttribute('dmrel').split(':')[0]

    def printValue(self):
        returnString = []
        for node in self.nodeList:
            returnString.append(node.printValue())
        return ' '.join(x for x in returnString)

    def printSSFValue(self, prefix, allFeat):
        returnStringList = []
        returnValue = [prefix, '((', self.type]
        if allFeat is False:
            fs = ['<fs']
            if 'head' in self.__attributes:
                head = self.__attributes['head']
            else:
                head = ''
            # print(head + ' H')
            # exit(1)
            for key in self.__attributes.keys():
                if key == 'af' and head == "'":
                    fs.append(key + '="' + head + ',punc,,,,,,"')
                elif head == "'" and key == 'name':
                    fs.append(key + '="' + head + '"')
                elif head == "'" and key == 'head':
                    fs.append(key + '="' + head + '"')
                elif head == '"' and key == 'af':
                    fs.append(key + '=\'' + head + ",punc,,,,,,'")
                elif head == '"' and key == 'name':
                    fs.append(key + '=\'' + head + "'")
                else:
                    # fs.append(key + "='" + self.getAttribute(key) + "'")
                    fs.append(key + "='" + str(self.getAttribute(key)) + "'")

            # for key in self.__attributes.keys():
            #     fs.append(key + "='" + self.getAttribute(key) + "'")
            delim = ' '
            fs[-1] = fs[-1] + '>'
            # fs.append('>')

        else:
            fs = self.fsList
            delim = '|'
        # print(fs)
        # exit(1)
        returnStringList.append(
            '\t'.join(x for x in returnValue) + '\t' + delim.join(x for x in fs))
        nodePosn = 0
        for node in self.nodeList:
            nodePosn += 1
            if isinstance(node, ChunkNode):
                returnStringList.extend(
                    node.printSSFValue(prefix + '.' + str(nodePosn), allFeat))
            else:
                returnStringList.extend(
                    node.printSSFValue(prefix + '.' + str(nodePosn), allFeat))
        returnStringList.append('\t' + '))')
        return returnStringList

    def getAttribute(self, key):
        if key in self.__attributes:
            return self.__attributes[key]
        else:
            return None

    def addAttribute(self, key, value):
        self.__attributes[key] = value

    def deleteAttribute(self, key):
        del self.__attributes[key]


class Sentence():
    def __init__(self, sentence, ignoreErrors=True, nesting=True, dummySentence=False):
        self.ignoreErrors = ignoreErrors
        self.nesting = nesting
        self.sentence = None
        self.sentenceID = None
        self.sentenceType = None
        self.length = 0
        self.tree = None
        self.nodeList = []
        self.edges = {}
        self.nodes = {}
        self.tokenNodes = {}
        self.rootNode = None
        self.fileName = None
        self.comment = None
        self.probSent = False
        self.errors = []
        self.text = sentence
        self.dummySentence = dummySentence
        if self.dummySentence is False:

            #            self.header = sentence.group('header')
            #            self.footer = sentence.group('footer')
            #            self.name = sentence.group('sentenceID')
            #            self.text = sentence.group('text')
            self.analyzeSentence()

    def analyzeSentence(self, ignoreErrors=False, nesting=True):
        lastContext = self

        for line in self.text.split('\n'):
            stripLine = line.strip()

            if stripLine == "":
                continue
            elif stripLine[0] == "<" and ignoreErrors is False:
                self.errors.append('Encountered a line starting with "<"')
                self.probSent = True
            else:
                splitLine = stripLine.split()
                # print(splitLine)
                if len(splitLine) > 0 and splitLine[0] == '))':
                    currentChunkNode.footer = line + '\n'
                    # print(currentChunkNode.type, 'T', currentChunkNode.name)
                    currentChunkNode.analyzeChunk()
                    lastContext = currentChunkNode.upper
                    currentChunkNode = lastContext

                elif len(splitLine) > 1 and splitLine[1] == '((':
                    currentChunkNode = ChunkNode(line + '\n')
                    currentChunkNode.upper = lastContext
                    currentChunkNode.upper.nodeList.append(currentChunkNode)
                    if currentChunkNode.upper.__class__.__name__ != 'Sentence':
                        currentChunkNode.upper.text.append(line)
                    lastContext = currentChunkNode
                else:
                    currentNode = Node(line + '\n')
                    lastContext.nodeList.append(currentNode)
                    currentNode.upper = lastContext


    def addEdge(self, parent, child):
        if parent in self.edges.iterkeys():
            if child not in self.edges[parent]:
                self.edges[parent].append(child)
        else:
            self.edges[parent] = [child]

    def updateAttributes(self):
        populateNodesStatus = self.populateNodes()
        populateEdgesStatus = self.populateEdges()
        self.sentence = self.generateSentence()
        if populateEdgesStatus == 0 or populateNodesStatus == 0:
            return 0
        return 1

    def printSSFValue(self, allFeat):
        returnStringList = []
        returnStringList.append("<Sentence id='" + str(self.sentenceID) + "'>")
        if self.nodeList != []:
            nodeList = self.nodeList
            nodePosn = 0
            for node in nodeList:
                nodePosn += 1
                returnStringList.extend(
                    node.printSSFValue(str(nodePosn), allFeat))
        returnStringList.append('</Sentence>\n')
        return '\n'.join(x for x in returnStringList)

    def populateNodes(self, naming='strict'):
        if naming == 'strict':
            for nodeElement in self.nodeList:
                assert nodeElement.name is not None
                self.nodes[nodeElement.name] = nodeElement
        return 1

    def populateEdges(self):
        for node in self.nodeList:
            nodeName = node.name
            if node.parent == '0' or node == self.rootNode:
                self.rootNode = node
                continue
            elif node.parent not in self.nodes.iterkeys():
                #                self.errors.append('Error : Bad DepRel Parent Name ' + self.fileName + ' : ' + str(self.name))
                return 0
            assert node.parent in self.nodes.iterkeys()
            self.addEdge(node.parent, node.name)
        return 1

    def generateSentence(self):
        sentence = []
        for nodeName in self.nodeList:
            sentence.append(nodeName.printValue())
        return ' '.join(x for x in sentence)


class Document():

    def __init__(self, fileName):
        self.header = None
        self.footer = None
        self.text = None
        self.nodeList = []
        self.fileName = fileName
        self.analyzeDocument()
        self.upper = None

    def analyzeDocument(self):
        inputFD = codecs.open(self.fileName, 'r', encoding='utf8')
        sentenceList = findSentences(inputFD)
        for sentence in sentenceList:
            tree = Sentence(sentence[1], ignoreErrors=True, nesting=True)
            tree.text = sentence[1]
            tree.sentenceID = int(sentence[0])
            tree.footer = sentence[2]
            tree.header = "<Sentence id='" + sentence[0] + "'"
            tree.upper = self
            self.nodeList.append(tree)
        inputFD.close()


def getAddressNode(address, node, level='ChunkNode'):
    ''' Returns the node referenced in the address string relative to the node in the second argument.
        There are levels for setting the starting address-base. These are "ChunkNode", "Node" , "Sentence" , "Document" , "Relative".
        The hierarchy of levels for interpretation is :
        "Document" -> "Sentence" -> "ChunkNode" -> "Node"
        "Relative" value starts the base address from the node which contains the address. This is also the default option.
    '''

    currentContext = node

    if level != 'Relative':
        while(currentContext.__class__.__name__ != level):
            currentContext = currentContext.upper

    currentContext = currentContext.upper

    stepList = address.split('%')

    for step in stepList:
        if step == '..':
            currentContext = currentContext.upper
        else:
            refNode = [
                iterNode for iterNode in currentContext.nodeList if iterNode.name == step][0]
            currentContext = refNode
    return refNode


def getChunkFeats(line):
    lineList = line.strip().split()
    returnErrors = list()
    chunkType = None
    fsList = []
    if len(lineList) >= 3:
        chunkType = lineList[2]
    returnFeats = OrderedDict()
    multipleFeatRE = r'<fs.*?>'
    # featRE = r'(?:\W*)(\S+)=([\'|\"])?([^ \t\n\r\f\v\'\"]*)[\'|\"]?(?:.*)'
    featRE = r'(?:\W*)(\S+)=([\'|\"])?([^ \t\n\r\f\v\'\"]*)[\'|\"]?(?:.*)'
    fsList = re.findall(multipleFeatRE, ' '.join(lineList))
    # print('FS', fsList)
    for x in lineList:
        feat = re.findall(featRE, x)
        if feat != []:
            if len(feat) > 1:
                returnErrors.append('Feature with more than one value')
                continue
            # if feat[0][2] not in ["'", '"']:
                # returnFeats[feat[0][0]] = feat[0][2].strip("'\"")
            returnFeats[feat[0][0]] = feat[0][2]
    return [chunkType, returnFeats, fsList]


def getTokenFeats(lineList):
    tokenType, token = None, None
    returnFeats = OrderedDict()
    fsList = []
    if len(lineList) >= 3:
        tokenType = lineList[2]
    returnErrors = list()
    token = lineList[1]
    multipleFeatRE = r'<fs.*?>'
    # featRE = r'(?:\W*)(\S+)=([\'|\"])?([^ \t\n\r\f\v\'\"]*)[\'|\"]?(?:.*)'
    featRE = r'(?:\W*)(\S+)=([\'|\"])?([^ \t\n\r\f\v\'\"]*)[\'|\"]?(?:.*)'
    fsList = re.findall(multipleFeatRE, ' '.join(lineList))
    for x in lineList:
        feat = re.findall(featRE, x)
        if feat != []:
            if len(feat) > 1:
                returnErrors.append('Feature with more than one value')
                continue
            # returnFeats[feat[0][0]] = feat[0][2].strip('"\'')
            returnFeats[feat[0][0]] = feat[0][2]
    # print(returnFeats)
    # exit(1)
    return [token, tokenType, returnFeats, fsList]


def getSentenceIter(inpFD):
    sentenceRE = r'''(?P<complete>(?P<header><Sentence id=[\'\"]?(?P<sentenceID>\d+)[\'\"]?>)(?P<text>.*?)(?P<footer></Sentence>))'''
    text = inpFD.read()
    text = text.replace('0xe0', '')
    return re.finditer(sentenceRE, text, re.DOTALL)


def findSentences(inpFD):
    sentenceRE = "<Sentence id='(.*?)'>(.*?)(</Sentence>)"
    text = inpFD.read()
    text = text.replace('0xe0', '')
    return re.findall(sentenceRE, text, re.DOTALL)


def folderWalk(folderPath):
    fileList = []
    for dirPath, dirNames, fileNames in os.walk(folderPath):
        for fileName in fileNames:
            fileList.append(os.path.join(dirPath, fileName))
    return fileList


# if __name__ == '__main__':

#     inputPath = sys.argv[1]
#     fileList = folderWalk(inputPath)
#     newFileList = []
#     for fileName in fileList:
#         xFileName = fileName.split('/')[-1]
#         if xFileName == 'err.txt' or xFileName.split('.')[-1] in ['comments', 'bak'] or xFileName[:4] == 'task':
#             continue
#         else:
#             newFileList.append(fileName)

#     for fileName in newFileList:
#         d = Document(fileName)
#         for tree in d.nodeList:
#             for chunkNode in tree.nodeList:
#                 if chunkNode.type == 'VGF':
#                     combinedTAM = ''
#                     for node in chunkNode.nodeList:
#                         if node.type != 'VM':
#                             combinedTAM += node.lex + '+'
#                     print('TAM', combinedTAM.strip('+'))
#                     # refAddress = node.getAttribute('ref')
#                     # if refAddress != None :
#                     #     refNode = getAddressNode(refAddress, node)
#                     #     print 'Anaphor' , node.printValue() , 'Reference' , refNode.printValue()
# #                        print tree.printSSFValue()
# #                        print tree.header + tree.text + tree.footer
